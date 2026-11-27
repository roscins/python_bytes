"""Output tests with `values`: the grader changes a variable and runs the code again."""

import unittest

from engine.level_pack import LevelError, check_test
from grader.checks import change_values, run_check

TEST = {"expected_stdout": "8\n", "values": {"size": 4}}


class TestChangedValues(unittest.TestCase):
    """change_values and the checks that use it."""

    def test_code_that_uses_the_variable_passes(self):
        """The output follows the new value."""
        self.assertTrue(run_check(TEST, "size = 1\nprint(size * 2)\n").passed)

    def test_printing_the_answer_fails(self):
        """A fixed number does not follow the new value."""
        self.assertTrue(run_check({"expected_stdout": "8\n"}, "print(8)").passed)
        self.assertFalse(run_check(TEST, "size = 4\nsize = 1\nprint(2)\n").passed)

    def test_a_missing_variable_is_explained(self):
        """The player is told which line to keep."""
        result = run_check(TEST, "print(8)")
        self.assertFalse(result.passed)
        self.assertIn("size = ...", result.message)

    def test_only_the_first_assignment_changes(self):
        """A later assignment is the program's own work."""
        changed, missing = change_values("a = 1\na = 2\n", {"a": 9})
        self.assertEqual(changed, "a = 9\na = 2")
        self.assertEqual(missing, [])

    def test_code_python_cannot_read_fails(self):
        """A syntax error is a failed check, not a crash of the grader."""
        self.assertFalse(run_check(TEST, "size = (").passed)

    def test_the_check_name_says_what_changed(self):
        """The player sees which values were tried."""
        self.assertIn("when the grader sets size = 4", run_check(TEST, "size = 1\nprint(size)").name)

    def test_loader_rejects_values_on_other_tests(self):
        """values only makes sense when output is compared."""
        for bad in [{"require": ["Name"], "values": {"a": 1}},
                    {"expected_stdout": "", "values": {}},
                    {"expected_stdout": "", "values": {"a": [1]}}]:
            with self.subTest(bad=bad), self.assertRaises(LevelError):
                check_test(bad, "here")


if __name__ == "__main__":
    unittest.main()
