"""Tests for engine/__main__.py, the file that starts the game."""

import io
import sys
import unittest
from contextlib import redirect_stdout

from engine import __main__ as engine_main
from engine.loop import WELCOME


class TestMain(unittest.TestCase):
    """Check that python -m engine starts a game that reads the keyboard."""

    def test_main_runs_until_quit(self):
        """main reads commands from standard input and prints the answers."""
        # input() reads from sys.stdin, so a StringIO pretends to be the
        # keyboard. The real stdin is put back after the test.
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO("map\nquit\n")
        output = io.StringIO()
        with redirect_stdout(output):
            engine_main.main()
        text = output.getvalue()
        self.assertIn(WELCOME, text)
        self.assertIn("Levels:", text)
        self.assertIn("Goodbye, technician.", text)


if __name__ == "__main__":
    unittest.main()
