"""Tests for render/highlight.py: colouring Python code with the tokenize module."""

import re
import unittest

from render.highlight import highlight_lines

RESET = "\x1b[0m"
KEYWORD = "\x1b[35m"
BUILTIN = "\x1b[96m"
STRING = "\x1b[36m"
NUMBER = "\x1b[95m"
COMMENT = "\x1b[90m"
BLANK = "\x1b[7m"


def strip_colours(text):
    """Return `text` without colour codes."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def painted(style, text):
    """Return `text` the way the highlighter paints it in `style`."""
    return style + text + RESET


class TestColours(unittest.TestCase):
    """Each kind of token has its colour."""

    def one_line(self, code):
        """Highlight one line of code and return the result."""
        lines = highlight_lines(code, color=True)
        self.assertEqual(len(lines), 1)
        return lines[0]

    def test_keyword(self):
        """if, True and friends."""
        self.assertIn(painted(KEYWORD, "if"), self.one_line("if x:"))
        self.assertIn(painted(KEYWORD, "True"), self.one_line("x = True"))

    def test_builtin_name(self):
        """print, len, int."""
        self.assertIn(painted(BUILTIN, "print"), self.one_line("print(x)"))

    def test_string(self):
        """Quotes included."""
        self.assertIn(painted(STRING, '"hello"'), self.one_line('x = "hello"'))

    def test_number(self):
        """Whole numbers and decimals."""
        self.assertIn(painted(NUMBER, "42"), self.one_line("x = 42"))
        self.assertIn(painted(NUMBER, "3.14"), self.one_line("x = 3.14"))

    def test_comment(self):
        """From the # to the end of the line."""
        self.assertIn(painted(COMMENT, "# a note"), self.one_line("x = 1  # a note"))

    def test_the_blank_of_a_fill_in_is_inverse(self):
        """___ stands out."""
        self.assertIn(painted(BLANK, "___"), self.one_line("print(___)"))

    def test_plain_names_and_operators_are_not_coloured(self):
        """x, =, +."""
        line = self.one_line("x = y + 1")
        self.assertTrue(line.startswith("x = y + "))

    def test_fstring_is_a_string(self):
        """f"..." in one colour; the name inside is still a name."""
        line = self.one_line('print(f"hi {name}")')
        self.assertIn(STRING, line)
        self.assertEqual(strip_colours(line), 'print(f"hi {name}")')


class TestShape(unittest.TestCase):
    """Whatever the code, the text stays the same and the lines stay lines."""

    SAMPLES = [
        "",
        "x = 1\n",
        'print("a")\nprint("b")\n',
        "if x:\n    y = 1\nelse:\n    y = 2\n",
        's = """abc\ndef"""\nt = 1\n',
        'print("VOICE',
        'x = 1\nprint("a\ny = 2\n',
        "if x:\n    y = 1\n  z = 2\n",
        "x = (1 +\n",
        "x = 'é ü 😀'  # unicode\n",
        "if x:\n\ty = 1\n",
        "def f(a, b=2):\n    return a + b\n",
        "print(___)\n",
    ]

    def test_the_text_is_unchanged_without_the_colour_codes(self):
        """Colouring only adds codes."""
        for code in self.SAMPLES:
            with self.subTest(code=code):
                lines = highlight_lines(code, color=True)
                self.assertEqual([strip_colours(line) for line in lines], code.splitlines())

    def test_no_colour_returns_the_plain_lines(self):
        """color=False is the plain mode."""
        for code in self.SAMPLES:
            with self.subTest(code=code):
                self.assertEqual(highlight_lines(code, color=False), code.splitlines())

    def test_every_colour_is_closed_on_its_own_line(self):
        """A line never leaves a colour open for the next line to inherit."""
        for code in self.SAMPLES:
            for line in highlight_lines(code, color=True):
                with self.subTest(line=line):
                    self.assertEqual(line.count("\x1b[0m"), len(re.findall(r"\x1b\[(?!0m)[0-9;]*m", line)))


class TestHalfTypedCode(unittest.TestCase):
    """The player types line by line, so code is often unfinished."""

    def test_an_unclosed_string_is_coloured_to_the_end_of_the_line(self):
        """print("VOICE: the print and the string both get colours."""
        line = highlight_lines('print("VOICE', color=True)[0]
        self.assertIn(painted(BUILTIN, "print"), line)
        self.assertIn(painted(STRING, '"VOICE'), line)

    def test_lines_after_the_broken_one_are_still_coloured(self):
        """A later keyword is not left plain because an earlier line is broken."""
        lines = highlight_lines('print("a\nif x:\n    pass\n', color=True)
        self.assertIn(painted(KEYWORD, "if"), lines[1])
        self.assertIn(painted(KEYWORD, "pass"), lines[2])

    def test_lines_before_the_broken_one_keep_their_colours(self):
        """The tokens already read are used."""
        lines = highlight_lines('x = 1\nprint("a\n', color=True)
        self.assertIn(painted(NUMBER, "1"), lines[0])

    def test_unfinished_bracket(self):
        """x = (1 + : the tokens before the end are coloured."""
        line = highlight_lines("x = (1 +\n", color=True)[0]
        self.assertIn(painted(NUMBER, "1"), line)

    def test_a_triple_quoted_string_over_several_lines(self):
        """Each of its lines is a string, not just the first."""
        lines = highlight_lines('s = """abc\ndef\nghi"""\nt = 1\n', color=True)
        self.assertIn(painted(STRING, '"""abc'), lines[0])
        self.assertEqual(lines[1], painted(STRING, "def"))
        self.assertIn(painted(STRING, 'ghi"""'), lines[2])
        self.assertIn(painted(NUMBER, "1"), lines[3])

    def test_bad_indentation_does_not_stop_the_colouring(self):
        """An unindent that matches nothing is an error for Python, not for the highlighter."""
        lines = highlight_lines("if x:\n    y = 1\n  z = 2\n", color=True)
        self.assertIn(painted(KEYWORD, "if"), lines[0])
        self.assertIn(painted(NUMBER, "2"), lines[2])


if __name__ == "__main__":
    unittest.main()
