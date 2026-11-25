"""Tests for grader/checks.py: each kind of test a level can run."""

import unittest

from grader.checks import (
    construct_name,
    count_comments,
    normalise_output,
    run_check,
    test_kind,
    values_match,
)


class TestNormaliseOutput(unittest.TestCase):
    """Check how output is tidied before it is compared."""

    def test_trailing_spaces_and_blank_lines_go(self):
        """Spaces at line ends and blank lines at the end are removed."""
        self.assertEqual(normalise_output("ONE  \nTWO\n\n\n"), "ONE\nTWO")

    def test_leading_spaces_stay(self):
        """Spaces at the start of a line matter, so they are kept."""
        self.assertEqual(normalise_output("  ONE\n"), "  ONE")


class TestExpectedStdout(unittest.TestCase):
    """Check the expected_stdout test."""

    def test_right_output_passes(self):
        """The exact output passes."""
        result = run_check({"expected_stdout": "SNEK ONLINE\n"}, 'print("SNEK ONLINE")')
        self.assertTrue(result.passed)
        self.assertEqual(result.message, "")

    def test_wrong_output_shows_both(self):
        """A wrong output fails, showing what was expected and what was printed."""
        result = run_check({"expected_stdout": "A\nB\n"}, 'print("A", "B")')
        self.assertFalse(result.passed)
        self.assertIn("Expected this output:\n    A\n    B", result.message)
        self.assertIn("Your program printed:\n    A B", result.message)

    def test_fake_input_is_used(self):
        """stdin is sent to the program and named in the check."""
        test = {"expected_stdout": "HI SNEK\n", "stdin": "SNEK\n"}
        result = run_check(test, 'print("HI", input())')
        self.assertTrue(result.passed)
        self.assertIn("input", result.name)

    def test_crash_is_explained(self):
        """A program that crashes fails with the error line."""
        result = run_check({"expected_stdout": "X"}, "print(X)")
        self.assertFalse(result.passed)
        self.assertIn("stopped with an error: NameError", result.message)

    def test_syntax_error_is_explained(self):
        """Code Python cannot read fails with a SyntaxError message."""
        result = run_check({"expected_stdout": "SNEK ONLINE"}, "print(SNEK ONLINE)")
        self.assertIn("SyntaxError", result.message)


class TestExpectedStdoutContains(unittest.TestCase):
    """Check the expected_stdout_contains test."""

    def test_all_pieces_present_passes(self):
        """Every piece appears in the output, so it passes."""
        test = {"expected_stdout_contains": ["Battery: 10 %", "Battery: 15 %"]}
        code = 'print("Battery: 10 %")\nprint("Battery: 15 %")'
        self.assertTrue(run_check(test, code).passed)

    def test_missing_piece_is_named(self):
        """A missing piece fails, and the message names it."""
        test = {"expected_stdout_contains": ["Battery: 10 %", "FULL"]}
        result = run_check(test, 'print("Battery: 10 %")')
        self.assertFalse(result.passed)
        self.assertIn("should contain: FULL", result.message)


class TestCall(unittest.TestCase):
    """Check function tests."""

    CODE = (
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "def pair():\n"
        "    return 1, 2\n"
        "\n"
        "def both():\n"
        "    return {3, 1, 2}\n"
    )

    def test_right_return_value_passes(self):
        """The function returns the expected value."""
        result = run_check({"call": "add", "args": [2, 3], "expected": 5}, self.CODE)
        self.assertTrue(result.passed)
        self.assertEqual(result.name, "add(2, 3) returns 5")

    def test_wrong_return_value_is_shown(self):
        """A wrong value fails, showing what came back."""
        result = run_check({"call": "add", "args": [2, 3], "expected": 6}, self.CODE)
        self.assertFalse(result.passed)
        self.assertIn("should return 6, but it returned 5", result.message)

    def test_floats_match_closely(self):
        """0.1 + 0.2 matches 0.3."""
        result = run_check({"call": "add", "args": [0.1, 0.2], "expected": 0.3}, self.CODE)
        self.assertTrue(result.passed)

    def test_tuple_matches_a_list(self):
        """A returned tuple matches a TOML list."""
        self.assertTrue(run_check({"call": "pair", "expected": [1, 2]}, self.CODE).passed)

    def test_set_matches_a_sorted_list(self):
        """A returned set matches the sorted list of its items."""
        self.assertTrue(run_check({"call": "both", "expected": [1, 2, 3]}, self.CODE).passed)

    def test_missing_function(self):
        """Calling a function that is not there says so."""
        result = run_check({"call": "move", "expected": 1}, self.CODE)
        self.assertFalse(result.passed)
        self.assertIn("no function named move", result.message)

    def test_error_inside_the_function(self):
        """An error inside the function is reported."""
        result = run_check({"call": "add", "args": [1, "x"], "expected": 1}, self.CODE)
        self.assertIn("TypeError", result.message)

    def test_value_that_is_not_json(self):
        """A value JSON cannot hold is shown with repr and fails."""
        code = "def make():\n    return object\n"
        result = run_check({"call": "make", "expected": "object"}, code)
        self.assertFalse(result.passed)
        self.assertIn("<class 'object'>", result.message)

    def test_printing_does_not_confuse_the_result(self):
        """What the player's code prints is not taken as the result."""
        code = 'print("HELLO")\ndef five():\n    print("5")\n    return 5\n'
        self.assertTrue(run_check({"call": "five", "expected": 5}, code).passed)


