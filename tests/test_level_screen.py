"""Tests for engine/level_screen.py, the text shown when a level starts."""

import unittest

from engine.level_pack import Level, Wave
from engine.level_screen import CODE_INDENT, cutscene_lines, intro_text, title_card, wave_lines


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

    def test_fill_in_wave_shows_its_starter(self):
        """A fill-in wave shows the code with blanks."""
        wave = make_intro_level().waves[0]
        self.assertEqual(wave_lines(wave, 1), [
            "WAVE 1 · FILL-IN · wave1.py",
            "Fill in the blank.",
            CODE_INDENT + "print(___)",
        ])

    def test_build_wave_shows_only_its_brief(self):
        """A build wave has no code to show, only the brief."""
        wave = make_intro_level().waves[1]
        self.assertEqual(wave_lines(wave, 2), ["WAVE 2 · BUILD · wave2.py", "Print", "three lines."])

    def test_predict_wave_shows_the_code_to_read(self):
        """A predict wave shows the code, but never the answer."""
        wave = make_intro_level().waves[2]
        lines = wave_lines(wave, 3)
        self.assertIn(CODE_INDENT + 'print("ONE")', lines)
        self.assertNotIn("ONE", lines)


class TestIntroText(unittest.TestCase):
    """Check the whole intro, in order."""

    def test_parts_come_in_order(self):
        """Title, then cutscene, then tips, then the three waves."""
        text = intro_text(make_intro_level())
        positions = []
        for part in ["LEVEL 1-1", "The lab is dark.", "TIPS", "  • Tip one.",
                     "WAVE 1", "WAVE 2", "WAVE 3"]:
            self.assertIn(part, text)
            positions.append(text.index(part))
        self.assertEqual(positions, sorted(positions))

    def test_wrong_solutions_and_answers_are_never_shown(self):
        """The intro must not give away the answers."""
        text = intro_text(make_intro_level())
        self.assertNotIn("print(OK)", text)
        self.assertNotIn('print("OK")', text)
        self.assertNotIn("TWO", text)


if __name__ == "__main__":
    unittest.main()
