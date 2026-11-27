"""Tests for the editor, its drawing, the quote rules and the error places."""

import unittest

from engine.editor import Editor
from engine.friendly import quote_sentence
from engine.wave_report import column_of, explain_error, run_report
from render.ansi import strip_ansi, visible_length
from render.editor_view import Mark, View, code_rows


def keys(editor, *pressed):
    """Press the keys one after the other."""
    for key in pressed:
        editor.press(key)


class TestEditor(unittest.TestCase):
    """Typing and moving."""

    def test_text_ends_with_a_newline_and_empty_is_empty(self):
        """The same shape as the saved buffers."""
        self.assertEqual(Editor("a\nb\n").text(), "a\nb\n")
        self.assertEqual(Editor("").text(), "")

    def test_enter_splits_and_backspace_joins(self):
        """Both ways."""
        editor = Editor("abcd")
        keys(editor, "right", "right", "enter")
        self.assertEqual(editor.lines, ["ab", "cd"])
        keys(editor, "backspace")
        self.assertEqual(editor.lines, ["abcd"])
        self.assertEqual(editor.column, 2)

    def test_delete_at_the_end_joins_the_next_line(self):
        """And in the middle deletes a character."""
        editor = Editor("ab\ncd")
        keys(editor, "end", "delete", "delete")
        self.assertEqual(editor.lines, ["abd"])

    def test_tab_types_four_spaces(self):
        """Never a tab character."""
        editor = Editor("x")
        keys(editor, "tab")
        self.assertEqual(editor.lines, ["    x"])

    def test_moving_stays_inside_the_text(self):
        """Also onto a shorter line."""
        editor = Editor("long line\nab")
        keys(editor, "end", "down", "down", "right")
        self.assertEqual((editor.row, editor.column), (1, 2))
        keys(editor, "home", "left")
        self.assertEqual((editor.row, editor.column), (0, 9))

    def test_typing_on_a_blank_replaces_it(self):
        """The whole blank, once."""
        editor = Editor("print(___)", blanks=True)
        self.assertTrue(editor.go_to_first_blank())
        keys(editor, '"', "a", '"')
        self.assertEqual(editor.lines, ['print("a")'])

    def test_backspace_and_delete_remove_a_blank_whole(self):
        """From inside it, or from just after it."""
        for pressed in (["delete"], ["backspace"], ["right", "right", "right", "backspace"]):
            editor = Editor("x[___]", blanks=True)
            editor.go_to_first_blank()
            keys(editor, *pressed)
            self.assertEqual(editor.lines, ["x[]"], pressed)

    def test_underscores_are_ordinary_outside_fill_in(self):
        """No blanks in other waves."""
        editor = Editor("___")
        keys(editor, "a")
        self.assertEqual(editor.lines, ["a___"])

    def test_undo_takes_back_one_line_of_work(self):
        """Typing on one line is one step; Enter is its own."""
        editor = Editor("")
        keys(editor, "a", "b", "enter", "c", "d")
        self.assertTrue(editor.undo())
        self.assertEqual(editor.lines, ["ab", ""])
        editor.undo()
        editor.undo()
        self.assertEqual(editor.lines, [""])
        self.assertFalse(editor.undo())


class TestCodeRows(unittest.TestCase):
    """Drawing the code."""

    def plain(self, lines, height=3, width=20, **options):
        """Return the rows without colours."""
        return [strip_ansi(row) for row in code_rows(lines, View(), height, width, **options)]

    def test_numbers_and_exact_height(self):
        """Empty rows fill the frame."""
        self.assertEqual(self.plain(["a"]), ["  1 │ a" + " " * 13, "", ""])

    def test_the_caret_goes_under_the_column(self):
        """Row 2 is the mark."""
        rows = self.plain(["ab", "cdef"], mark=Mark(1, 2))
        self.assertEqual(rows[2].index("^"), rows[1].index("e"))

    def test_a_long_line_scrolls_sideways_to_the_cursor(self):
        """With < to say there is more."""
        row = self.plain(["abcdefghijklmnopqrstuvwxyz"], cursor=(0, 25))[0]
        self.assertIn("<", row)
        self.assertIn("z", row)
        self.assertLessEqual(len(row), 20)

    def test_a_long_text_scrolls_down_to_the_cursor(self):
        """The last line can be seen."""
        rows = self.plain([str(number) for number in range(10)], cursor=(9, 0))
        self.assertTrue(rows[-1].strip().startswith("10 │"))

    def test_rows_never_exceed_the_width(self):
        """Colour codes take no room."""
        for row in code_rows(['print("' + "x" * 40 + '")'], View(), 2, 20, cursor=(0, 0)):
            self.assertLessEqual(visible_length(row), 20)


class TestQuoteSentences(unittest.TestCase):
    """The table of docs/design/code-editor.md."""

    def sentence(self, line, code=None, type_name="SyntaxError"):
        """Return the suggestion for `line`."""
        return quote_sentence(type_name, line, code or line)

    def test_the_table(self):
        """Words without quotes."""
        for line, words in [("print(SNEK ONLINE)", "SNEK ONLINE"),
                            ("print(HELLO, TECHNICIAN)", "HELLO, TECHNICIAN"),
                            ("print(SNEK)", "SNEK"), ("print(SNEK'S ONLINE)", "SNEK'S ONLINE")]:
            self.assertEqual(self.sentence(line), f'Text needs quotes: try print("{words}")')
        self.assertEqual(self.sentence("print SNEK"), 'Text needs quotes and brackets: try print("SNEK")')

    def test_a_typo_of_a_name_in_the_code(self):
        """Not quotes."""
        self.assertEqual(self.sentence("print(unti)", "unit = 1\nprint(unti)", "NameError"),
                         "I do not know the name unti. Did you mean unit?")

    def test_code_is_left_alone(self):
        """Operators, attributes, strings, and names the code creates."""
        for line in ["print(a + b)", "print(a - b)", "print(math.pi)", 'print("a" b)', "print(f(x))",
                     "print('a)", "total = x y", "print(12 3)"]:
            self.assertIsNone(self.sentence(line), line)
        self.assertIsNone(self.sentence("print(unit volts)", "unit = 1\nprint(unit volts)"))
        self.assertIsNone(self.sentence("print(SNEK)", type_name="TypeError"))


class TestErrorPlaces(unittest.TestCase):
    """Which line and column an error is at."""

    def test_a_syntax_error(self):
        """From compile()."""
        lines, mark = run_report("x = 1\nprint(SNEK ONLINE)\n")
        self.assertEqual((mark.row, mark.column), (1, 6))
        self.assertIn('Text needs quotes: try print("SNEK ONLINE")', lines)
        self.assertIn("SyntaxError", strip_ansi("\n".join(lines)))

    def test_a_crash_inside_an_indented_block(self):
        """The traceback hides the indentation; the column counts it."""
        code = "if True:\n    y = 1 + zzz\n"
        _, mark = run_report(code)
        self.assertEqual((mark.row, mark.column), (1, 12))

    def test_no_caret_means_no_column(self):
        """Only the line is marked."""
        self.assertIsNone(column_of('  File "main.py", line 1, in <module>\n    x\nNameError: x', "x"))

    def test_a_message_without_a_line(self):
        """No mark."""
        self.assertIsNone(explain_error("MemoryError", "x")[1])


if __name__ == "__main__":
    unittest.main()
