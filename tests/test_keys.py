"""Tests for engine/keys.py, engine/focus.py and render/buttons.py."""

import os
import signal
import sys
import time
import unittest
from pathlib import Path

from engine.focus import Choice
from engine.keys import PosixKeyboard, WindowsKeyboard, parse_keys
from render.ansi import strip_ansi
from render.buttons import button_row, menu_lines
from tests.helpers import make_temporary_folder

PROJECT_FOLDER = Path(__file__).parent.parent


class TestParseKeys(unittest.TestCase):
    """Turning the text a terminal sends into key names."""

    def test_arrows_in_both_forms(self):
        """Normal and application mode."""
        self.assertEqual(parse_keys("\x1b[A\x1b[B\x1b[C\x1b[D\x1bOA"), ["up", "down", "right", "left", "up"])

    def test_the_editing_keys(self):
        """Enter, Tab, Shift-Tab, Backspace, Delete and the paging keys."""
        self.assertEqual(parse_keys("\r\n\t\x1b[Z\x7f\x1b[3~\x1b[5~\x1b[6~"),
                         ["enter", "enter", "tab", "shift-tab", "backspace", "delete", "page-up", "page-down"])

    def test_control_keys(self):
        """Ctrl-D, Ctrl-E and Ctrl-S."""
        self.assertEqual(parse_keys("\x04\x05\x13"), ["ctrl-d", "ctrl-e", "ctrl-s"])

    def test_characters_including_norwegian_letters(self):
        """Typed characters are the keys themselves."""
        self.assertEqual(parse_keys("a:æø"), ["a", ":", "æ", "ø"])

    def test_a_lone_escape(self):
        """Esc, also when typed before a letter."""
        self.assertEqual(parse_keys("\x1b"), ["escape"])
        self.assertEqual(parse_keys("\x1bq"), ["escape", "q"])

    def test_an_unknown_sequence_is_left_out(self):
        """F5 is not typed as text."""
        self.assertEqual(parse_keys("\x1b[15~x"), ["x"])


class FakeMsvcrt:
    """msvcrt with a list of characters waiting."""

    def __init__(self, characters):
        """Remember what will be typed."""
        self.characters = list(characters)

    def kbhit(self):
        """Is a character waiting?"""
        return bool(self.characters)

    def getwch(self):
        """Return the next character."""
        return self.characters.pop(0)


class TestWindowsKeyboard(unittest.TestCase):
    """The msvcrt reader, with a fake msvcrt."""

    def test_arrows_enter_escape_and_characters(self):
        """The prefixed codes and the plain ones."""
        keyboard = WindowsKeyboard(FakeMsvcrt("\xe0H\x00P\r\x1bx"))
        keys = [keyboard.read_key(0) for _ in range(5)]
        self.assertEqual(keys, ["up", "down", "enter", "escape", "x"])

    def test_no_key_gives_none_after_the_timeout(self):
        """With a clock that jumps."""
        times = iter([0.0, 5.0])
        keyboard = WindowsKeyboard(FakeMsvcrt(""), sleep=lambda seconds: None, clock=lambda: next(times))
        self.assertIsNone(keyboard.read_key(1))


@unittest.skipIf(os.name == "nt", "pseudo-terminals are for Linux and macOS")
class TestPosixKeyboard(unittest.TestCase):
    """The termios reader on a pseudo-terminal."""

    def setUp(self):
        """A terminal pair and a keyboard on it."""
        self.master, self.slave = os.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        self.keyboard = PosixKeyboard(self.slave, register=lambda function: None)

    def test_stop_puts_the_settings_back_exactly(self):
        """Also when start and stop are called twice."""
        import termios

        before = termios.tcgetattr(self.slave)
        self.keyboard.start()
        self.keyboard.start()
        self.assertNotEqual(termios.tcgetattr(self.slave), before)
        self.keyboard.stop()
        self.keyboard.stop()
        self.assertEqual(termios.tcgetattr(self.slave), before)

    def test_keys_arrive_one_at_a_time_without_enter(self):
        """An arrow and Ctrl-S (not taken by flow control)."""
        self.keyboard.start()
        self.addCleanup(self.keyboard.stop)
        os.write(self.master, b"\x1b[B\x13")
        self.assertEqual(self.keyboard.read_key(2), "down")
        self.assertEqual(self.keyboard.read_key(2), "ctrl-s")
        self.assertIsNone(self.keyboard.read_key(0))

    def test_what_follows_a_key_is_left_for_input(self):
        """Typing ":help" fast: the keyboard takes the colon only."""
        self.keyboard.start()
        self.addCleanup(self.keyboard.stop)
        os.write(self.master, b":help\r")
        self.assertEqual(self.keyboard.read_key(2), ":")
        self.assertEqual(os.read(self.slave, 100), b"help\n")

    def test_a_letter_of_two_bytes_split_in_the_middle(self):
        """UTF-8 is put together again."""
        self.keyboard.start()
        self.addCleanup(self.keyboard.stop)
        first, second = "ø".encode()
        os.write(self.master, bytes([first]))
        self.assertIsNone(self.keyboard.read_key(1))
        os.write(self.master, bytes([second]))
        self.assertEqual(self.keyboard.read_key(2), "ø")


