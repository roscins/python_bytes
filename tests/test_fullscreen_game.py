"""The whole game in full-screen mode, on a fake terminal, and on a real pseudo-terminal.

The fake-terminal tests run run_game with a display that collects what is
drawn. The last class starts the real game in a pseudo-terminal (POSIX only)
and checks the terminal is put back on every way out.
"""

import io
import json
import os
import signal
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from engine import __main__ as engine_main
from engine.key_display import KeyDisplay
from engine.terminal import ENTER_FULLSCREEN, LEAVE_FULLSCREEN, supports_truecolor
from render.ansi import strip_ansi
from tests.helpers import make_temporary_folder
from tests.test_display import FakeKeyboard, FakeTerminal

PROJECT_FOLDER = Path(__file__).parent.parent


class TestRunGameFullScreen(unittest.TestCase):
    """run_game with a KeyDisplay on a fake terminal and a scripted keyboard."""

    def setUp(self):
        """A save path and a fake terminal."""
        self.save_path = make_temporary_folder(self) / "save.json"
        self.terminal = FakeTerminal()

    def play(self, keys):
        """Run the real game (real levels) with the keys; return (exit code, printed text)."""
        self.keyboard = keys if isinstance(keys, FakeKeyboard) else FakeKeyboard(keys)
        printed = io.StringIO()

        def factory(state):
            return KeyDisplay(state, self.terminal.write, self.keyboard, size=self.terminal.size,
                              sleep=self.terminal.sleep)

        with redirect_stdout(printed):
            code = engine_main.run_game(save_path=self.save_path, display_factory=factory, concepts_file=None)
        return code, printed.getvalue()

    def test_the_game_enters_full_screen_and_leaves_it_at_the_end(self):
        """And says goodbye on the player's own screen, after leaving."""
        code, printed = self.play(["enter", "down", "enter"])
        self.assertEqual(code, 0)
        self.assertEqual(self.terminal.written[0], ENTER_FULLSCREEN)
        self.assertEqual(self.terminal.written[-1], LEAVE_FULLSCREEN)
        self.assertFalse(self.keyboard.started)
        self.assertIn("Goodbye, technician.", printed)

    def test_the_title_has_the_logo_and_press_enter_before_the_menu(self):
        """The first screens."""
        self.play(["enter", "down", "enter"])
        text = strip_ansi(self.terminal.text())
        self.assertIn("PRESS ENTER", text)
        self.assertLess(text.index("PRESS ENTER"), text.index("NEW GAME"))
        self.assertIn("▀", self.terminal.text())

    def test_a_stop_signal_leaves_full_screen_and_saves(self):
        """SIGTERM while the editor waits for a key."""
        class SignalAtTheEnd(FakeKeyboard):
            """Sends SIGTERM instead of running out of keys."""

            def read_key(self, timeout=None):
                """Return the next key, or raise the signal."""
                if timeout != 0 and not self.keys:
                    signal.raise_signal(signal.SIGTERM)
                return super().read_key(timeout)

        keys = ["enter", "enter", "escape", "enter", "escape", "7"]
        code, _ = self.play(SignalAtTheEnd(keys))
        self.assertEqual(code, 128 + signal.SIGTERM)
        self.assertEqual(self.terminal.written[-1], LEAVE_FULLSCREEN)
        self.assertFalse(self.keyboard.started)
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["buffers"]["1-1"]["1"], "print(7)\n")

    def test_an_error_inside_the_game_leaves_full_screen_before_it_propagates(self):
        """The terminal is not left in the alternate screen."""
        class Broken(FakeKeyboard):
            """A keyboard that fails."""

            def read_key(self, timeout=None):
                """Raise an error the game does not expect."""
                raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            self.play(Broken())
        self.assertEqual(self.terminal.written[-1], LEAVE_FULLSCREEN)
        self.assertFalse(self.keyboard.started)

    def test_every_frame_of_a_session_has_the_hud(self):
        """On every screen drawn after the title."""
        self.play(["enter", "enter", "escape", "enter", "escape", "ctrl-d"])
        frames = [chunk for chunk in self.terminal.written if chunk.startswith("\x1b[1;1H")]
        self.assertGreater(len(frames), 5)
        for frame in frames:
            self.assertIn("WORLD 1", strip_ansi(frame))

    def test_plain_mode_never_uses_the_display(self):
        """--plain is the baseline: no escape codes at all."""
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO("1\nplay 1-1\n:quit\n")
        printed = io.StringIO()
        with redirect_stdout(printed):
            engine_main.run_game(save_path=self.save_path, plain=True, concepts_file=None)
        self.assertNotIn(ENTER_FULLSCREEN, printed.getvalue())
        self.assertNotIn("\x1b[?1049h", printed.getvalue())


