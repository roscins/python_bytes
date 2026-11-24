"""Tests for engine/__main__.py, the file that starts the game.

Every test passes its own temporary levels folder and save path, so the
real levels/ folder and the player's real save file are never touched.
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout

from engine import __main__ as engine_main
from engine.loop import WELCOME
from engine.save_file import DEFAULT_SAVE_PATH
from tests.helpers import VALID_LEVEL_TOML, make_temporary_folder, write_level_pack


class TestMain(unittest.TestCase):
    """Check that python -m engine loads levels and the save, then runs."""

    def setUp(self):
        """Make an empty levels folder and a save path in a temporary folder."""
        folder = make_temporary_folder(self)
        self.levels_folder = folder / "levels"
        self.levels_folder.mkdir()
        self.save_path = folder / "save" / "save.json"

    def run_main(self, typed_text):
        """Run main with `typed_text` as the keyboard; return exit code and output."""
        # input() reads from sys.stdin, so a StringIO pretends to be the
        # keyboard. The real stdin is put back after the test.
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO(typed_text)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.main(self.levels_folder, self.save_path)
        return exit_code, output.getvalue()

    def test_main_runs_until_quit_and_saves(self):
        """main reads commands, prints the answers and writes a save file."""
        exit_code, text = self.run_main("map\nquit\n")
        self.assertEqual(exit_code, 0)
        self.assertIn(WELCOME, text)
        self.assertIn("No levels found", text)
        self.assertIn("Goodbye, technician.", text)
        self.assertTrue(self.save_path.exists())

    def test_quit_and_resume(self):
        """A player who plays 1-1 and quits is welcomed back to 1-1."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        self.run_main("play 1-1\nquit\n")
        exit_code, text = self.run_main("quit\n")
        self.assertIn("Welcome back. You were on level 1-1.", text)

    def test_broken_save_is_set_aside(self):
        """A broken save is renamed to .broken and the game starts fresh."""
        self.save_path.parent.mkdir()
        self.save_path.write_text("this is not json", encoding="utf-8")
        exit_code, text = self.run_main("quit\n")
        self.assertEqual(exit_code, 0)
        self.assertIn("Your save file is broken", text)
        broken_path = self.save_path.with_name("save.json.broken")
        self.assertEqual(broken_path.read_text(encoding="utf-8"), "this is not json")
        # The game started fresh and saved a new, valid file.
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["current_level"], None)

    def test_broken_level_stops_the_game(self):
        """A level.toml with a mistake gives a message and exit code 1."""
        broken_text = VALID_LEVEL_TOML.replace('title = "Hello, Terminal"\n', "")
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal", broken_text)
        exit_code, text = self.run_main("quit\n")
        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot load the levels", text)
        self.assertIn("title is missing", text)
        self.assertFalse(self.save_path.exists())


class TestDefaultSavePath(unittest.TestCase):
    """Check where the real save file goes."""

    def test_save_lives_in_the_home_folder(self):
        """The save is ~/.python-bytes/save.json."""
        self.assertEqual(DEFAULT_SAVE_PATH.parent.name, ".python-bytes")
        self.assertEqual(DEFAULT_SAVE_PATH.name, "save.json")


if __name__ == "__main__":
    unittest.main()
