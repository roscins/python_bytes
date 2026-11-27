"""The real terminal: full-screen mode, the window size, and the "skip" key.

Everything that depends on the operating system lives here, so the rest of
the game can be tested with plain text.

Full-screen mode uses the terminal's alternate screen buffer: the game gets
a clean screen, and when it ends the player's own terminal comes back
exactly as it was. Fullscreen.leave() is run on every way out: a normal
exit, an error, a stop signal (see engine/shutdown.py) and, as the last
safety net, atexit. Only kill -9 cannot be caught; then the player types
`reset`.
"""

import atexit
import os
import select
import shutil
import sys

ENTER_FULLSCREEN = "\x1b[?1049h\x1b[2J\x1b[H"
LEAVE_FULLSCREEN = "\x1b[0m\x1b[?25h\x1b[?1049l"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

# The size the game assumes when the system cannot tell.
DEFAULT_SIZE = (80, 24)


class Fullscreen:
    """The alternate screen: enter once, leave on every way out.

    Attributes:
        active: True between enter() and leave().
    """

    def __init__(self, write, register=atexit.register):
        """Remember how to write to the terminal and how to register the exit safety net."""
        self.write = write
        self.register = register
        self.active = False

    def enter(self):
        """Switch to the alternate screen (does nothing if already there)."""
        if self.active:
            return
        self.write(ENTER_FULLSCREEN)
        self.active = True
        self.register(self.leave)

    def leave(self):
        """Switch back, show the cursor and reset the colours (does nothing if not there)."""
        if not self.active:
            return
        self.active = False
        self.write(LEAVE_FULLSCREEN)

    def hide_cursor(self):
        """Hide the cursor, for an animation."""
        self.write(HIDE_CURSOR)

    def show_cursor(self):
        """Show the cursor again."""
        self.write(SHOW_CURSOR)

    def __enter__(self):
        """Use with `with`: enter full screen."""
        self.enter()
        return self

    def __exit__(self, kind, error, traceback):
        """Leave full screen, whatever happened inside the with block."""
        self.leave()
        return False


def terminal_size(get_size=shutil.get_terminal_size):
    """Return (columns, rows) of the window, or 80 x 24 if the system cannot tell."""
    size = get_size(DEFAULT_SIZE)
    return size[0], size[1]


def enable_virtual_terminal():
    """Make a Windows console understand colour and cursor codes. Return True if it does.

    Windows Terminal does already; the old console needs this switch. On
    other systems there is nothing to do.
    """
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        # 0x0004 is ENABLE_VIRTUAL_TERMINAL_PROCESSING.
        return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except (ImportError, AttributeError, OSError):
        return False


class EnterWatcher:
    """Tells an animation if the player pressed Enter, so it can be skipped.

    It only looks at a real terminal. When the input is a pipe (a test, a
    script) the typed lines belong to the game, so the watcher never reads.
    In a terminal the line is read only when the player has pressed Enter,
    so no raw-mode switch is needed.
    """

    def __init__(self, stdin=None, system=os.name, select_function=select.select, msvcrt_module=None):
        """Remember what to watch; the last three are parameters so tests can fake them."""
        self.stdin = stdin
        self.system = system
        self.select_function = select_function
        self.msvcrt_module = msvcrt_module

    def pressed(self):
        """Return True if the player pressed Enter since the last call."""
        if self.stdin is None:
            return False
        if self.system == "nt":
            return self.windows_pressed()
        if not self.stdin.isatty():
            return False
        ready, _, _ = self.select_function([self.stdin], [], [], 0)
        if not ready:
            return False
        self.stdin.readline()
        return True

    def windows_pressed(self):
        """Look for the Enter key on Windows, ignoring every other key."""
        module = self.msvcrt_module
        if module is None:
            import msvcrt as module
        found = False
        while module.kbhit():
            if module.getwch() in ("\r", "\n"):
                found = True
        return found


def enable_line_editing(importer=__import__):
    """Let input() use the arrow keys and recall earlier lines, where Python can.

    Importing readline is enough. Windows does not have it; then nothing
    changes. Returns True if line editing is on.
    """
    try:
        importer("readline")
    except ImportError:
        return False
    return True


def default_write(text):
    """Write text to the terminal right away, without a newline."""
    sys.stdout.write(text)
    sys.stdout.flush()


def supports_truecolor(environment=os.environ):
    """Return True if the terminal shows 24-bit colour (the pixel art is drawn with it).

    Most terminals say so with COLORTERM. Windows Terminal and a few others
    are known by their own variables. macOS Terminal.app has only 256
    colours, and so does anything unknown: the game then converts the colours.
    """
    if environment.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    if "WT_SESSION" in environment:
        return True
    return environment.get("TERM_PROGRAM", "") in ("iTerm.app", "WezTerm", "vscode", "Hyper")
