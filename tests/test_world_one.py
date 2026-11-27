"""Check World 1: all its levels exist and their debug waves are honest.

tests/test_levels.py already checks the limits and the reference and wrong
solutions of every level. These tests add what those cannot see: a predict
wave's answer must be what Python really prints, and a fix-the-bug starter
must really have a bug. The last tests cover Boss 1 and play the whole world.
"""

import json
import tempfile
import unittest
from pathlib import Path

from engine.__main__ import run_game
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

class TestBossOne(unittest.TestCase):
    """Boss 1, The Corrupted Bootloader."""

    def setUp(self):
        """Find the real boss."""
        for level in load_levels(LEVELS_FOLDER):
            if level.id == "boss-1":
                self.boss = level

    def test_reference_knocks_off_all_health(self):
        """The reference solution passes every hidden test."""
        wave = self.boss.waves[0]
        self.assertTrue(grade_wave(wave, wave.reference).all_passed())

    def test_wrong_solution_and_scrambled_report_fail(self):
        """Neither the wrong solution nor the unchanged starter wins."""
        wave = self.boss.waves[0]
        for text in [wave.wrong, wave.starter]:
            self.assertFalse(grade_wave(wave, text).all_passed())

    def test_boss_has_its_own_sprite(self):
        """The sprite is a 16 x 16 file in art/."""
        path = LEVELS_FOLDER.parent / "art" / (self.boss.sprite + ".txt")
        rows = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 16)
        for row in rows:
            self.assertEqual(len(row), 16)


def code_waves():
    """Yield (level id, wave) for every World 1 wave where code is written, from 1-2 on.

    1-1 teaches print() and text, so there printing the text is the task. A
    predict wave asks for the output itself.
    """
    for level in load_levels(LEVELS_FOLDER):
        if level.world == 1 and level.id != "1-1":
            for wave in level.waves:
                if wave.mode != "predict":
                    yield level.id, wave


class TestPrintingTheAnswerFails(unittest.TestCase):
    """Typing the expected output into print() must not pass a wave."""

    def cheat_for(self, wave):
        """Return a program that sets the tested variables, then only prints the expected text."""
        lines = ["# cheat"]
        expected = ""
        for test in wave.tests:
            if "values" in test:
                for name in test["values"]:
                    lines.append(f"{name} = 1")
            elif "expected_stdout" in test:
                expected = test["expected_stdout"]
        # Dead code that uses every construct the wave asks for.
        lines.append('padding = "abc"')
        lines.append('unused = f"{padding[0:1]}" == str(1 + 1)')
        lines.append(f"print({expected.rstrip()!r})")
        return "\n".join(lines) + "\n"

    def test_every_code_wave_has_a_changed_values_test(self):
        """Each code wave runs the player's code with other data."""
        for level_id, wave in code_waves():
            with self.subTest(level=level_id, wave=wave.kind):
                self.assertTrue(any("values" in test for test in wave.tests))

    def test_print_only_cheats_fail(self):
        """The cheat prints the right text and still does not pass."""
        for level_id, wave in code_waves():
            with self.subTest(level=level_id, wave=wave.kind):
                result = grade_wave(wave, self.cheat_for(wave))
                self.assertFalse(result.all_passed())


class TestWorldOneThroughTheGame(unittest.TestCase):
    """A new player can clear the whole of World 1 in one sitting."""

    def test_clear_every_level_and_the_boss(self):
        """Type every reference solution, in order, into the real game."""
        lines = ["1"]
        for level in load_levels(LEVELS_FOLDER):
            if level.world != 1:
                continue
            lines.append("play " + level.id)
            for wave in level.waves:
                text = wave.reference
                if wave.mode == "predict":
                    text = wave.answer
                lines.append(":clear")
                lines.extend(text.strip().splitlines())
                lines.append(":submit")
        lines.append(":quit")
        with tempfile.TemporaryDirectory() as folder:
            save_path = Path(folder) / "save.json"
            typed = iter(lines)
            output = []
            run_game(save_path=save_path, workspace_root=Path(folder) / "workspace",
                     read_line=lambda prompt: next(typed), write=output.append,
                     plain=True, install_signals=False, pause=lambda seconds: None)
            saved = json.loads(save_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["cleared"], WORLD_ONE_LEVELS + ["boss-1"])
        self.assertIn("BOSS DEFEATED", "\n".join(output))


if __name__ == "__main__":
    unittest.main()
