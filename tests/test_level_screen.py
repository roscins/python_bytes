"""Tests for engine/level_screen.py, the text shown when a level starts."""

import unittest

from engine.level_pack import Level, Wave
from engine.level_screen import (
    CODE_INDENT,
    cutscene_lines,
    intro_text,
    numbered_code,
    title_card,
    wave_screen_text,
)


def make_intro_level():
    """Return a level with one wave of each kind, for checking the intro."""
    fill_in = Wave("fill-in", "Fill in the blank.", starter="print(___)",
                   reference='print("OK")', wrong="print(OK)")
    build = Wave("build", "Print\nthree lines.", reference='print("A")', wrong="print(A)")
    predict = Wave("debug", "What does this print?", mode="predict",
                   code='print("ONE")', answer="ONE", wrong="TWO")
    cutscene = '\n# >> The lab is dark.\nprint("SYSTEM CHECK")\n\n# >> Snek: "HELLO."\n'
    return Level("1-1", "Hello, Terminal", 1, ["print()", "strings"], "status",
                 cutscene, ["Tip one.", "Tip two."], [fill_in, build, predict])


class TestParts(unittest.TestCase):
    """Check each part of the intro on its own."""

    def test_title_card(self):
        """The title card shows the id and the title in capitals."""
        self.assertEqual(title_card(make_intro_level()), "LEVEL 1-1 · HELLO, TERMINAL")

    def test_story_lines_lose_their_marker_and_code_is_indented(self):
        """# >> lines become plain story text; code lines are indented."""
        lines = cutscene_lines(make_intro_level().cutscene)
        self.assertEqual(lines, [
            "The lab is dark.",
            CODE_INDENT + 'print("SYSTEM CHECK")',
            'Snek: "HELLO."',
        ])

    def test_numbered_code(self):
        """Code lines get a number and a bar; the plain look uses |."""
        self.assertEqual(numbered_code("a\n  b\n"), ["  1 │ a", "  2 │   b"])
        self.assertEqual(numbered_code("a\n", plain=True), ["  1 | a"])

    def test_numbered_code_in_colour_keeps_the_text(self):
        """Colour only adds codes: without them the lines are the same."""
        import re

        plain_lines = numbered_code("if x:\n    y = 1\n")
        coloured = numbered_code("if x:\n    y = 1\n", color=True)
        self.assertIn("\x1b[35mif\x1b[0m", coloured[0])
        self.assertEqual([re.sub(r"\x1b\[[0-9;]*m", "", line) for line in coloured], plain_lines)

    def test_wave_screen_colours_the_code_when_asked(self):
        """The player's code and the code to read are highlighted."""
        screen = wave_screen_text(make_intro_level(), 3, "print(1)\n", color=True)
        self.assertIn("\x1b[96mprint\x1b[0m", screen)

    def test_wave_screen_shows_the_task_and_the_code_so_far(self):
        """A fill-in wave shows its brief, then its code with the blank."""
        level = make_intro_level()
        text = wave_screen_text(level, 1, "print(___)\n")
        self.assertIn("WAVE 1 of 3 · FILL-IN", text)
        self.assertIn("Fill in the blank.", text)
        self.assertIn("YOUR CODE:", text)
        self.assertIn("  1 │ print(___)", text)

    def test_empty_build_wave_invites_the_first_line(self):
        """No code yet: a short hint instead of an empty list."""
        text = wave_screen_text(make_intro_level(), 2, "")
        self.assertIn("WAVE 2 of 3 · BUILD", text)
        self.assertIn("Print", text)
        self.assertIn("(nothing yet: type your first line)", text)

    def test_predict_wave_shows_the_code_to_read_but_never_the_answer(self):
        """The player types what the program prints."""
        text = wave_screen_text(make_intro_level(), 3, "")
        self.assertIn(CODE_INDENT + 'print("ONE")', text)
        self.assertIn("YOUR ANSWER", text)
        self.assertNotIn("TWO", text)

    def test_the_commands_are_in_the_footer_not_on_the_wave_screen(self):
        """The footer names them, once."""
        self.assertNotIn(":submit", wave_screen_text(make_intro_level(), 2, ""))


class TestIntroText(unittest.TestCase):
    """Check the whole intro, in order."""

    def test_parts_come_in_order(self):
        """Title, then cutscene, then tips, then how many waves."""
        text = intro_text(make_intro_level())
        positions = []
        for part in ["LEVEL 1-1", "The lab is dark.", "TIPS", "  • Tip one.", "3 waves"]:
            self.assertIn(part, text)
            positions.append(text.index(part))
        self.assertEqual(positions, sorted(positions))

    def test_wrong_solutions_and_answers_are_never_shown(self):
        """The intro must not give away the answers."""
        text = intro_text(make_intro_level())
        self.assertNotIn("print(OK)", text)
        self.assertNotIn('print("OK")', text)
        self.assertNotIn("TWO", text)

    def test_no_file_names_any_more(self):
        """The code is typed in the game."""
        self.assertNotIn("wave1.py", intro_text(make_intro_level()))


if __name__ == "__main__":
    unittest.main()
