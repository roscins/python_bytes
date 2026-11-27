"""Check every real level in levels/ against docs/level-style-guide.md.

The loader only checks that a level has the right structure. These tests
check the guide's content rules, so a level that breaks one cannot be
merged. The limits themselves live in grader/level_limits.py, so that
tools/check_level.py checks the same ones.
"""

import re
import unittest
from pathlib import Path

from engine.level_pack import load_levels
from grader.level_limits import (
    FORBIDDEN_WORDS,
    MAX_BLANKS,
    MAX_BRIEF_SENTENCES,
    MAX_CUTSCENE_LINES,
    MIN_BLANKS,
    MIN_TESTS_PER_WAVE,
    WAVE_ORDER,
    count_lines,
    count_sentences,
    is_valid_python,
    max_debug_lines,
)
from grader.wave_grader import BLANK, grade_wave

PROJECT_FOLDER = Path(__file__).parent.parent
LEVELS_FOLDER = PROJECT_FOLDER / "levels"
LEVEL_GUIDE = PROJECT_FOLDER / "docs" / "level-style-guide.md"


def player_texts(level):
    """Return every piece of text in `level` that the player reads."""
    texts = [level.title, level.cutscene]
    texts.extend(level.tips)
    for wave in level.waves:
        texts.append(wave.brief)
        texts.extend(wave.hints)
    return texts


class TestRealLevels(unittest.TestCase):
    """Check each level in levels/ against the level style guide."""

    def setUp(self):
        """Load every real level, leaving out bosses."""
        self.levels = []
        for level in load_levels(LEVELS_FOLDER):
            if not level.id.startswith("boss-"):
                self.levels.append(level)

    def test_level_1_1_exists(self):
        """The test level from Phase 1 is there."""
        ids = []
        for level in self.levels:
            ids.append(level.id)
        self.assertIn("1-1", ids)

    def test_level_sits_in_its_world_folder(self):
        """A level of world 1 lives in levels/w1/."""
        for level in self.levels:
            with self.subTest(level=level.id):
                self.assertEqual(level.folder.parent.name, f"w{level.world}")

    def test_three_waves_in_order(self):
        """Fill-in, build and debug, in that order; only review waves may follow."""
        for level in self.levels:
            with self.subTest(level=level.id):
                kinds = []
                for wave in level.waves:
                    kinds.append(wave.kind)
                self.assertEqual(kinds[:len(WAVE_ORDER)], WAVE_ORDER)
                for wave in level.waves[len(WAVE_ORDER):]:
                    self.assertEqual(wave.mode, "review")

    def test_cutscene_length_and_story(self):
        """A cutscene is at most 25 lines and has at least one # >> story line."""
        for level in self.levels:
            with self.subTest(level=level.id):
                self.assertLessEqual(count_lines(level.cutscene), MAX_CUTSCENE_LINES)
                self.assertIn("# >>", level.cutscene)

    def test_code_is_valid_python(self):
        """The cutscene, reference solutions and predict code all compile."""
        for level in self.levels:
            with self.subTest(level=level.id, part="cutscene"):
                self.assertTrue(is_valid_python(level.cutscene))
            for wave in level.waves:
                with self.subTest(level=level.id, wave=wave.kind):
                    if wave.reference is not None:
                        self.assertTrue(is_valid_python(wave.reference))
                    if wave.mode == "predict":
                        self.assertTrue(is_valid_python(wave.code))

    def test_fill_in_has_one_to_three_blanks(self):
        """The starter of a fill-in wave has 1 to 3 blanks; the reference has none."""
        for level in self.levels:
            wave = level.waves[0]
            if wave.is_quiz():
                continue
            with self.subTest(level=level.id):
                self.assertIsNotNone(wave.starter)
                blanks = wave.starter.count(BLANK)
                self.assertGreaterEqual(blanks, MIN_BLANKS)
                self.assertLessEqual(blanks, MAX_BLANKS)
                self.assertNotIn(BLANK, wave.reference)

    def test_build_brief_is_at_most_five_sentences(self):
        """The brief of a build wave is short."""
        for level in self.levels:
            with self.subTest(level=level.id):
                self.assertLessEqual(count_sentences(level.waves[1].brief), MAX_BRIEF_SENTENCES)

    def test_debug_code_is_at_most_ten_lines(self):
        """The code in a debug wave is at most 10 lines."""
        for level in self.levels:
            wave = level.waves[2]
            if wave.is_quiz():
                continue
            with self.subTest(level=level.id):
                if wave.mode == "predict":
                    code = wave.code
                else:
                    code = wave.starter
                self.assertIsNotNone(code)
                self.assertLessEqual(count_lines(code), max_debug_lines(level.world))

    def test_every_wave_has_enough_tests(self):
        """At least 2 tests per wave; a predict wave has a right and a wrong answer."""
        for level in self.levels:
            for wave in level.waves:
                with self.subTest(level=level.id, wave=wave.kind):
                    if wave.mode is not None:
                        self.assertNotEqual(wave.answer.strip(), wave.wrong.strip())
                    else:
                        self.assertGreaterEqual(len(wave.tests), MIN_TESTS_PER_WAVE)

    def test_reference_and_wrong_differ(self):
        """A wrong solution must really be different from the reference."""
        for level in self.levels:
            for wave in level.waves:
                if wave.reference is None:
                    continue
                with self.subTest(level=level.id, wave=wave.kind):
                    self.assertNotEqual(wave.reference.strip(), wave.wrong.strip())

    def test_no_easy_or_simple(self):
        """The player never reads "easy" or "simple"."""
        for level in self.levels:
            for text in player_texts(level):
                for word in FORBIDDEN_WORDS:
                    with self.subTest(level=level.id, word=word):
                        self.assertIsNone(re.search(rf"\b{word}\b", text, re.IGNORECASE))


