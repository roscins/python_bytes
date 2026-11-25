"""Tests for grader/style.py, the code-quality rules."""

import unittest

from grader.style import (
    ALL_RULES,
    COMMENT_RULE,
    DOCSTRING_RULE,
    INDENT_RULE,
    NAMING_RULE,
    is_good_name,
    style_checks,
)

GOOD_CODE = '''# A robot that reports its battery.
MAX_BATTERY = 100


class WeldingRobot:
    """A robot that welds."""

    def report(self, battery_level):
        """Print the battery level."""
        if battery_level > MAX_BATTERY:
            print("TOO HIGH")
        print(battery_level)
'''


def results_by_rule(code):
    """Return the style results for `code` as a dict from rule name to CheckResult."""
    results = {}
    for result in style_checks(code):
        results[result.name] = result
    return results


class TestStyleChecks(unittest.TestCase):
    """Check each rule on good and bad code."""

    def test_good_code_passes_every_rule(self):
        """Code that follows every rule passes all four."""
        results = style_checks(GOOD_CODE)
        self.assertEqual(len(results), len(ALL_RULES))
        for result in results:
            with self.subTest(rule=result.name):
                self.assertTrue(result.passed, result.message)

    def test_bad_names_are_listed(self):
        """camelCase names fail and are listed once each."""
        code = "# Names\nbatteryLevel = 1\nbatteryLevel = 2\ndef GetIt(myArg):\n    \"\"\"Doc.\"\"\"\n"
        result = results_by_rule(code)[NAMING_RULE]
        self.assertFalse(result.passed)
        self.assertIn("batteryLevel, GetIt, myArg", result.message)

    def test_class_must_be_cap_words(self):
        """A lower-case class name fails."""
        code = '# A robot\nclass robot:\n    """A robot."""\n'
        self.assertIn("robot", results_by_rule(code)[NAMING_RULE].message)

    def test_tab_indent_fails(self):
        """A tab indent fails and names the line."""
        code = "# Loop\nfor n in range(3):\n\tprint(n)\n"
        result = results_by_rule(code)[INDENT_RULE]
        self.assertFalse(result.passed)
        self.assertIn("Line 3 is indented with a tab", result.message)

    def test_two_space_indent_fails(self):
        """An indent of 2 spaces fails."""
        code = "# Loop\nfor n in range(3):\n  print(n)\n"
        self.assertIn("indented by 2 spaces", results_by_rule(code)[INDENT_RULE].message)

    def test_nested_four_space_indents_pass(self):
        """8 spaces inside a nested block is fine."""
        code = "# Grid\nfor x in range(2):\n    for y in range(2):\n        print(x, y)\n"
        self.assertTrue(results_by_rule(code)[INDENT_RULE].passed)

    def test_missing_comment_fails(self):
        """Code without a comment fails the comment rule."""
        self.assertFalse(results_by_rule('print("HI")')[COMMENT_RULE].passed)

    def test_missing_docstring_is_named(self):
        """A function without a docstring fails and is named."""
        code = "# Move\ndef move():\n    return 1\n"
        result = results_by_rule(code)[DOCSTRING_RULE]
        self.assertFalse(result.passed)
        self.assertIn("move", result.message)

    def test_code_without_functions_passes_docstrings(self):
        """With no functions or classes, the docstring rule passes."""
        self.assertTrue(results_by_rule('# Hi\nprint("HI")')[DOCSTRING_RULE].passed)

    def test_unreadable_code_fails_every_rule(self):
        """Code Python cannot read fails all four rules."""
        for result in style_checks("print(SNEK ONLINE)"):
            self.assertFalse(result.passed)

    def test_empty_code_fails_every_rule(self):
        """An empty file has no quality to score."""
        for result in style_checks("   \n"):
            self.assertFalse(result.passed)
            self.assertIn("Write some code first", result.message)


class TestIsGoodName(unittest.TestCase):
    """Check which names count as good."""

    def test_good_names(self):
        """snake_case, UPPER_CASE, leading underscores and _ are good."""
        for name in ["battery", "battery_level", "MAX_BATTERY", "_hidden", "__init__", "_", "x1"]:
            with self.subTest(name=name):
                self.assertTrue(is_good_name(name))

    def test_bad_names(self):
        """camelCase and CapWords are not good for variables."""
        for name in ["batteryLevel", "Battery", "BatteryLevel"]:
            with self.subTest(name=name):
                self.assertFalse(is_good_name(name))


if __name__ == "__main__":
    unittest.main()
