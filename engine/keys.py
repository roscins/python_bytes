"""Reading single keys from the real terminal, with the standard library only.

A keyboard has three methods. start() switches the terminal to "one key at a
time", stop() puts it back exactly as it was, and read_key(timeout) returns
the next key, or None if no key came in time. A key is a name ("up",
"enter", "escape", "ctrl-e") or the one character that was typed.

Linux and macOS use termios; Windows uses msvcrt. stop() is also run by
atexit, and a stop signal reaches it through the game's `finally` (see
engine/shutdown.py). Only kill -9 cannot be caught; then type `reset`.
"""

import atexit
import codecs
import os
import select
import sys
import time

try:
    import termios
except ImportError:
    # Windows has no termios; WindowsKeyboard is used there.
    termios = None

# How long to wait for the rest of an escape sequence, so that a lone Esc
# can be told apart from an arrow key.
ESCAPE_WAIT = 0.05

# How often Windows looks for a key.
POLL_SECONDS = 0.02

# What terminals send for the keys that are not characters.
SEQUENCES = {
    "\x1b[A": "up", "\x1b[B": "down", "\x1b[C": "right", "\x1b[D": "left",
    "\x1bOA": "up", "\x1bOB": "down", "\x1bOC": "right", "\x1bOD": "left",
    "\x1b[H": "home", "\x1b[F": "end", "\x1bOH": "home", "\x1bOF": "end",
    "\x1b[1~": "home", "\x1b[4~": "end", "\x1b[7~": "home", "\x1b[8~": "end",
    "\x1b[3~": "delete", "\x1b[5~": "page-up", "\x1b[6~": "page-down",
    "\x1b[Z": "shift-tab",
}

SINGLE_KEYS = {"\r": "enter", "\n": "enter", "\t": "tab", "\x7f": "backspace", "\x08": "backspace"}

# The second character Windows sends after "\x00" or "\xe0".
WINDOWS_CODES = {
    "H": "up", "P": "down", "K": "left", "M": "right", "G": "home", "O": "end",
    "I": "page-up", "Q": "page-down", "S": "delete", "\x0f": "shift-tab",
}


def key_name(character):
    """Return the key for one character that is not part of an escape sequence, or None."""
    if character in SINGLE_KEYS:
        return SINGLE_KEYS[character]
    number = ord(character)
    if 1 <= number <= 26:
        return "ctrl-" + chr(ord("a") + number - 1)
    if character.isprintable():
        return character
    return None


def sequence_end(text, start):
    """Return where the escape sequence starting at `start` ends, or None if it is not complete."""
    if start + 1 >= len(text):
        return None
    if text[start + 1] == "O":
        if start + 2 < len(text):
            return start + 3
        return None
    if text[start + 1] != "[":
        return start + 1
    for index in range(start + 2, len(text)):
        # A sequence ends with a letter or "~".
        if "@" <= text[index] <= "~":
            return index + 1
    return None


def parse_keys(text):
    """Return the keys in the text a terminal sent. Unknown sequences are left out."""
    keys = []
    index = 0
    while index < len(text):
        if text[index] != "\x1b":
            key = key_name(text[index])
            if key is not None:
                keys.append(key)
            index = index + 1
            continue
        end = sequence_end(text, index)
        if end is None or end == index + 1:
            keys.append("escape")
            index = index + 1
            continue
        sequence = text[index:end]
        if sequence in SEQUENCES:
            keys.append(SEQUENCES[sequence])
        index = end
    return keys


