"""Check World 3: all its levels exist and their debug waves are honest."""

import unittest
from pathlib import Path

from engine.level_pack import load_levels
from grader.checks import normalise_output, run_check
from grader.wave_grader import grade_wave
from runner.process import run_code

PROJECT_FOLDER = Path(__file__).parent.parent
WORLD_THREE_IDS = ["3-1", "3-2", "3-3", "3-4", "3-5", "boss-3"]


class TestWorldThree(unittest.TestCase):
    """The content of World 3."""

    def setUp(self):
        """Load the real levels of World 3."""
        self.levels = []
        for level in load_levels(PROJECT_FOLDER / "levels"):
            if level.world == 3:
                self.levels.append(level)

    def test_all_levels_and_the_boss_are_written(self):
        """Five levels and the boss, in map order."""
        self.assertEqual([level.id for level in self.levels], WORLD_THREE_IDS)

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

    def test_boss_cannot_be_passed_by_printing_the_expected_text(self):
        """The output tests use different stock data, so fixed text fails."""
        wave = self.levels[-1].waves[0]
        output_tests = [test for test in wave.tests if "expected_stdout" in test]
        books = {tuple(test["values"].get("book", [])) for test in output_tests}
        self.assertGreaterEqual(len(books - {()}), 2)
        self.assertTrue(grade_wave(wave, wave.reference).all_passed())
        data_lines = wave.starter.split("def add_delivery")[0]
        for test in output_tests:
            cheat = data_lines + f"print({test['expected_stdout']!r}, end='')\n"
            passed = [run_check(other, cheat).passed for other in output_tests]
            self.assertLess(passed.count(True), len(output_tests))

    def test_boss_has_its_own_sprite(self):
        """The Storage Auditor uses a 16 x 16 sprite."""
        self.assertEqual(self.levels[-1].sprite, "boss-storage-auditor")
        sprite_file = PROJECT_FOLDER / "art" / "boss-storage-auditor.txt"
        rows = sprite_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual([len(row) for row in rows], [16] * 16)


if __name__ == "__main__":
    unittest.main()
