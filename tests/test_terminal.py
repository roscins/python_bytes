"""Tests for engine/terminal.py: full screen, the window size, and the "press Enter to skip" key.

The terminal itself is replaced by small fakes, so these tests never touch a real one.
"""

import unittest

from engine.shutdown import GameInterrupted
from engine.terminal import (
    ENTER_FULLSCREEN,
    LEAVE_FULLSCREEN,
    Fullscreen,
    terminal_size,
)


class FakeStdin:
    """A pretend keyboard. `lines` is what the player has typed and not yet read."""

    def __init__(self, lines=(), tty=True):
        """Remember the typed lines and whether this is a terminal."""
        self.lines = list(lines)
        self.tty = tty
        self.read_count = 0

    def isatty(self):
        """Say whether this pretends to be a terminal."""
        return self.tty

    def readline(self):
        """Return the next typed line, with its newline."""
        self.read_count = self.read_count + 1
        return self.lines.pop(0) + "\n"

    def fileno(self):
        """Return a fake file number."""
        return 0


class TestFullscreen(unittest.TestCase):
    """The alternate screen is entered once and always left again."""

    def setUp(self):
        """A recorder for what is written, and a recorder for atexit registrations."""
        self.written = []
        self.registered = []
        self.screen = Fullscreen(self.written.append, register=self.registered.append)

    def test_enter_writes_the_alternate_screen_code(self):
        """ESC[?1049h switches to the alternate screen."""
        self.screen.enter()
        self.assertEqual(self.written, [ENTER_FULLSCREEN])
        self.assertIn("\x1b[?1049h", ENTER_FULLSCREEN)

    def test_leave_restores_the_screen_the_cursor_and_the_colours(self):
        """ESC[?1049l leaves; the cursor is shown again; colours are reset."""
        self.screen.enter()
        self.screen.leave()
        self.assertEqual(self.written[-1], LEAVE_FULLSCREEN)
        for code in ("\x1b[?1049l", "\x1b[?25h", "\x1b[0m"):
            self.assertIn(code, LEAVE_FULLSCREEN)

    def test_leave_twice_writes_once(self):
        """atexit and the normal exit may both call it."""
        self.screen.enter()
        self.screen.leave()
        self.screen.leave()
        self.assertEqual(self.written.count(LEAVE_FULLSCREEN), 1)

    def test_leave_without_enter_writes_nothing(self):
        """Nothing to restore."""
        self.screen.leave()
        self.assertEqual(self.written, [])

    def test_enter_twice_writes_once(self):
        """Entering again does nothing."""
        self.screen.enter()
        self.screen.enter()
        self.assertEqual(self.written.count(ENTER_FULLSCREEN), 1)

    def test_with_statement_leaves_on_a_normal_exit(self):
        """Enter at the start, leave at the end."""
        with self.screen:
            self.assertTrue(self.screen.active)
        self.assertFalse(self.screen.active)
        self.assertEqual(self.written, [ENTER_FULLSCREEN, LEAVE_FULLSCREEN])

    def test_with_statement_leaves_when_an_error_happens(self):
        """Any exception."""
        with self.assertRaises(ValueError):
            with self.screen:
                raise ValueError("boom")
        self.assertEqual(self.written[-1], LEAVE_FULLSCREEN)

    def test_with_statement_leaves_on_a_stop_signal(self):
        """GameInterrupted, which is what SIGTERM, SIGHUP and Ctrl-C raise."""
        with self.assertRaises(GameInterrupted):
            with self.screen:
                raise GameInterrupted(143)
        self.assertEqual(self.written[-1], LEAVE_FULLSCREEN)

    def test_with_statement_leaves_on_exit_calls(self):
        """sys.exit() inside the game."""
        with self.assertRaises(SystemExit):
            with self.screen:
                raise SystemExit(0)
        self.assertEqual(self.written[-1], LEAVE_FULLSCREEN)

    def test_leave_is_registered_for_the_end_of_the_program(self):
        """atexit is the last safety net."""
        self.screen.enter()
        self.assertEqual(self.registered, [self.screen.leave])

    def test_cursor_hide_and_show(self):
        """The cursor is hidden only while an animation plays."""
        self.screen.enter()
        self.screen.hide_cursor()
        self.screen.show_cursor()
        self.assertEqual(self.written[-2:], ["\x1b[?25l", "\x1b[?25h"])

    def test_leave_shows_the_cursor_even_if_it_was_hidden(self):
        """A hidden cursor must never be left behind."""
        self.screen.enter()
        self.screen.hide_cursor()
        self.screen.leave()
        self.assertIn("\x1b[?25h", self.written[-1])


class TestTerminalSize(unittest.TestCase):
    """The window size, with a safe default."""

    def test_size_comes_from_the_system(self):
        """(columns, rows) of the window."""
        columns, rows = terminal_size(lambda fallback: (100, 40))
        self.assertEqual((columns, rows), (100, 40))

    def test_default_when_unknown(self):
        """The fallback asked for is 80 x 24."""
        seen = []
        terminal_size(lambda fallback: seen.append(fallback) or fallback)
        self.assertEqual(seen, [(80, 24)])


if __name__ == "__main__":
    unittest.main()
