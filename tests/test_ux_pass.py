"""The UX pass (docs/design/ux-pass.md): screens, footer, fill-in, commands, results, startup."""

import unittest
from pathlib import Path

from engine.commands import handle_line
from engine.fill import fill_next_blank
from engine.footer import footer_for
from engine.game_state import GameState
from engine.level_pack import load_levels
from engine.loop import show_answer
from engine.screens import PAGE_BREAK, split_screens, wrap_text
from engine.terminal import enable_line_editing
from engine.tutorial import SCREENS, tutorial_text
from render.ansi import strip_ansi
from render.compare_view import compare_lines
from render.screen import size_problem
from tests.helpers import make_full_level, type_code

LEVELS_FOLDER = Path(__file__).parent.parent / "levels"


def text_of(answer):
    """Return an answer as one text (an animation is a list of frames)."""
    if isinstance(answer, list):
        return "\n".join(answer)
    return answer


class GameCase(unittest.TestCase):
    """A plain game on the real levels, all of World 1 open."""

    def setUp(self):
        """Clear every level but keep nothing else."""
        self.state = GameState(load_levels(LEVELS_FOLDER))
        self.state.plain = True
        self.state.cleared = ["1-1", "1-2", "1-3", "1-4", "1-5"]
        self.addCleanup(self.state.close)

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer as text."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return text_of(answer)

    def code(self):
        """Return the code of the wave being played."""
        level = self.state.find_level(self.state.current_level)
        return self.state.wave_text(level, self.state.current_wave)


class TestScreens(unittest.TestCase):
    """One screen at a time."""

    def show(self, typed):
        """Show three screens, typing the lines in `typed` at the pauses."""
        written = []
        lines = iter(typed)
        left = show_answer(PAGE_BREAK.join(["one", "two", "three"]), written.append,
                           lambda seconds: None, lambda prompt: next(lines), 80)
        return written, left

    def test_enter_goes_through_them(self):
        """Every screen, nothing left over."""
        self.assertEqual(self.show(["", ""]), (["one", "two", "three"], None))

    def test_s_skips_to_the_last(self):
        """The middle one is not shown."""
        self.assertEqual(self.show(["s"]), (["one", "three"], None))

    def test_another_line_is_not_lost(self):
        """It is handed back to be handled."""
        self.assertEqual(self.show(["map"]), (["one", "three"], "map"))

    def test_wrapping_leaves_code_alone(self):
        """Sentences wrap; indented code does not."""
        wrapped = wrap_text("word " * 30 + "\n    x = " + "1" * 100, 40).split("\n")
        self.assertTrue(all(len(line) <= 40 for line in wrapped[:-1]))
        self.assertEqual(len(wrapped[-1]), 108)

    def test_indented_sentences_wrap_too(self):
        """Messages inside the results, and the frames of a boss fight."""
        message = "      " + "word " * 30 + "end."
        self.assertTrue(all(len(line) <= 60 for line in wrap_text(message, 60).split("\n")))
        written = []
        show_answer(["word " * 30], written.append, lambda seconds: None, lambda prompt: "", 40)
        self.assertTrue(all(len(line) <= 40 for line in written[0].split("\n")))

    def test_tutorial(self):
        """Four short screens, and the first says how to skip."""
        self.assertEqual(len(split_screens(tutorial_text())), 4)
        self.assertIn("skip", SCREENS[0])
        words = sum(len(screen.split()) for screen in SCREENS)
        self.assertLess(words, 200)          # about a minute of reading


class TestStartup(unittest.TestCase):
    """Window size and line editing."""

    def test_size_problem_says_exactly_what_is_missing(self):
        """Both directions."""
        message = size_problem(70, 20)
        self.assertIn("80 x 24; yours is 70 x 20", message)
        self.assertIn("10 columns wider and 4 rows taller", message)
        self.assertEqual(size_problem(80, 24), "")

    def test_line_editing_is_used_where_python_has_it(self):
        """Without readline (Windows) the game goes on."""
        def missing(name):
            raise ImportError(name)

        self.assertFalse(enable_line_editing(missing))
        self.assertTrue(enable_line_editing(lambda name: None))