class TestTrueColourDetection(unittest.TestCase):
    """Which terminals get the 24-bit pixel art."""

    def test_colorterm(self):
        """truecolor and 24bit."""
        self.assertTrue(supports_truecolor({"COLORTERM": "truecolor"}))
        self.assertTrue(supports_truecolor({"COLORTERM": "24bit"}))

    def test_windows_terminal(self):
        """It sets WT_SESSION."""
        self.assertTrue(supports_truecolor({"WT_SESSION": "abc"}))

    def test_known_terminal_programs(self):
        """iTerm2 and friends."""
        self.assertTrue(supports_truecolor({"TERM_PROGRAM": "iTerm.app"}))

    def test_macos_terminal_app_has_256_colours(self):
        """So the game converts."""
        self.assertFalse(supports_truecolor({"TERM_PROGRAM": "Apple_Terminal", "TERM": "xterm-256color"}))

    def test_nothing_known_means_256(self):
        """The safe choice."""
        self.assertFalse(supports_truecolor({}))


@unittest.skipIf(os.name == "nt", "pseudo-terminals are for Linux and macOS")
class TestRealTerminal(unittest.TestCase):
    """Start the real game in a pseudo-terminal of 80 x 24."""

    def start(self):
        """Fork the game in a pty; return (process id, master file descriptor, save path)."""
        import fcntl
        import pty
        import struct
        import termios

        save_path = make_temporary_folder(self) / "save.json"
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(PROJECT_FOLDER)
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLORTERM"] = "truecolor"
            os.execv(sys.executable, [sys.executable, "play.py", "--save", str(save_path)])
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        self.addCleanup(self.finish, pid, master)
        return pid, master, save_path

    def finish(self, pid, master):
        """Make sure the child is gone and the descriptor closed."""
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        try:
            os.close(master)
        except OSError:
            pass

    def read_until(self, master, text, seconds=15):
        """Read what the game prints until `text` appears; return everything read."""
        import select

        collected = b""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                collected = collected + data
                if text.encode() in collected:
                    return collected
        self.fail(f"Waited for {text!r}; the game printed {collected[-300:]!r}")

    def test_enters_the_alternate_screen_and_leaves_it_on_quit(self):
        """Title -> Enter -> menu -> QUIT: the alternate screen is entered and left, exit code 0."""
        pid, master, _ = self.start()
        self.read_until(master, "\x1b[?1049h")
        self.read_until(master, "PRESS ENTER")
        os.write(master, b"\r")
        self.read_until(master, "NEW GAME")
        os.write(master, b"\x1b[B")          # down to QUIT
        os.write(master, b"\r")
        data = self.read_until(master, "\x1b[?1049l")
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertIn(b"Goodbye, technician.", data + self.read_rest(master))

    def read_rest(self, master):
        """Read whatever is left after the game ended."""
        import select

        rest = b""
        while select.select([master], [], [], 0.2)[0]:
            try:
                data = os.read(master, 65536)
            except OSError:
                break
            if not data:
                break
            rest = rest + data
        return rest

    def press_enter_until(self, master, text, tries=20):
        """Press Enter now and then until `text` shows (an Enter may be used to skip an animation)."""
        import select

        seen = b""
        for _ in range(tries):
            os.write(master, b"\r")
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        seen = seen + os.read(master, 65536)
                    except OSError:
                        return seen
                    if text.encode() in seen:
                        return seen
        self.fail(f"Pressed Enter {tries} times waiting for {text!r}; the game printed {seen[-300:]!r}")

    def type_line(self, master, text):
        """Type a line and press Enter."""
        os.write(master, text.encode() + b"\r")

    def press(self, master, keys, expected):
        """Press keys and wait for something printed after them."""
        os.write(master, keys)
        return self.read_until(master, expected)

    def test_playing_a_level_from_the_title_to_quit(self):
        """New game, the map, Enter on 1-1, type into the blank, ^R, ^S, ^O, the Quit button."""
        pid, master, save_path = self.start()
        self.read_until(master, "PRESS ENTER")
        self.press_enter_until(master, "NEW GAME")
        os.write(master, b"\r")                       # NEW GAME
        self.press_enter_until(master, "[1-1] ")       # the tutorial comes first
        self.press_enter_until(master, "WAVE 1 of 3")  # Enter plays; story and tips
        self.press(master, b'"SNEK ONLINE"', "^S submit")
        self.press(master, b"\x12", "RUN (not graded)")
        self.press(master, b"\x13", "tests passed")
        self.press(master, b"\x0f", ": command")       # Ctrl-O: the map
        os.write(master, b"\x1b[B\x1b[C\x1b[C\x1b[C\r")  # buttons, then Quit
        data = self.read_until(master, "\x1b[?1049l")
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertIn(b"Goodbye, technician.", data + self.read_rest(master))
        with open(save_path, encoding="utf-8") as save_file:
            saved = json.load(save_file)
        self.assertEqual(saved["current_level"], "1-1")
        self.assertEqual(saved["levels"]["1-1"]["wave_best"][0], 1.0)
        self.assertEqual(saved["buffers"]["1-1"]["1"], 'print("SNEK ONLINE")\n')

    def test_a_stop_signal_puts_the_terminal_back(self):
        """SIGTERM at the title: the alternate screen is left and the cursor shown."""
        pid, master, _ = self.start()
        self.read_until(master, "\x1b[?1049h")
        self.read_until(master, "PRESS ENTER")
        os.kill(pid, signal.SIGTERM)
        data = self.read_until(master, "\x1b[?1049l")
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 128 + signal.SIGTERM)
        self.assertIn(b"\x1b[?25h", data)


if __name__ == "__main__":
    unittest.main()
