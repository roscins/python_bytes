"""Tests for engine/friendly.py: Python's errors as game messages.

The error texts below are what Python really prints (copied from the runner),
so the table is tested against the real thing.
"""

import unittest

from engine.friendly import (
    format_friendly,
    friendly_error,
    friendly_message,
    friendly_timeout,
    line_number_of,
)

SYNTAX_QUOTE = '''  File "main.py", line 2
    print("hello)
          ^
SyntaxError: unterminated string literal (detected at line 2)
'''
SYNTAX_PAREN = '''  File "main.py", line 1
    print("a"
         ^
SyntaxError: '(' was never closed
'''
SYNTAX_COLON = '''  File "main.py", line 1
    if x == 1
             ^
SyntaxError: expected ':'
'''
INDENT_BLOCK = '''  File "main.py", line 2
    print(1)
    ^^^^^
IndentationError: expected an indented block after 'if' statement on line 1
'''
INDENT_UNEXPECTED = '''  File "main.py", line 2
    y = 2
IndentationError: unexpected indent
'''
SYNTAX_COMMA = '''  File "main.py", line 1
    print("a" "b" 1)
          ^^^^^^^^^
SyntaxError: invalid syntax. Perhaps you forgot a comma?
'''
SYNTAX_NUMBER = '''  File "main.py", line 1
    x = 3x
        ^
SyntaxError: invalid decimal literal
'''
SYNTAX_ASSIGN = '''  File "main.py", line 1
    5 = x
    ^
SyntaxError: cannot assign to literal here. Maybe you meant '==' instead of '='?
'''
NAME_ERROR = '''Traceback (most recent call last):
  File "main.py", line 3, in <module>
    print(y)
          ^
NameError: name 'y' is not defined
'''
TYPE_PLUS = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    1 + "a"
    ~~^~~~~
TypeError: unsupported operand type(s) for +: 'int' and 'str'
'''
TYPE_CONCAT = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    "a" + 1
    ~~~~^~~
TypeError: can only concatenate str (not "int") to str
'''
ZERO = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    x = 5 / 0
        ~~^~~
ZeroDivisionError: division by zero
'''
INDEX = '''Traceback (most recent call last):
  File "main.py", line 2, in <module>
    print(x[5])
          ~^^^
IndexError: string index out of range
'''
VALUE = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    int("abc")
    ~~~^^^^^^^^
ValueError: invalid literal for int() with base 10: 'abc'
'''
ATTRIBUTE = '''Traceback (most recent call last):
  File "main.py", line 2, in <module>
    x.foo()
    ^^^^^
AttributeError: 'str' object has no attribute 'foo'
'''
EOF_ERROR = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    input()
    ~~~~~^^
EOFError: EOF when reading a line
'''
UNKNOWN = '''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    raise RuntimeError("boom")
RuntimeError: boom
'''
RECURSION = '''Traceback (most recent call last):
  File "main.py", line 3, in <module>
    f()
  File "main.py", line 2, in f
    f()
  [Previous line repeated 996 more times]
