"""The catches test: the player's test function against a correct and a broken version."""

import unittest

from engine.level_pack import LevelError, check_test
from grader.checks import run_check

CORRECT = "def is_low(value):\n    return value <= 5\n"
BROKEN = "def is_low(value):\n    return value < 5\n"
CHECK = {"catches": {"test": "test_is_low", "function": "is_low",
                     "correct": CORRECT, "broken": BROKEN}}


def run(test_body, own=CORRECT):
    """Grade a program with is_low and a test_is_low that has `test_body`."""
    return run_check(CHECK, f"{own}\ndef test_is_low():\n    {test_body}\n")


class TestCatches(unittest.TestCase):
    """Which test functions count."""

    def test_a_boundary_assert_passes(self):
        """It tells the two versions apart."""
        self.assertTrue(run("assert is_low(5)").passed)

    def test_the_players_own_function_is_swapped_out(self):
        """So a bug of their own does not matter here."""
        self.assertTrue(run("assert is_low(5)", own=BROKEN).passed)

    def test_weak_tests_fail(self):
        """Empty, trivial and off-boundary tests miss the fault."""
        for body in ["pass", "assert True", "assert is_low(1)"]:
            with self.subTest(body=body):
                self.assertIn("still passes", run(body).message)

    def test_a_test_that_always_fails_does_not_count(self):
        """It must pass on the correct version."""
        self.assertIn("even when", run("assert False").message)

    def test_a_missing_test_function(self):
        """The player is told the name."""
        self.assertIn("no function named test_is_low", run_check(CHECK, CORRECT).message)

    def test_a_crash_is_not_a_catch(self):
        """Only a failed assert counts."""
        self.assertFalse(run("is_low(None)").passed)

    def test_the_loader_checks_the_table(self):
        """Both versions must be Python that defines the function."""
        check_test(CHECK, "test")
        for broken in ["def other():\n    pass\n", "def (", 3]:
            bad = {"catches": dict(CHECK["catches"], broken=broken)}
            with self.subTest(broken=broken), self.assertRaises(LevelError):
                check_test(bad, "test")


if __name__ == "__main__":
    unittest.main()
