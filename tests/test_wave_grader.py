"""Tests for grader/wave_grader.py, which grades one whole wave."""

import unittest

from engine.level_pack import Wave
from grader.checks import CheckResult
from grader.wave_grader import WaveResult, grade_wave

FILL_IN = Wave("fill-in", "Fill in.", starter="print(___)", reference='print("OK")',
               wrong="print(OK)", tests=[{"expected_stdout": "OK\n"}, {"require": ["Call"]}])

BUILD = Wave("build", "Print OK with a comment.", reference='# Say OK\nprint("OK")',
             wrong='print("OK")',
             tests=[{"expected_stdout": "OK\n"}, {"require_comment": True}])

PREDICT = Wave("debug", "What does it print?", mode="predict", code='print("ONE")',
               answer="ONE", wrong="TWO")


class TestGradeWave(unittest.TestCase):
    """Check grading each kind of wave."""

    def test_fill_in_reference_passes(self):
        """The fill-in reference passes every test and has no quality score."""
        result = grade_wave(FILL_IN, FILL_IN.reference)
        self.assertTrue(result.all_passed())
        self.assertEqual(result.test_count(), 2)
        self.assertIsNone(result.quality)
        self.assertIsNone(result.quality_share())

    def test_fill_in_with_blank_left_is_not_run(self):
        """A blank still in the code gives one failed check."""
        result = grade_wave(FILL_IN, FILL_IN.starter)
        self.assertEqual(result.test_count(), 1)
        self.assertFalse(result.all_passed())
        self.assertIn("___", result.checks[0].message)

    def test_build_has_quality(self):
        """A build wave is checked against the style rules too."""
        result = grade_wave(BUILD, BUILD.reference)
        self.assertTrue(result.all_passed())
        self.assertEqual(result.quality_share(), 1.0)

    def test_build_wrong_solution_fails_one_test(self):
        """Without a comment, one of two tests fails."""
        result = grade_wave(BUILD, BUILD.wrong)
        self.assertEqual(result.passed_count(), 1)
        self.assertEqual(result.share_passed(), 0.5)
        self.assertLess(result.quality_share(), 1.0)

    def test_predict_right_answer(self):
        """The right answer passes, even with a trailing new line."""
        self.assertTrue(grade_wave(PREDICT, "ONE\n").all_passed())

    def test_predict_wrong_answer(self):
        """A wrong answer fails without giving the answer away."""
        result = grade_wave(PREDICT, "TWO")
        self.assertFalse(result.all_passed())
        self.assertNotIn("ONE", result.checks[0].message)

    def test_predict_empty_answer(self):
        """An empty answer fails and says it is empty."""
        self.assertIn("empty", grade_wave(PREDICT, "  ").checks[0].message)


class TestWaveResult(unittest.TestCase):
    """Check the counting methods of WaveResult."""

    def test_no_checks_is_not_all_passed(self):
        """A result with no checks has passed nothing."""
        result = WaveResult([])
        self.assertFalse(result.all_passed())
        self.assertEqual(result.share_passed(), 0.0)

    def test_quality_share(self):
        """The quality share is the share of rules passed."""
        rules = [CheckResult(True, "a"), CheckResult(False, "b", "no")]
        self.assertEqual(WaveResult([], rules).quality_share(), 0.5)


class TestWaveTimeLimit(unittest.TestCase):
    """grade_wave runs the player's program with the wave's own limit."""

    SLEEPY = 'import time\ntime.sleep(2.3)\nprint("OK")\n'

    def make_wave(self, time_limit):
        """Return a build wave with the given time limit."""
        return Wave("build", "Wait, then print OK.", reference=self.SLEEPY, wrong="print(1)",
                    tests=[{"expected_stdout": "OK\n"}], time_limit=time_limit)

    def test_a_longer_limit_lets_a_slow_program_pass(self):
        """2.3 seconds is over the default 2, but within a limit of 4."""
        self.assertTrue(grade_wave(self.make_wave(4), self.SLEEPY).all_passed())

    def test_a_wave_without_a_limit_uses_the_default(self):
        """The same program fails with the default limit."""
        self.assertFalse(grade_wave(self.make_wave(None), self.SLEEPY).all_passed())

    def test_wave_has_no_limit_unless_given(self):
        """Wave.time_limit is None by default."""
        self.assertIsNone(FILL_IN.time_limit)


if __name__ == "__main__":
    unittest.main()
