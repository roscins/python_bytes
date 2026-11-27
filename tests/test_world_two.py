"""Check World 2: all its levels exist and their debug waves are honest."""

import unittest
from pathlib import Path

from engine.level_pack import load_levels
from grader.checks import normalise_output
from grader.wave_grader import grade_wave
from runner.process import run_code

PROJECT_FOLDER = Path(__file__).parent.parent
WORLD_TWO_IDS = ["2-1", "2-2", "2-3", "2-4", "2-5", "boss-2"]


class TestWorldTwo(unittest.TestCase):
    """The content of World 2."""

    def setUp(self):
        """Load the real levels of World 2."""
        self.levels = []
        for level in load_levels(PROJECT_FOLDER / "levels"):
            if level.world == 2:
                self.levels.append(level)

    def test_all_levels_and_the_boss_are_written(self):
        """Five levels and the boss, in map order."""
        self.assertEqual([level.id for level in self.levels], WORLD_TWO_IDS)

    def test_debug_waves_are_honest(self):
        """A predict answer is what Python prints; a buggy starter fails."""
        for level in self.levels:
            for wave in level.waves:
                if wave.kind != "debug":
                    continue
                with self.subTest(level=level.id):
                    if wave.mode == "predict":
                        printed = run_code(wave.code).stdout
                        self.assertEqual(normalise_output(printed), normalise_output(wave.answer))
                    else:
                        self.assertFalse(grade_wave(wave, wave.starter).all_passed())

    def test_boss_has_its_own_sprite(self):
        """The Night Patrol uses a 16 x 16 sprite."""
        self.assertEqual(self.levels[-1].sprite, "boss-night-patrol")
        sprite_file = PROJECT_FOLDER / "art" / "boss-night-patrol.txt"
        rows = sprite_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual([len(row) for row in rows], [16] * 16)


if __name__ == "__main__":
    unittest.main()