class TestValuesMatch(unittest.TestCase):
    """Check how returned values are compared."""

    def test_bools_do_not_match_numbers(self):
        """True does not match 1."""
        self.assertFalse(values_match(True, 1))
        self.assertTrue(values_match(False, False))

    def test_nested_lists_and_dicts(self):
        """Lists and dictionaries match item by item."""
        self.assertTrue(values_match({"a": [1, 2.0]}, {"a": [1, 2]}))
        self.assertFalse(values_match({"a": [1]}, {"a": [1, 2]}))
        self.assertFalse(values_match({"a": 1}, {"b": 1}))

    def test_text(self):
        """Text matches only the same text."""
        self.assertTrue(values_match("OK", "OK"))
        self.assertFalse(values_match("OK", "ok"))


class TestRequireAndForbid(unittest.TestCase):
    """Check the AST rules."""

    def test_require_passes_when_used(self):
        """Code with a while loop passes require While."""
        code = "n = 0\nwhile n < 3:\n    n += 1\n"
        result = run_check({"require": ["While"]}, code)
        self.assertTrue(result.passed)
        self.assertEqual(result.name, "uses a while loop")

    def test_require_fails_with_friendly_name(self):
        """Code without a for loop fails require For, naming it kindly."""
        result = run_check({"require": ["For"]}, "print(1)")
        self.assertFalse(result.passed)
        self.assertIn("must use a for loop", result.message)

    def test_forbid(self):
        """forbid fails when the construct is used and passes when it is not."""
        code = "for n in range(3):\n    print(n)\n"
        self.assertFalse(run_check({"forbid": ["For"]}, code).passed)
        self.assertTrue(run_check({"forbid": ["While"]}, code).passed)

    def test_unreadable_code(self):
        """Code that is not Python fails, saying why."""
        result = run_check({"require": ["Call"]}, "print(SNEK ONLINE)")
        self.assertFalse(result.passed)
        self.assertIn("Python cannot read your code", result.message)

    def test_unknown_construct_shows_its_own_name(self):
        """A node type with no friendly name is shown as it is."""
        self.assertEqual(construct_name("Starred"), "Starred")


class TestRequireComment(unittest.TestCase):
    """Check the comment test."""

    def test_comment_passes(self):
        """A # comment passes."""
        self.assertTrue(run_check({"require_comment": True}, '# Say hi\nprint("HI")').passed)

    def test_hash_inside_a_string_is_not_a_comment(self):
        """A # inside a string does not count."""
        result = run_check({"require_comment": True}, 'print("# not a comment")')
        self.assertFalse(result.passed)

    def test_count_comments_on_bad_code(self):
        """Code that cannot be split into tokens gives None."""
        self.assertIsNone(count_comments('print("unclosed'))


class TestTestKind(unittest.TestCase):
    """Check how the kind of a test is found."""

    def test_kind_is_the_known_key(self):
        """The known key decides the kind; other keys like stdin are ignored."""
        self.assertEqual(test_kind({"stdin": "x", "expected_stdout": "y"}), "expected_stdout")

    def test_unknown_kind(self):
        """A table without a known key has no kind and fails when run."""
        self.assertIsNone(test_kind({"stdin": "x"}))
        self.assertFalse(run_check({"stdin": "x"}, "print(1)").passed)


if __name__ == "__main__":
    unittest.main()
