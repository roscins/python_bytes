"""The Phase 2 gate: Level 1-1 is fully graded, start to finish, through the real game.

"Level 1-1 is fully graded; each wave's reference solution passes and a
known-wrong solution fails." These tests run the game (run_game) with
the real Level 1-1 and a temporary save file, and type every line of every
solution as a player would: no files, only the game.
"""

import io
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from engine import __main__ as engine_main
from engine.level_pack import load_levels
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
    """Return the "reference" (or "wrong") solution of each wave, as a list of texts."""
    texts = []
    for wave in level.waves:
        if wave.mode == "predict":
            if which == "reference":
                texts.append(wave.answer)
            else:
                texts.append(wave.wrong)
        elif which == "reference":
            texts.append(wave.reference)
        else:
            texts.append(wave.wrong)
    return texts


def typing_for(texts):
    """Return the lines a player types to enter each wave's solution and submit it."""
    lines = []
    number = 0
    for text in texts:
        number = number + 1
        lines.append(f":wave {number}")
        lines.append(":clear")
        lines.extend(text.splitlines())
        lines.append(":submit")
    return lines


class GameRunner:
    """Runs the game with typed lines and a temporary save."""

    def __init__(self, test, levels_folder=LEVELS_FOLDER):
        """Make the temporary folder for one player."""
        folder = make_temporary_folder(test)
        self.test = test
        self.levels_folder = levels_folder
        self.save_path = folder / "save.json"

    def play(self, typed_lines):
        """Start the game, type each line, and return everything it printed."""
        real_stdin = sys.stdin
        self.test.addCleanup(setattr, sys, "stdin", real_stdin)
        sys.stdin = io.StringIO("\n".join(typed_lines) + "\n")
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = engine_main.run_game(self.levels_folder, self.save_path, plain=True)
        self.test.assertEqual(exit_code, 0)
        return output.getvalue()


class TestPhaseTwoGate(unittest.TestCase):
    """Level 1-1 is fully graded through the real game."""

    def test_reference_solutions_clear_level_1_1_with_three_stars(self):
        """Typing every reference solution gives 100 %, 3 stars and the level-clear screen."""
        player = GameRunner(self)
        lines = ["1", "play 1-1"] + typing_for(solutions(level_1_1(), "reference")) + ["map", "quit"]
        text = player.play(lines)
        self.assertIn("LEVEL 1-1 CLEARED · HELLO, TERMINAL", text)
        self.assertIn("POWER-UP: status", text)
        self.assertIn("WAVE 1 · FILL-IN  2/2 tests passed ✓", text)
        self.assertIn("WAVE 2 · BUILD  2/2 tests passed ✓", text)
        self.assertIn("Code quality 4/4", text)
        self.assertIn("WAVE 3 · DEBUG  1/1 test passed ✓", text)
        self.assertIn("LEVEL SCORE 100 %  ★★★", text)
        # World 1 has six nodes on the map (five levels and the boss), 3 stars each.
        self.assertIn("★ 3/18", text)

    def test_each_wave_that_passes_moves_the_player_to_the_next_wave(self):
        """After a fully passed wave, the next wave is shown."""
        player = GameRunner(self)
        first = typing_for(solutions(level_1_1(), "reference"))[:4]
        text = player.play(["1", "play 1-1"] + first + [":quit"])
        self.assertIn("Wave 1 passed! Next:", text)
        self.assertIn("WAVE 2 of 3 · BUILD", text)

    def test_wrong_solutions_score_under_70_and_open_nothing(self):
        """Typing every wrong solution scores under 70 %, and the next level stays locked."""
        levels_folder = make_temporary_folder(self) / "levels"
        shutil.copytree(LEVEL_1_1_FOLDER, levels_folder / "w1" / "1-1-hello-terminal")
        copy_folder = levels_folder / "w1" / "1-2-copy"
        shutil.copytree(LEVEL_1_1_FOLDER, copy_folder)
        level_file = copy_folder / "level.toml"
        level_file.write_text(level_file.read_text(encoding="utf-8").replace(
            'id = "1-1"', 'id = "1-2"'), encoding="utf-8")

        player = GameRunner(self, levels_folder)
        lines = ["1", "play 1-1"] + typing_for(solutions(level_1_1(), "wrong")) + [":play 1-2", ":quit"]
        text = player.play(lines)
        self.assertNotIn("CLEARED", text)
        self.assertIn("Pass every wave to clear this level.", text)
        score = int(text.split("LEVEL SCORE ")[-1].split(" %")[0])
        self.assertLess(score, 70)
        self.assertIn("Level 1-2 is locked. Pass every wave of 1-1 first.", text)


if __name__ == "__main__":
    unittest.main()
