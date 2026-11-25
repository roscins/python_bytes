"""Tests for engine/__main__.py, the file that starts the game.

Every test passes its own temporary save path and workspace folder, so the
player's real save file and workspace are never touched. The gate test reads the real levels/ folder; the
others use temporary level packs.
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout

from engine import __main__ as engine_main
from engine.loop import WELCOME
from engine.save_file import DEFAULT_SAVE_PATH
from tests.helpers import (
    VALID_LEVEL_TOML,
    concepts_toml_text,
    make_temporary_folder,
    write_level_pack,
)


class TestMain(unittest.TestCase):
    """Check that python -m engine loads levels and the save, then runs."""

    def setUp(self):
        """Make an empty levels folder and a save path in a temporary folder."""
        folder = make_temporary_folder(self)
        self.levels_folder = folder / "levels"
        self.levels_folder.mkdir()
        self.save_path = folder / "save" / "save.json"
        self.workspace_root = folder / "workspace"

    def run_main(self, typed_text, concepts_file=None):
        """Run main with `typed_text` as the keyboard; return exit code and output.

        Most tests run without a curriculum (concepts_file None), so the map
        is made of the level packs that exist.
        """
        # input() reads from sys.stdin, so a StringIO pretends to be the
        # keyboard. The real stdin is put back after the test.
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO(typed_text)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.main(self.levels_folder, self.save_path, self.workspace_root,
                                         concepts_file)
        return exit_code, output.getvalue()

    def test_main_runs_until_quit_and_saves(self):
        """main reads commands, prints the answers and writes a save file."""
        exit_code, text = self.run_main("map\nquit\n")
        self.assertEqual(exit_code, 0)
        self.assertIn(WELCOME, text)
        self.assertIn("No levels found", text)
        self.assertIn("Goodbye, technician.", text)
        self.assertTrue(self.save_path.exists())

    def write_concepts(self, *level_ids):
        """Write a small concepts.toml next to the levels folder; return its path."""
        path = self.levels_folder.parent / "concepts.toml"
        path.write_text(concepts_toml_text(*level_ids), encoding="utf-8")
        return path

    def test_map_shows_the_whole_world_from_concepts_toml(self):
        """With a curriculum the map has a node for every level, written or not."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        concepts = self.write_concepts("1-1", "1-2", "boss-1")
        exit_code, text = self.run_main("map\nquit\n", concepts)
        self.assertEqual(exit_code, 0)
        for label in ("[1-1]", "[1-2]", "[boss-1]"):
            self.assertIn(label, text)

    def test_level_that_is_not_written_cannot_be_played(self):
        """play 1-2 says the level is not written yet."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        concepts = self.write_concepts("1-1", "1-2", "boss-1")
        exit_code, text = self.run_main("play 1-2\nquit\n", concepts)
        self.assertIn("not written yet", text)

    def test_pack_that_is_not_in_the_curriculum_stops_the_game(self):
        """A level pack whose id is not in concepts.toml is a mistake in the game."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        concepts = self.write_concepts("2-1", "boss-2")
        exit_code, text = self.run_main("quit\n", concepts)
        self.assertEqual(exit_code, 1)
        self.assertIn("1-1", text)
        self.assertIn("concepts.toml", text)

    def test_missing_or_broken_concepts_file_stops_the_game(self):
        """The curriculum is part of the game; without it the game cannot start."""
        exit_code, text = self.run_main("quit\n", self.levels_folder.parent / "nothing.toml")
        self.assertEqual(exit_code, 1)
        self.assertIn("concepts.toml", text.replace("nothing.toml", "concepts.toml"))

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


class TestPhaseOneGate(unittest.TestCase):
    """The Phase 1 gate: open the map, play Level 1-1, quit and resume."""

    def test_open_map_play_1_1_quit_and_resume(self):
        """With the real levels, a player is welcomed back to 1-1 after quitting."""
        folder = make_temporary_folder(self)
        save_path = folder / "save.json"
        workspace_root = folder / "workspace"
        output = io.StringIO()
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)

        sys.stdin = io.StringIO("map\nplay 1-1\nquit\n")
        with redirect_stdout(output):
            exit_code = engine_main.main(save_path=save_path, workspace_root=workspace_root)
        self.assertEqual(exit_code, 0)
        first_game = output.getvalue()
        self.assertIn("WORLD 1 · BOOT SECTOR", first_game)
        self.assertIn("[1-1]", first_game)
        self.assertIn("LEVEL 1-1 · HELLO, TERMINAL", first_game)

        output = io.StringIO()
        sys.stdin = io.StringIO("map\nquit\n")
        with redirect_stdout(output):
            engine_main.main(save_path=save_path, workspace_root=workspace_root)
        second_game = output.getvalue()
        self.assertIn("Welcome back. You were on level 1-1.", second_game)
        self.assertIn("You are at [1-1] Hello, Terminal.", second_game)


class TestDefaultSavePath(unittest.TestCase):
    """Check where the real save file goes."""

    def test_save_lives_in_the_home_folder(self):
        """The save is ~/.python-bytes/save.json."""
        self.assertEqual(DEFAULT_SAVE_PATH.parent.name, ".python-bytes")
        self.assertEqual(DEFAULT_SAVE_PATH.name, "save.json")


if __name__ == "__main__":
    unittest.main()