class TestPredictExplanations(unittest.TestCase):
    """Every predict wave can say why its answer is right."""

    def test_every_predict_wave_has_an_explanation(self):
        """Needed when the answer is revealed."""
        for level in load_levels(LEVELS_FOLDER):
            for wave in level.waves:
                if wave.mode == "predict":
                    with self.subTest(level=level.id):
                        self.assertTrue(wave.explanation and wave.explanation.strip())


class TestRealLevelsKeepEveryLimit(unittest.TestCase):
    """The same limits, through check_limits, and the progression rules."""

    def test_real_levels_have_no_limit_problems(self):
        """check_limits finds nothing in any real level, bosses included."""
        from grader.level_limits import check_limits

        for level in load_levels(LEVELS_FOLDER):
            with self.subTest(level=level.id):
                self.assertEqual(check_limits(level), [])

    def test_real_levels_follow_the_progression_rules(self):
        """Rule 1 and the match with concepts.toml hold in every real level."""
        from grader.progression import check_level_code, check_level_matches, load_curriculum

        curriculum = load_curriculum()
        for level in load_levels(LEVELS_FOLDER):
            with self.subTest(level=level.id):
                self.assertEqual(check_level_matches(curriculum, level), [])
                self.assertEqual(check_level_code(curriculum, level), [])


class TestPhaseTwoGate(unittest.TestCase):
    """The Phase 2 gate: each reference solution passes, each wrong one fails."""

    def setUp(self):
        """Load every real level, leaving out bosses."""
        self.levels = []
        for level in load_levels(LEVELS_FOLDER):
            if not level.id.startswith("boss-"):
                self.levels.append(level)

    def test_reference_solutions_pass_every_test(self):
        """Every reference solution (or right answer) passes, with full code quality."""
        for level in self.levels:
            for wave in level.waves:
                with self.subTest(level=level.id, wave=wave.kind):
                    if wave.mode is not None:
                        result = grade_wave(wave, wave.answer)
                    else:
                        result = grade_wave(wave, wave.reference)
                    failed = []
                    for check in result.checks:
                        if not check.passed:
                            failed.append(check.name + ": " + check.message)
                    self.assertTrue(result.all_passed(), failed)
                    if result.quality is not None:
                        self.assertEqual(result.quality_share(), 1.0)

    def test_wrong_solutions_fail_at_least_one_test(self):
        """Every wrong solution (or wrong answer) fails at least one test."""
        for level in self.levels:
            for wave in level.waves:
                with self.subTest(level=level.id, wave=wave.kind):
                    self.assertFalse(grade_wave(wave, wave.wrong).all_passed())


class TestGuideExample(unittest.TestCase):
    """Check that Level 1-1 and the guide's example stay the same."""

    def test_level_1_1_is_the_guide_example(self):
        """levels/w1/1-1-hello-terminal/level.toml is the guide's TOML example."""
        guide = LEVEL_GUIDE.read_text(encoding="utf-8")
        start = guide.index("```toml\n") + len("```toml\n")
        end = guide.index("```", start)
        example = guide[start:end]
        level_path = LEVELS_FOLDER / "w1" / "1-1-hello-terminal" / "level.toml"
        self.assertEqual(level_path.read_text(encoding="utf-8"), example)


class TestHelpers(unittest.TestCase):
    """Check the small helpers used by the level tests."""

    def test_count_sentences(self):
        """Full stops, question marks and exclamation marks end sentences."""
        self.assertEqual(count_sentences("One. Two? Three!"), 3)
        self.assertEqual(count_sentences("Print 3.5 now."), 1)

    def test_count_lines_ignores_blank_ends(self):
        """Blank lines at the start and end are not counted."""
        self.assertEqual(count_lines("\nprint(1)\nprint(2)\n"), 2)

    def test_is_valid_python(self):
        """Code that compiles is valid; a missing quote is not."""
        self.assertTrue(is_valid_python('print("OK")'))
        self.assertFalse(is_valid_python("print(SNEK ONLINE)"))


if __name__ == "__main__":
    unittest.main()