class TestFooterAndGoal(GameCase):
    """The mode, the keys and the goal."""

    def test_modes(self):
        """MAP, FILL, CODE, ANSWER and BOSS."""
        self.assertTrue(footer_for(self.state).startswith("MAP"))
        self.type_lines("play 1-1")
        self.assertTrue(footer_for(self.state).startswith("FILL"))
        self.type_lines(":wave 2")
        self.assertTrue(footer_for(self.state).startswith("CODE"))
        self.type_lines(":wave 3")
        self.assertTrue(footer_for(self.state).startswith("ANSWER"))
        self.type_lines(":play boss-1")
        self.assertIn(":run is free", footer_for(self.state))
        for line in [":play 1-1", ":wave 2", ":play boss-1"]:
            self.type_lines(line)
            self.assertLessEqual(len(footer_for(self.state)), 80)

    def test_every_wave_has_a_short_goal_shown_in_a_box(self):
        """At most 60 characters, above the code."""
        self.state.cleared = [level.id for level in self.state.levels]
        for level in self.state.levels:
            for number, wave in enumerate(level.waves, 1):
                with self.subTest(level=level.id, wave=number):
                    self.assertLessEqual(len(wave.goal), 60)
                    self.type_lines(":play " + level.id)
                    screen = self.type_lines(f":wave {number}") if not level.boss else self.type_lines(":show")
                    self.assertIn("GOAL", screen)
                    self.assertIn(wave.goal, screen)

    def test_intro_is_story_then_tips_then_wave(self):
        """Three screens."""
        screens = split_screens(self.type_lines("play 1-2"))
        self.assertEqual(len(screens), 3)
        self.assertIn("LEVEL 1-2", screens[0])
        self.assertTrue(screens[1].startswith("TIPS"))
        self.assertTrue(screens[2].startswith("WAVE 1 of 3"))


class TestFillIn(GameCase):
    """Only the blank is asked for."""

    def test_the_blank_is_marked(self):
        """^^^ sits under it."""
        lines = split_screens(self.type_lines("play 1-1"))[-1].split("\n")
        index = [i for i, line in enumerate(lines) if "print(___)" in line][0]
        self.assertEqual(lines[index + 1].index("^"), lines[index].index("___"))

    def test_typing_the_content_fills_it(self):
        """No second line appears."""
        self.type_lines("play 1-1", '"SNEK ONLINE"')
        self.assertEqual(self.code(), 'print("SNEK ONLINE")\n')

    def test_typing_the_whole_line_is_understood(self):
        """A habit, not an error."""
        self.type_lines("play 1-1", 'print("SNEK ONLINE")')
        self.assertEqual(self.code(), 'print("SNEK ONLINE")\n')

    def test_two_blanks_one_at_a_time(self):
        """1-3 has two."""
        answer = self.type_lines("play 1-3", "//")
        self.assertIn("Blank 2 of 2", answer)
        self.type_lines("%")
        self.assertIn("hours = total_minutes // 60", self.code())
        self.assertIn("minutes = total_minutes % 60", self.code())

    def test_after_the_last_blank_more_lines_are_not_added(self):
        """And :undo brings the blank back."""
        self.type_lines("play 1-1", '"A"')
        self.assertIn("All blanks are filled", self.type_lines('"B"'))
        self.type_lines(":undo")
        self.assertIn("___", self.code())

    def test_after_clear_the_player_writes_freely(self):
        """Even when the first line looks like the starter."""
        self.type_lines("play 1-1", ":clear", 'print("one")', 'print("two")')
        self.assertEqual(self.code(), 'print("one")\nprint("two")\n')

    def test_filling_a_whole_line_pattern(self):
        """The indentation stays."""
        self.assertEqual(fill_next_blank("    x = ___\n", "x = 5"), "    x = 5\n")