class PosixKeyboard:
    """The keyboard on Linux and macOS.

    Attributes:
        fd: the file descriptor of the terminal.
        original: the settings from before the first start(), or None.
        started: True between start() and stop().
        waiting: keys already read but not handed out yet.
    """

    def __init__(self, fd=None, register=atexit.register):
        """Remember which terminal to read; nothing is changed yet."""
        if fd is None:
            fd = sys.stdin.fileno()
        self.fd = fd
        self.register = register
        self.registered = False
        self.original = None
        self.started = False
        self.waiting = []
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def start(self):
        """Give keys one at a time without showing them (does nothing if already started).

        Ctrl-S arrives as a key (no flow control), Ctrl-Z and Ctrl-\\ do not
        stop the game, and Ctrl-C still sends its signal.
        """
        if self.started:
            return
        # Only the first time: later the terminal may be half changed, for
        # example by an input() that a signal interrupted.
        if self.original is None:
            self.original = termios.tcgetattr(self.fd)
        self.started = True
        if not self.registered:
            self.register(self.stop)
            self.registered = True
        settings = termios.tcgetattr(self.fd)
        settings[0] = settings[0] & ~termios.IXON
        settings[3] = settings[3] & ~(termios.ICANON | termios.ECHO | termios.IEXTEN)
        disabled = bytes([os.fpathconf(self.fd, "PC_VDISABLE")])
        settings[6][termios.VSUSP] = disabled
        settings[6][termios.VQUIT] = disabled
        settings[6][termios.VMIN] = 1
        settings[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSADRAIN, settings)

    def stop(self):
        """Put the terminal back as it was (does nothing if not started)."""
        if not self.started:
            return
        self.started = False
        try:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.original)
        except (termios.error, OSError):
            # The terminal is gone (the window was closed): nothing to restore.
            pass

    def ready(self, timeout):
        """Return True if there is something to read within `timeout` seconds."""
        return bool(select.select([self.fd], [], [], timeout)[0])

    def read_character(self, timeout):
        """Return the next character, or None after `timeout` seconds; EOFError if the terminal closed.

        One byte is read at a time, so that whatever else was typed stays in
        the terminal for input() to read.
        """
        while self.ready(timeout):
            try:
                data = os.read(self.fd, 1)
            except OSError as error:
                raise EOFError from error
            if not data:
                raise EOFError
            # A letter like "ø" is two bytes; the decoder waits for both.
            text = self.decoder.decode(data)
            if text:
                return text
        return None

    def read_key(self, timeout=None):
        """Return the next key, or None after `timeout` seconds (None waits for ever)."""
        if self.waiting:
            return self.waiting.pop(0)
        text = self.read_character(timeout)
        if text is None:
            return None
        # An escape sequence is several characters; a lone Esc is only one.
        while text.startswith("\x1b") and sequence_end(text, 0) is None:
            more = self.read_character(ESCAPE_WAIT)
            if more is None:
                break
            text = text + more
        self.waiting = parse_keys(text)
        if not self.waiting:
            return None
        return self.waiting.pop(0)


class WindowsKeyboard:
    """The keyboard on Windows. The console needs no switching: msvcrt reads single keys."""

    def __init__(self, msvcrt_module=None, sleep=time.sleep, clock=time.monotonic):
        """Remember the module to read with; the parameters let tests fake them."""
        if msvcrt_module is None:
            import msvcrt as msvcrt_module
        self.msvcrt = msvcrt_module
        self.sleep = sleep
        self.clock = clock

    def start(self):
        """Nothing to switch on."""

    def stop(self):
        """Nothing to put back."""

    def read_key(self, timeout=None):
        """Return the next key, or None after `timeout` seconds (None waits for ever)."""
        deadline = None
        if timeout is not None:
            deadline = self.clock() + timeout
        while True:
            while self.msvcrt.kbhit():
                character = self.msvcrt.getwch()
                if character in ("\x00", "\xe0"):
                    key = WINDOWS_CODES.get(self.msvcrt.getwch())
                elif character == "\x1b":
                    key = "escape"
                else:
                    key = key_name(character)
                if key is not None:
                    return key
            if deadline is not None and self.clock() >= deadline:
                return None
            self.sleep(POLL_SECONDS)


def make_keyboard(system=os.name):
    """Return the keyboard for this operating system."""
    if system == "nt":
        return WindowsKeyboard()
    return PosixKeyboard()


def keyboard_available():
    """Return True if single keys can be read here. The terminal is left as it was."""
    try:
        keyboard = make_keyboard()
        keyboard.start()
        keyboard.stop()
    except Exception:
        # Whatever the reason (no termios, not a terminal), line mode works.
        return False
    return True