RecursionError: maximum recursion depth exceeded
'''


class TestLineNumbers(unittest.TestCase):
    """Which line of the player's code is meant."""

    def test_syntax_error_line(self):
        """From the File line."""
        self.assertEqual(line_number_of(SYNTAX_QUOTE), 2)

    def test_the_last_frame_of_a_traceback_is_used(self):
        """In a recursion the innermost frame is the last one."""
        self.assertEqual(line_number_of(RECURSION), 2)

    def test_repl_lines_are_found_too(self):
        """The quick console names its code <repl>."""
        text = 'Traceback (most recent call last):\n  File "<repl>", line 1, in <module>\nNameError: name \'q\' is not defined\n'
        self.assertEqual(line_number_of(text), 1)

    def test_no_line(self):
        """A bare error line has none."""
        self.assertIsNone(line_number_of("NameError: name 'q' is not defined"))

    def test_lines_of_other_files_are_ignored(self):
        """Only the player's file counts, not a library."""
        text = 'Traceback:\n  File "/usr/lib/python3/json/__init__.py", line 9, in load\nValueError: x\n'
        self.assertIsNone(line_number_of(text))


class TestHeadlines(unittest.TestCase):
    """Each row of the table, with the line number."""

    def check(self, text, line, *phrases):
        """The headline starts with the line and holds every phrase."""
        error = friendly_error(text)
        self.assertEqual(error.line, line, error.headline)
        for phrase in phrases:
            self.assertIn(phrase, error.headline)
        return error

    def test_missing_quote(self):
        """The example from the design."""
        error = self.check(SYNTAX_QUOTE, 2, "Snek tripped on line 2", "quote is missing")
        self.assertEqual(error.headline, "Snek tripped on line 2: a quote is missing.")

    def test_bracket_never_closed(self):
        """Names the bracket."""
        self.check(SYNTAX_PAREN, 1, "bracket", "(")

    def test_missing_colon(self):
        """if without a colon."""
        self.check(SYNTAX_COLON, 1, "colon")

    def test_block_needs_indentation(self):
        """The line after an if must be indented."""
        self.check(INDENT_BLOCK, 2, "indented", "4 spaces")

    def test_unexpected_indent(self):
        """Indented too far."""
        self.check(INDENT_UNEXPECTED, 2, "indented too far")

    def test_missing_comma(self):
        """Python's own hint, in plain words."""
        self.check(SYNTAX_COMMA, 1, "comma")

    def test_number_with_letters(self):
        """3x."""
        self.check(SYNTAX_NUMBER, 1, "number")

    def test_assigning_to_a_literal(self):
        """5 = x."""
        self.check(SYNTAX_ASSIGN, 1, "left of =")

    def test_name_error(self):
        """Says which name, and what to check."""
        error = self.check(NAME_ERROR, 3, "I do not know the name y")
        self.assertIn("spelled", error.headline)

    def test_adding_a_number_to_text(self):
        """The most common mistake of week one."""
        self.check(TYPE_CONCAT, 1, "str()")

    def test_mixing_types_with_plus(self):
        """int and str."""
        self.check(TYPE_PLUS, 1, "int", "str")

    def test_division_by_zero(self):
        """Plain words."""
        self.check(ZERO, 1, "divided by zero")

    def test_position_that_does_not_exist(self):
        """IndexError."""
        self.check(INDEX, 2, "position")

    def test_text_that_is_not_a_number(self):
        """int("abc")."""
        self.check(VALUE, 1, "whole number")

    def test_missing_attribute(self):
        """Names the type and the attribute."""
        self.check(ATTRIBUTE, 2, "str", ".foo")

    def test_asked_for_input_with_none_given(self):
        """EOFError from input()."""
        self.check(EOF_ERROR, 1, "input")

    def test_endless_recursion(self):
        """RecursionError."""
        self.check(RECURSION, 2, "calls itself")

    def test_unknown_error_still_gets_a_headline(self):
        """The real error is part of it."""
        error = self.check(UNKNOWN, 1, "RuntimeError", "boom")
        self.assertTrue(error.headline.startswith("Snek tripped on line 1"))

    def test_without_a_line_number(self):
        """No 'on line': just Snek tripped."""
        error = friendly_error("ZeroDivisionError: division by zero")
        self.assertTrue(error.headline.startswith("Snek tripped: "))
        self.assertIsNone(error.line)

    def test_the_real_error_is_kept_for_the_detail(self):
        """The last line of the traceback."""
        self.assertEqual(friendly_error(NAME_ERROR).detail, "NameError: name 'y' is not defined")

    def test_empty_text(self):
        """Nothing to explain."""
        error = friendly_error("")
        self.assertEqual(error.detail, "")


class TestTimeout(unittest.TestCase):
    """A program that runs too long."""

    def test_timeout_headline(self):
        """Mentions the seconds and the endless loop."""
        error = friendly_timeout(2)
        self.assertIn("2 seconds", error.headline)
        self.assertIn("never ends", error.headline)


class TestFormat(unittest.TestCase):
    """The text the player sees."""

    SOURCE = 'x = 1\nprint("hello)\n'

    def test_plain_has_headline_source_line_and_real_error(self):
        """No colour codes; the real error is marked as Python's words."""
        text = format_friendly(friendly_error(SYNTAX_QUOTE), self.SOURCE, plain=True, color=False)
        self.assertIn("Snek tripped on line 2: a quote is missing.", text)
        self.assertIn('  2 | print("hello)', text)
        self.assertIn("Python says: SyntaxError: unterminated string literal", text)
        self.assertNotIn("\x1b[", text)

    def test_colour_makes_the_real_error_grey(self):
        """Dim grey (SGR 90) around the real error."""
        text = format_friendly(friendly_error(SYNTAX_QUOTE), self.SOURCE, plain=False, color=True)
        self.assertIn("\x1b[90m", text)
        self.assertIn("SyntaxError: unterminated string literal", text)

    def test_no_source_line_when_the_line_is_out_of_range(self):
        """A line number beyond the code is simply not shown."""
        error = friendly_error(NAME_ERROR)
        text = format_friendly(error, "x = 1\n", plain=True, color=False)
        self.assertIn("Snek tripped on line 3", text)
        self.assertNotIn("  3 |", text)


class TestFriendlyMessage(unittest.TestCase):
    """The grader's messages are rewritten the same way."""

    def test_grader_message_with_a_line(self):
        """'Your program stopped with an error on line 2: ...' becomes a friendly headline."""
        message = "Your program stopped with an error on line 2: NameError: name 'y' is not defined"
        text = friendly_message(message)
        self.assertIn("Snek tripped on line 2: I do not know the name y", text)
        self.assertIn("NameError: name 'y' is not defined", text)

    def test_grader_message_without_a_line(self):
        """The older form still works."""
        text = friendly_message("Your program stopped with an error: ZeroDivisionError: division by zero")
        self.assertIn("Snek tripped: you divided by zero", text)

    def test_other_messages_are_unchanged(self):
        """Only error messages are rewritten."""
        self.assertEqual(friendly_message("Expected this output: x"), "Expected this output: x")

    def test_time_limit_message_is_rewritten(self):
        """The grader's timeout text."""
        text = friendly_message("Your program ran for more than 2 seconds. Is there a loop that never ends?")
        self.assertIn("Snek", text)
        self.assertIn("2 seconds", text)


if __name__ == "__main__":
    unittest.main()
