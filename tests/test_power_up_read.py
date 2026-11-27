"""The shared part of the power-ups (earning, routing, refusals) and the read tool."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.level_pack import load_levels
from render.read_view import read_view
from tests.helpers import make_full_level

SNEK_VIEW = """READ
char     S  N  E  K
index    0  1  2  3
back    -4 -3 -2 -1
[1:3]       ^  ^
gives  'NE'     len = 4"""


class PowerUpCase(unittest.TestCase):
    """A game on a small level that gives read."""

    def setUp(self):
        """Make the game; read is not earned yet."""
        self.level = make_full_level()
        self.level.power_up = "read"
        self.state = GameState([self.level])
        self.addCleanup(self.state.close)

    def earn(self):
        """Mark the level as cleared."""
        self.state.cleared.append(self.level.id)

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return answer


class TestEarningAndRouting(PowerUpCase):
    """Who may use a power-up, and which lines are one."""

    def test_not_earned(self):
        """The answer says which level to clear."""
        self.assertEqual(self.type_lines('read "AB"'), "Clear 1-1 to earn read.")

    def test_earned(self):
        """At the map without a colon."""
        self.earn()
        self.assertIn("len = 2", self.type_lines('read "AB"'))

    def test_inside_a_wave_with_a_colon(self):
        """:read works while coding and does not become code."""
        self.earn()
        self.assertIn("len = 2", self.type_lines("play 1-1", ':read "AB"'))
        self.assertNotIn("read", self.state.wave_text(self.level, 1))

    def test_a_variable_called_read_is_still_python(self):
        """read = 5 assigns, even before the power-up is earned."""
        for earned in [False, True]:
            with self.subTest(earned=earned):
                self.assertEqual(self.type_lines("read = 5"), "")
                self.assertIn("6", self.type_lines("print(read + 1)"))
                self.earn()

    def test_refused_in_an_open_prediction(self):
        """Wave 3 asks for a prediction."""
        self.earn()
        answer = self.type_lines("play 1-1", ":wave 3", ':read "AB"')
        self.assertIn("will not help", answer)

    def test_read_still_works_at_the_map_during_the_lock(self):
        """read runs nothing, so the lock does not stop it."""
        self.earn()
        self.assertIn("len = 2", self.type_lines("play 1-1", ":wave 3", ":map", 'read "AB"'))

    def test_help_lists_only_earned_power_ups(self):
        """help grows when the level is cleared."""
        self.assertNotIn("Power-ups", self.type_lines("help"))
        self.earn()
        self.assertIn("Power-ups", self.type_lines("help"))


class TestRead(PowerUpCase):
    """What read shows."""

    def setUp(self):
        """Earn read."""
        super().setUp()
        self.earn()

    def test_the_drawing(self):
        """Indexes, negative indexes, marks and the result."""
        self.assertEqual(self.type_lines('read "SNEK" [1:3]'), SNEK_VIEW)

    def test_one_index_and_a_missing_index(self):
        """A single index is marked; one past the end is explained."""
        self.assertIn("gives  'K'", self.type_lines('read "SNEK"[-1]'))
        self.assertIn("IndexError", self.type_lines('read "SNEK"[9]'))

    def test_spaces_are_visible(self):
        """A dot, or _ in plain mode."""
        self.assertIn("·", read_view("a b", None, ""))
        self.assertIn("_", read_view("a b", None, "", plain=True))

    def test_long_text_wraps_and_fits_the_screen(self):
        """99 characters stay within the width of a panel."""
        view = read_view("x" * 99, slice(0, 99), "0:99]")
        self.assertEqual(view.count("char"), 5)
        self.assertLessEqual(max(len(line) for line in view.splitlines()), 74)
        self.assertIn("at most 99", self.type_lines('read "' + "x" * 100 + '"'))

    def test_a_console_variable(self):
        """At the map a quick console variable can be read."""
        self.assertIn("'bc'", self.type_lines('word = "abc"', "read word[1:]"))

    def test_a_variable_of_the_wave_is_read_without_running(self):
        """In a wave the text comes from the line that sets it."""
        answer = self.type_lines("play 1-1", ":clear", 'line = "07:30"', "print(oops)", ":read line [0:2]")
        self.assertIn("gives  '07'", answer)

    def test_unknown_names_and_bad_input(self):
        """A friendly answer, never a crash."""
        self.assertIn("cannot find", self.type_lines("read nothing"))
        for bad in ["read", "read 5", 'read "a" [x:]', 'read "a"[::0]', "read ((("]:
            with self.subTest(line=bad):
                self.assertIn("Usage", self.type_lines(bad))


class TestRealLevelNames(unittest.TestCase):
    """The curriculum rename."""

    def test_level_1_1_gives_explain(self):
        """status is now called explain."""
        for level in load_levels("levels"):
            if level.id == "1-1":
                self.assertEqual(level.power_up, "explain")


if __name__ == "__main__":
    unittest.main()