class TestCommandsWithoutColon(GameCase):
    """submit, hint and typos."""

    def setUp(self):
        """Start on the build wave of 1-1."""
        super().setUp()
        self.type_lines("play 1-1", ":wave 2", ":clear")

    def test_submit_and_hint(self):
        """They are commands."""
        self.type_lines('print("x")')
        self.assertIn("RESULTS", self.type_lines("submit"))
        self.assertIn("HINT 1 of 3", self.type_lines("hint"))
        self.assertNotIn("submit", self.code())

    def test_a_name_of_the_players_own_wins_with_one_note(self):
        """The line is code, and the note points to :submit."""
        answer = self.type_lines("submit = 1", "submit")
        self.assertEqual(answer, "Your code has a name submit, so this line is code. To hand in, type :submit.")
        self.assertEqual(self.code(), "submit = 1\nsubmit\n")

    def test_the_note_also_for_a_hint_name_in_code_python_cannot_read_yet(self):
        """A half-typed block does not hide the name."""
        self.assertIn("name hint", self.type_lines("hint = 2", "print(", "hint"))

    def test_indented_submit_is_code(self):
        """Only the exact line is a command."""
        self.type_lines("    submit")
        self.assertEqual(self.code(), "    submit\n")

    def test_typos_are_suggested(self):
        """In a wave and at the map."""
        self.assertIn("Did you mean :submit?", self.type_lines("sumbit"))
        self.assertIn("Did you mean :submit?", self.type_lines(":sumbit"))
        self.assertIn("Did you mean submit?", self.type_lines(":map", "sumbit"))
        self.assertIn("Did you mean play 1-1?", self.type_lines("play 1.1"))
        self.assertIn("Your next level: play boss-1", self.type_lines("play"))

    def test_a_typo_does_not_fill_a_blank(self):
        """The blank stays."""
        self.assertIn("Not filled in", self.type_lines("play 1-3", ":wave 1", "sumbit"))
        self.assertIn("___", self.code())


class TestResultsThatTeach(GameCase):
    """Differences and syntax errors."""

    def test_first_difference_is_marked(self):
        """The ^ is under the first different character."""
        lines = compare_lines("SNEK ONLINE", "Snek online")
        self.assertEqual(lines[2].index("^"), lines[1].index("Snek") + 1)
        self.assertIn("line 1, character 2", lines[-1])

    def test_missing_line_and_long_lines(self):
        """Shorter output, and lines too long for two columns."""
        self.assertIn("(no line)", "\n".join(compare_lines("a\nb", "a")))
        stacked = compare_lines("x" * 50 + "a", "x" * 50 + "b")
        self.assertTrue(stacked[0].startswith("expected:"))

    def test_results_show_both_outputs(self):
        """In the game."""
        self.type_lines("play 1-1", '"Snek online"')
        answer = self.type_lines(":submit")
        self.assertIn("EXPECTED", answer)
        self.assertIn("YOURS", answer)
        self.assertIn("GOAL: Make Snek print SNEK ONLINE.", answer)

    def test_syntax_error_points_at_the_column(self):
        """Once, with a ^ under the quote that is never closed."""
        self.type_lines("play 1-1", ":wave 2", ":clear", 'print("a)')
        lines = self.type_lines(":submit").split("\n")
        source = [i for i, line in enumerate(lines) if 'print("a)' in line][0]
        self.assertEqual(lines[source + 1].index("^"), lines[source].index('"'))
        self.assertEqual("\n".join(lines).count("a quote is missing"), 1)

    def test_next_level_after_a_clear(self):
        """Not just "type map"."""
        level = make_full_level()
        second = make_full_level()
        second.id = "1-2"
        state = GameState([level, second])
        state.plain = True
        handle_line(state, "play 1-1")
        answer = ""
        for text in ['print("a")', '# a\nprint("a")', "a"]:
            type_code(state, text)
            answer = text_of(handle_line(state, ":submit"))
        self.assertIn("Next: play 1-2", answer)


if __name__ == "__main__":
    unittest.main()