# Runs the game and then says whether the terminal settings are as before.
WRAPPER = """
import subprocess, sys, termios
before = termios.tcgetattr(0)
game = subprocess.Popen([sys.executable, "play.py", "--save", sys.argv[1]])
print("PID", game.pid, "END", flush=True)
code = game.wait()
print("RESTORED", termios.tcgetattr(0) == before, "CODE", code, "DONE", flush=True)
"""


@unittest.skipIf(os.name == "nt", "pseudo-terminals are for Linux and macOS")
class TestTerminalIsRestored(unittest.TestCase):
    """After every way out of the real game the terminal settings are as before."""

    def start(self):
        """Run the wrapper in an 80 x 24 pseudo-terminal; return the master descriptor."""
        import fcntl
        import pty
        import struct
        import termios

        save_path = make_temporary_folder(self) / "save.json"
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(PROJECT_FOLDER)
            os.environ["TERM"] = "xterm-256color"
            os.environ.pop("NO_COLOR", None)
            fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
            os.execv(sys.executable, [sys.executable, "-c", WRAPPER, str(save_path)])
        self.addCleanup(os.close, master)
        self.addCleanup(self.finish, pid)
        self.output = b""
        return master

    def finish(self, pid):
        """Kill the wrapper and its game if a failed test left them running."""
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        os.waitpid(pid, 0)

    def read_until(self, master, text):
        """Read until `text` has been printed."""
        import select

        deadline = time.monotonic() + 15
        while text.encode() not in self.output:
            if time.monotonic() > deadline:
                self.fail(f"Waited for {text!r}; got {self.output[-300:]!r}")
            if select.select([master], [], [], 0.1)[0]:
                self.output = self.output + os.read(master, 65536)

    def end_with(self, action):
        """Start the game, wait for the title, do `action(master, game pid)`, return the report."""
        master = self.start()
        self.read_until(master, "PRESS ENTER")
        game = int(self.output.split(b"PID ")[1].split(b" END")[0])
        action(master, game)
        self.read_until(master, " DONE")
        return self.output.split(b"RESTORED ")[1].split(b" DONE")[0].decode()

    def test_after_each_stop_signal(self):
        """SIGINT, SIGTERM, SIGHUP and SIGQUIT."""
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
            with self.subTest(signal=number.name):
                report = self.end_with(lambda master, game: os.kill(game, number))
                self.assertEqual(report, f"True CODE {128 + number}")

    def test_after_a_signal_at_the_typing_row(self):
        """Inside a wave the line is read by input(); a kill there must restore too."""
        def press(master, key, expected):
            """Press a key and wait for something printed after it."""
            self.output = b""
            os.write(master, key)
            self.read_until(master, expected)

        def action(master, game):
            press(master, b"\r", "NEW GAME")
            press(master, b"\r", "Esc skip")        # the tutorial
            press(master, b"\x1b", ": command")     # the map
            press(master, b"\r", "Esc skip")        # the story of 1-1
            press(master, b"\x1b", "FILL ")         # the wave and its typing row
            time.sleep(0.5)
            os.kill(game, signal.SIGTERM)

        self.assertEqual(self.end_with(action), f"True CODE {128 + signal.SIGTERM}")

    def test_after_ctrl_d(self):
        """Enter to leave the title screen, then Ctrl-D at the menu."""
        def action(master, game):
            os.write(master, b"\r")
            self.read_until(master, "NEW GAME")
            os.write(master, b"\x04")

        self.assertEqual(self.end_with(action), "True CODE 0")


class TestChoice(unittest.TestCase):
    """Moving between buttons."""

    def test_moves_and_stops_at_the_ends(self):
        """Right, right, right; then left."""
        choice = Choice(["a", "b"])
        for key in ("right", "right", "up"):
            choice.move(key)
        self.assertEqual(choice.label(), "b")
        choice.move("left")
        choice.move("left")
        self.assertEqual(choice.label(), "a")


class TestButtons(unittest.TestCase):
    """Drawing buttons and menus."""

    def test_the_chosen_button_is_highlighted(self):
        """Only that one."""
        row = button_row(["Run", "Map"], 1)
        self.assertIn("\x1b[7m[Map]", row)
        self.assertEqual(strip_ansi(row), " [Run]  [Map]")

    def test_the_chosen_menu_line_has_an_arrow(self):
        """So it shows without colour too."""
        lines = [strip_ansi(line) for line in menu_lines(["One", "Two"], 0)]
        self.assertTrue(lines[0].startswith("> "))
        self.assertTrue(lines[1].startswith("   "))


if __name__ == "__main__":
    unittest.main()
