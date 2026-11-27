"""The calc power-up: Python's order of evaluation, step by step."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.powerups.calc import do_calc
from tests.helpers import make_full_level

DESIGN_EXAMPLE = """CALC
(74 - 2) * 3 + 10 // 4
 ~~~~~~
72 * 3 + 10 // 4
~~~~~~
216 + 10 // 4
      ~~~~~~~
216 + 2
~~~~~~~
218"""


def last_line(expression):
    """Return the last line calc shows for `expression`."""
    return do_calc(GameState(), expression).splitlines()[-1]


class TestSteps(unittest.TestCase):
    """What calc shows."""

    def test_the_design_example(self):
        """Brackets, then the left product, then the right side, then the sum."""
        self.assertEqual(do_calc(GameState(), "(74 - 2) * 3 + 10 // 4"), DESIGN_EXAMPLE)

    def test_results_match_python(self):
        """The last step is what Python gives."""
        for expression in ["2 ** 3 ** 2", "-2 ** 2", "(-2) ** 2", "7 % -3", "10 / 4", "2 - (3 - 4)",
                           "int('7') + float('0.5')", "str(12) + ' Wh'", "round(10 / 3, 2)", "-(-5)",
                           "0.1 + 0.2", "'é' + 'a' * 3", "+5 - -5", "int(-7.9) // 2"]:
            with self.subTest(expression=expression):
                self.assertEqual(last_line(expression), repr(eval(expression)))

    def test_negative_values_keep_their_brackets(self):
        """A negative result raised to a power is shown in brackets."""
        self.assertIn("(-2) ** 2", do_calc(GameState(), "(1 - 3) ** 2"))

    def test_errors_show_where_python_stops(self):
        """Dividing by zero and mixing text with numbers."""
        self.assertIn("ZeroDivisionError", last_line("1 + 2 / (3 - 3)"))
        self.assertIn("TypeError", last_line("'a' + 1"))
        self.assertIn("NameError", last_line("price * 2"))

    def test_huge_and_unknown_things_are_refused(self):
        """No hang, no eval, no crash."""
        for expression in ["9 ** 9 ** 9", "'a' * 10 ** 9", "round(5, -10 ** 9)", "__import__('os')",
                           "open('x')", "[1, 2]", "'%999999999d' % 1", "(-8) ** (1 / 3)",
                           "1 if 2 else 3", "x.real", "round(1.5, ndigits=1)", "1 +", "1 + " * 30 + "1"]:
            with self.subTest(expression=expression):
                answer = do_calc(GameState(), expression)
                self.assertFalse(answer.startswith("CALC\n") and "stops" not in answer, answer)


class TestNotOrdinaryNumbers(unittest.TestCase):
    """inf and nan cannot be written back into a line, so calc stops there."""

    def test_inf_and_nan_do_not_loop(self):
        """Each of these once could, or still could, go round for ever."""
        for expression in ["float('nan')", "float('inf')", "float('-inf') + 1", "1e999 - 1e999",
                           "1e308 * 10"]:
            with self.subTest(expression=expression):
                self.assertIn("inf or nan", do_calc(GameState(), expression))


class TestVariables(unittest.TestCase):
    """calc with the variables of the console or the wave."""

    def setUp(self):
        """A game where calc has been earned."""
        level = make_full_level()
        level.power_up = "calc"
        self.state = GameState([level])
        self.state.cleared.append(level.id)
        self.addCleanup(self.state.close)

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return answer

    def test_console_variables(self):
        """The name is replaced by its value as one step."""
        answer = self.type_lines("price = 5", "calc price * 2")
        self.assertEqual(answer, "CALC\nprice * 2\n~~~~~\n5 * 2\n~~~~~\n10")

    def test_wave_variables(self):
        """In a wave the code is run for its variables."""
        answer = self.type_lines("play 1-1", ":clear", "size = -3", ":calc size ** 2")
        self.assertIn("(-3) ** 2", answer)
        self.assertTrue(answer.endswith("\n9"))

    def test_locked_while_a_prediction_is_open(self):
        """calc works out code, so it is refused at the map too."""
        answer = self.type_lines("play 1-1", ":wave 3", ":map", "calc 1 + 1")
        self.assertIn("prediction is open", answer)


if __name__ == "__main__":
    unittest.main()
