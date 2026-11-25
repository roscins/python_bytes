"""Check grader/level_limits.py: the limits of docs/level-style-guide.md.

Each test starts from a small level that breaks no limit, breaks one, and
looks for the one-line problem.
"""

import unittest
from pathlib import Path

from engine.level_pack import load_level
from grader.level_limits import (
    check_limits,
    count_lines,
    count_sentences,
    is_valid_python,
    max_debug_lines,
)
from tests.helpers import make_boss_level, make_full_level

LEVEL_1_1 = Path(__file__).parent.parent / "levels" / "w1" / "1-1-hello-terminal" / "level.toml"


def mentions(problems, text):
    """Return True if any problem contains `text`."""
    for problem in problems:
        if text in problem:
            return True
    return False


class TestHelpers(unittest.TestCase):
    """The small counting functions."""

    def test_count_lines_ignores_blank_lines_at_the_ends(self):
        """Blank lines around the text do not count."""
        self.assertEqual(count_lines("\n\na\nb\n\n"), 2)

    def test_count_sentences(self):
        """A sentence ends with . ! or ? and a space or the end."""
        self.assertEqual(count_sentences("One. Two! Three? Four"), 3)

    def test_is_valid_python(self):
        """compile() decides."""
        self.assertTrue(is_valid_python("print(1)"))
        self.assertFalse(is_valid_python("print("))

    def test_debug_limit_grows_in_world_three(self):
        """10 lines before World 3, 30 from World 3."""
        self.assertEqual(max_debug_lines(1), 10)
        self.assertEqual(max_debug_lines(2), 10)
        self.assertEqual(max_debug_lines(3), 30)
        self.assertEqual(max_debug_lines(8), 30)


class TestLimits(unittest.TestCase):
    """One limit at a time."""

    def test_good_level_has_no_problems(self):
        """The small level breaks nothing."""
        self.assertEqual(check_limits(make_full_level()), [])

    def test_real_level_1_1_has_no_problems(self):
        """The Level 1-1 in levels/ breaks nothing."""
        self.assertEqual(check_limits(load_level(LEVEL_1_1)), [])

    def test_good_boss_has_no_problems(self):
        """The helper boss breaks nothing."""
        self.assertEqual(check_limits(make_boss_level()), [])

    def test_wrong_folder(self):
        """A level of world 1 must sit in w1/."""
        level = make_full_level()
        level.folder = Path("levels/w2/1-1-hello")
        self.assertTrue(mentions(check_limits(level), "w1"))

    def test_waves_must_be_fill_in_build_debug(self):
        """The three waves come in this order."""
        level = make_full_level()
        level.waves.reverse()
        self.assertTrue(mentions(check_limits(level), "fill-in, build, debug"))

    def test_cutscene_too_long(self):
        """A cutscene is at most 25 lines."""
        level = make_full_level()
        level.cutscene = "# >> Hi.\n" + "print('a')\n" * 30
        self.assertTrue(mentions(check_limits(level), "cutscene"))

    def test_cutscene_needs_a_story_line(self):
        """A cutscene has at least one # >> line."""
        level = make_full_level()
        level.cutscene = 'print("a")'
        self.assertTrue(mentions(check_limits(level), "# >>"))

    def test_code_must_be_valid_python(self):
        """The cutscene, references and predict code compile."""
        level = make_full_level()
        level.cutscene = "# >> Hi.\nprint("
        level.waves[1].reference = "print("
        level.waves[2].code = "print("
        problems = check_limits(level)
        self.assertTrue(mentions(problems, "cutscene is not valid Python"))
        self.assertTrue(mentions(problems, "wave 2 (build) reference is not valid Python"))
        self.assertTrue(mentions(problems, "wave 3 (debug) code is not valid Python"))

    def test_fill_in_blanks(self):
        """A fill-in starter has 1 to 3 blanks; the reference has none."""
        level = make_full_level()
        level.waves[0].starter = 'print("a")'
        self.assertTrue(mentions(check_limits(level), "blank"))
        level.waves[0].starter = "print(___, ___, ___, ___)"
        self.assertTrue(mentions(check_limits(level), "blank"))
        level = make_full_level()
        level.waves[0].reference = "print(___)"
        self.assertTrue(mentions(check_limits(level), "reference"))

    def test_build_brief_too_long(self):
        """A brief is at most 5 sentences."""
        level = make_full_level()
        level.waves[1].brief = "One. Two. Three. Four. Five. Six."
        self.assertTrue(mentions(check_limits(level), "brief"))

    def test_debug_code_too_long_in_world_one_but_not_in_world_three(self):
        """15 lines break World 1's limit of 10 but not World 3's limit of 30."""
        level = make_full_level()
        level.waves[2].code = 'print("a")\n' * 15
        self.assertTrue(mentions(check_limits(level), "debug"))
        level.world = 3
        level.folder = None
        self.assertFalse(mentions(check_limits(level), "lines"))

    def test_each_wave_needs_two_tests(self):
        """One test is not enough."""
        level = make_full_level()
        level.waves[1].tests = [{"expected_stdout": "a\n"}]
        self.assertTrue(mentions(check_limits(level), "wave 2 (build) has 1 test"))

    def test_predict_answer_must_differ_from_wrong(self):
        """The right answer and the wrong one are not the same."""
        level = make_full_level()
        level.waves[2].wrong = "a"
        self.assertTrue(mentions(check_limits(level), "answer"))

    def test_reference_must_differ_from_wrong(self):
        """A wrong solution is really different."""
        level = make_full_level()
        level.waves[1].wrong = level.waves[1].reference
        self.assertTrue(mentions(check_limits(level), "wrong"))

    def test_easy_and_simple_are_forbidden(self):
        """The player never reads "easy" or "simple"."""
        level = make_full_level()
        level.waves[1].brief = "This is easy."
        level.waves[0].hints = ["a", "b", "A Simple fix."]
        problems = check_limits(level)
        self.assertTrue(mentions(problems, "easy"))
        self.assertTrue(mentions(problems, "simple"))

    def test_boss_cutscene_is_checked_too(self):
        """A boss has a cutscene with a story line."""
        level = make_boss_level()
        level.cutscene = "print('a')"
        self.assertTrue(mentions(check_limits(level), "# >>"))

    def test_boss_needs_a_different_wrong_solution(self):
        """A boss's wrong solution differs from its reference."""
        level = make_boss_level()
        level.waves[0].wrong = level.waves[0].reference
        self.assertTrue(mentions(check_limits(level), "wrong"))


if __name__ == "__main__":
    unittest.main()
