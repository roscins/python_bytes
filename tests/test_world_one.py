"""Check World 1: all its levels exist and their debug waves are honest.

tests/test_levels.py already checks the limits and the reference and wrong
solutions of every level. These tests add what those cannot see: a predict
wave's answer must be what Python really prints, and a fix-the-bug starter
must really have a bug.
"""

import unittest
from pathlib import Path

from engine.level_pack import load_levels
from grader.checks import normalise_output
from grader.wave_grader import grade_wave
from runner.process import run_code

LEVELS_FOLDER = Path(__file__).parent.parent / "levels"
WORLD_ONE_LEVELS = ["1-1", "1-2", "1-3", "1-4", "1-5"]


def world_one():
    """Return the real levels of World 1, without the boss."""
    levels = []
    for level in load_levels(LEVELS_FOLDER):
        if level.world == 1 and not level.boss:
            levels.append(level)
    return levels


class TestWorldOne(unittest.TestCase):
    """The content of World 1."""

    def test_all_five_levels_are_written(self):
        """The levels 1-1 to 1-5 are there, in map order."""
        ids = []
        for level in world_one():
            ids.append(level.id)
        self.assertEqual(ids, WORLD_ONE_LEVELS)

    def test_predict_answers_are_what_python_prints(self):
        """Running a predict wave's code gives exactly its answer."""
        for level in world_one():
            for wave in level.waves:
                if wave.mode != "predict":
                    continue
                with self.subTest(level=level.id):
                    printed = run_code(wave.code).stdout
                    self.assertEqual(normalise_output(printed), normalise_output(wave.answer))

    def test_fix_the_bug_starters_fail(self):
        """A debug starter handed in unchanged does not pass."""
        for level in world_one():
            wave = level.waves[2]
            if wave.mode == "predict":
                continue
            with self.subTest(level=level.id):
                self.assertFalse(grade_wave(wave, wave.starter).all_passed())

    def test_cutscenes_run(self):
        """The code shown in every cutscene runs without an error."""
        for level in world_one():
            with self.subTest(level=level.id):
                self.assertEqual(run_code(level.cutscene).exit_code, 0)


if __name__ == "__main__":
    unittest.main()
