"""The Phase 2 gate: Level 1-1 is fully graded, start to finish, through the real game.

"Level 1-1 is fully graded; each wave's reference solution passes and a
known-wrong solution fails." These tests run python -m engine's main with
the real Level 1-1, a temporary workspace and a temporary save file, and
type commands as a player would.
"""

import io
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from engine import __main__ as engine_main
from engine.level_pack import load_levels
from engine.workspace import wave_file_name
from tests.helpers import make_temporary_folder

PROJECT_FOLDER = Path(__file__).parent.parent
LEVELS_FOLDER = PROJECT_FOLDER / "levels"
LEVEL_1_1_FOLDER = LEVELS_FOLDER / "w1" / "1-1-hello-terminal"


def level_1_1():
    """Return the real Level 1-1."""
    for level in load_levels(LEVELS_FOLDER):
        if level.id == "1-1":
            return level
    raise AssertionError("Level 1-1 is missing")


def solutions(level, which):
    """Return a dict from wave file name to the "reference" (or "wrong") solution of each wave."""
    files = {}
    number = 0
    for wave in level.waves:
        number = number + 1
        if wave.mode == "predict":
            if which == "reference":
                text = wave.answer
            else:
                text = wave.wrong
        elif which == "reference":
            text = wave.reference
        else:
            text = wave.wrong
        files[wave_file_name(wave, number)] = text
    return files


class GameRunner:
    """Runs python -m engine's main with typed lines, a temporary save and a temporary workspace."""

    def __init__(self, test, levels_folder=LEVELS_FOLDER):
        """Make the temporary folders for one player."""
        folder = make_temporary_folder(test)
        self.test = test
        self.levels_folder = levels_folder
        self.save_path = folder / "save.json"
        self.workspace_root = folder / "workspace"

    def play(self, typed_lines):
        """Start the game, type each line, and return everything it printed."""
        real_stdin = sys.stdin
        self.test.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO("\n".join(typed_lines) + "\n")
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.main(self.levels_folder, self.save_path, self.workspace_root)
        self.test.assertEqual(exit_code, 0)
        return output.getvalue()

    def write_files(self, level_id, files):
        """Write the player's wave files into the level's workspace folder."""
        for name in files:
            path = self.workspace_root / level_id / name
            path.write_text(files[name], encoding="utf-8")


class TestPhaseTwoGate(unittest.TestCase):
    """Level 1-1 is fully graded through the real game."""

    def test_reference_solutions_clear_level_1_1_with_three_stars(self):
        """Writing every reference solution gives 100 %, 3 stars and the level-clear screen."""
        player = GameRunner(self)
        player.play(["play 1-1", "quit"])
        player.write_files("1-1", solutions(level_1_1(), "reference"))
        text = player.play(["submit", "map", "quit"])
        self.assertIn("LEVEL 1-1 CLEARED · HELLO, TERMINAL", text)
        self.assertIn("POWER-UP: status", text)
        self.assertIn("WAVE 1 · FILL-IN  2/2 tests passed ✓", text)
        self.assertIn("WAVE 2 · BUILD  2/2 tests passed ✓", text)
        self.assertIn("Code quality 4/4", text)
        self.assertIn("WAVE 3 · DEBUG  1/1 test passed ✓", text)
        self.assertIn("LEVEL SCORE 100 %  ★★★", text)
        self.assertIn("★ 3/3", text)

    def test_wrong_solutions_score_under_70_and_open_nothing(self):
        """Writing every wrong solution scores under 70 %, and the next level stays locked."""
        levels_folder = make_temporary_folder(self) / "levels"
        shutil.copytree(LEVEL_1_1_FOLDER, levels_folder / "w1" / "1-1-hello-terminal")
        copy_folder = levels_folder / "w1" / "1-2-copy"
        shutil.copytree(LEVEL_1_1_FOLDER, copy_folder)
        level_file = copy_folder / "level.toml"
        level_file.write_text(level_file.read_text(encoding="utf-8").replace(
            'id = "1-1"', 'id = "1-2"'), encoding="utf-8")

        player = GameRunner(self, levels_folder)
        player.play(["play 1-1", "quit"])
        player.write_files("1-1", solutions(level_1_1(), "wrong"))
        text = player.play(["submit", "play 1-2", "quit"])
        self.assertNotIn("CLEARED", text)
        self.assertIn("You need 70 % to clear this level.", text)
        score = int(text.split("LEVEL SCORE ")[1].split(" %")[0])
        self.assertLess(score, 70)
        self.assertIn("Level 1-2 is locked. Clear 1-1 with at least 70 % first.", text)


if __name__ == "__main__":
    unittest.main()
