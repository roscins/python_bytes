"""Tests for engine/__main__.py, the file that starts the game (run_game and main).

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
from engine.save_file import DEFAULT_SAVE_PATH
from tests.helpers import (
    VALID_LEVEL_TOML,
    concepts_toml_text,
    make_temporary_folder,
    write_level_pack,
)


class TestRunGame(unittest.TestCase):
    """Check that the game shows the title, loads levels and the save, then runs."""

    def setUp(self):
        """Make an empty levels folder and a save path in a temporary folder."""
        folder = make_temporary_folder(self)
        self.levels_folder = folder / "levels"
        self.levels_folder.mkdir()
        self.save_path = folder / "save" / "save.json"
        self.workspace_root = folder / "workspace"

    def run_game(self, typed_text, concepts_file=None):
        """Run the game with `typed_text` as the keyboard; return exit code and output.

        The first typed line answers the title screen. Most tests run without
        a curriculum (concepts_file None), so the map is made of the level
        packs that exist.
        """
        # input() reads from sys.stdin, so a StringIO pretends to be the
        # keyboard. The real stdin is put back after the test.
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO(typed_text)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.run_game(self.levels_folder, self.save_path, self.workspace_root,
                                             concepts_file, plain=True)
        return exit_code, output.getvalue()

    def test_the_title_screen_comes_first_without_help_text(self):
        """The game starts with the title, and does not explain commands."""
        exit_code, text = self.run_game("1\nquit\n")
        self.assertTrue(text.startswith("PYTHON BYTES"))
        self.assertNotIn("Type help", text)

    def test_quit_at_the_title_leaves_at_once(self):
        """Choosing QUIT on the title screen exits with 0 and writes no save."""
        exit_code, text = self.run_game("2\n")
        self.assertEqual(exit_code, 0)
        self.assertFalse(self.save_path.exists())

    def test_a_new_game_runs_until_quit_and_saves(self):
        """The loop reads commands, prints the answers and writes a save file."""
        exit_code, text = self.run_game("1\nmap\nquit\n")
        self.assertEqual(exit_code, 0)
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
        exit_code, text = self.run_game("1\nmap\nquit\n", concepts)
        self.assertEqual(exit_code, 0)
        for label in ("[1-1]", "[1-2]", "[boss-1]"):
            self.assertIn(label, text)

    def test_a_new_game_starts_at_the_map(self):
        """No need to type map first."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        exit_code, text = self.run_game("1\nquit\n")
        self.assertIn("[1-1]", text)

    def test_level_that_is_not_written_cannot_be_played(self):
        """play 1-2 says the level is not written yet."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        concepts = self.write_concepts("1-1", "1-2", "boss-1")
        exit_code, text = self.run_game("1\nplay 1-2\nquit\n", concepts)
        self.assertIn("not written yet", text)

    def test_pack_that_is_not_in_the_curriculum_stops_the_game(self):
        """A level pack whose id is not in concepts.toml is a mistake in the game."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        concepts = self.write_concepts("2-1", "boss-2")
        exit_code, text = self.run_game("1\nquit\n", concepts)
        self.assertEqual(exit_code, 1)
        self.assertIn("1-1", text)
        self.assertIn("concepts.toml", text)

    def test_missing_or_broken_concepts_file_stops_the_game(self):
        """The curriculum is part of the game; without it the game cannot start."""
        exit_code, text = self.run_game("1\nquit\n", self.levels_folder.parent / "nothing.toml")
        self.assertEqual(exit_code, 1)
        self.assertIn("concepts.toml", text.replace("nothing.toml", "concepts.toml"))

    def test_continue_lands_on_the_wave_with_the_code_typed(self):
        """Quit in the middle of a wave; CONTINUE shows the same wave and the same lines."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        self.run_game('1\nplay 1-1\nprint("SYSTEM CHECK")\nprint("VOICE\n:quit\n')
        exit_code, text = self.run_game("1\n:quit\n")
        self.assertIn("CONTINUE (level 1-1, wave 1)", text)
        self.assertIn('  1 | print("SYSTEM CHECK")', text)
        self.assertIn('  2 | print("VOICE', text)

    def test_new_game_over_a_save_keeps_the_old_one(self):
        """NEW GAME asks for yes, and the old save is kept as .old."""
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        self.run_game("1\nplay 1-1\n:quit\n")
        before = self.save_path.read_text(encoding="utf-8")
        exit_code, text = self.run_game("2\nyes\nquit\n")
        self.assertEqual(self.save_path.with_name("save.json.old").read_text(encoding="utf-8"), before)
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertIsNone(json.load(save_file)["current_level"])

    def test_broken_save_is_set_aside(self):
        """A broken save is renamed to .broken and the game starts fresh."""
        self.save_path.parent.mkdir()
        self.save_path.write_text("this is not json", encoding="utf-8")
        exit_code, text = self.run_game("1\nquit\n")
        self.assertEqual(exit_code, 0)
        self.assertIn("damaged", text)
        broken_path = self.save_path.with_name("save.json.broken")
        self.assertEqual(broken_path.read_text(encoding="utf-8"), "this is not json")
        # The game started fresh and saved a new, valid file.
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["current_level"], None)

    def test_broken_level_stops_the_game(self):
        """A level.toml with a mistake gives a message and exit code 1."""
        broken_text = VALID_LEVEL_TOML.replace('title = "Hello, Terminal"\n', "")
        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal", broken_text)
        exit_code, text = self.run_game("1\nquit\n")
        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot load the levels", text)
        self.assertIn("title is missing", text)
        self.assertFalse(self.save_path.exists())

    def test_a_stop_signal_while_waiting_saves_and_exits_with_128_plus_signal(self):
        """SIGTERM while the game waits for typing: the save is written, the code is 143."""
        import signal

        write_level_pack(self.levels_folder, "w1", "1-1-hello-terminal")
        lines = ["1", "play 1-1", "x = 1"]

        def read_line(prompt):
            if not lines:
                signal.raise_signal(signal.SIGTERM)
            return lines.pop(0)

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.run_game(self.levels_folder, self.save_path, self.workspace_root,
                                             None, read_line=read_line, plain=True)
        self.assertEqual(exit_code, 128 + signal.SIGTERM)
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["buffers"]["1-1"]["1"], "x = 1\n")


class TestCommandLine(unittest.TestCase):
    """Check main(), which python play.py runs."""

    def test_arguments(self):
        """--plain and --save are understood."""
        arguments = engine_main.parse_arguments(["--plain", "--save", "somewhere/save.json"])
        self.assertTrue(arguments.plain)
        self.assertEqual(arguments.save, "somewhere/save.json")

    def test_defaults(self):
        """Without arguments: not plain, the save in the home folder."""
        arguments = engine_main.parse_arguments([])
        self.assertFalse(arguments.plain)
        self.assertEqual(arguments.save, str(DEFAULT_SAVE_PATH))

    def test_main_runs_the_game_with_those_arguments(self):
        """main(argv) starts the real game: QUIT at the title returns 0."""
        folder = make_temporary_folder(self)
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO("2\n")
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.main(["--plain", "--save", str(folder / "save.json")])
        self.assertEqual(exit_code, 0)
        self.assertIn("PYTHON BYTES", output.getvalue())


class TestPhaseOneGate(unittest.TestCase):
    """The Phase 1 gate: open the map, play Level 1-1, quit and resume."""

    def test_open_map_play_1_1_quit_and_resume(self):
        """With the real levels, CONTINUE brings the player back to 1-1."""
        folder = make_temporary_folder(self)
        save_path = folder / "save.json"
        workspace_root = folder / "workspace"
        output = io.StringIO()
        real_stdin = sys.stdin
        self.addCleanup(setattr, sys, "stdin", real_stdin)

        sys.stdin = io.StringIO("1\nmap\nplay 1-1\n:quit\n")
        with redirect_stdout(output):
            exit_code = engine_main.run_game(save_path=save_path, workspace_root=workspace_root, plain=True)
        self.assertEqual(exit_code, 0)
        first_game = output.getvalue()
        self.assertIn("WORLD 1 · BOOT SECTOR", first_game)
        self.assertIn("[1-1]", first_game)
        self.assertIn("LEVEL 1-1 · HELLO, TERMINAL", first_game)

        output = io.StringIO()
        sys.stdin = io.StringIO("1\n:map\nquit\n")
        with redirect_stdout(output):
            engine_main.run_game(save_path=save_path, workspace_root=workspace_root, plain=True)
        second_game = output.getvalue()
        self.assertIn("CONTINUE (level 1-1, wave 1)", second_game)
        self.assertIn("WAVE 1 of 3 · FILL-IN", second_game)
        self.assertIn("You are at [1-1] Hello, Terminal.", second_game)


class TestDefaultSavePath(unittest.TestCase):
    """Check where the real save file goes."""

    def test_save_lives_in_the_home_folder(self):
        """The save is ~/.python-bytes/save.json."""
        self.assertEqual(DEFAULT_SAVE_PATH.parent.name, ".python-bytes")
        self.assertEqual(DEFAULT_SAVE_PATH.name, "save.json")


if __name__ == "__main__":
    unittest.main()
