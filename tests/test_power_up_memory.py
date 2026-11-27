"""The memory power-up: names, the values they point to, and shared boxes."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from render.memory_view import REUSE_NOTE, memory_view
from tests.helpers import make_full_level


def variable(name, number, type_name="int", shown="5", text=None):
    """Return a variable description as the console worker makes it."""
    return {"name": name, "id": number, "type": type_name, "repr": shown, "text": text}


class TestDrawing(unittest.TestCase):
    """memory_view on made-up variables."""

    def test_one_box_per_object(self):
        """Two names of one object share a box; another object gets its own."""
        view = memory_view([variable("power", 1, shown="9"), variable("name", 2, "list", "[1]"),
                            variable("twin", 2, "list", "[1]")])
        self.assertEqual(view, "MEMORY\nNAMES          VALUES\npower -------> [ 9 ]  int\n"
                               "name  --+----> [ [1] ]  list\ntwin  --+")

    def test_note_for_shared_small_ints_and_short_strings(self):
        """The note appears for values Python reuses."""
        for kind, shown, text in [("int", "5", None), ("str", "'ok'", "ok")]:
            with self.subTest(kind=kind):
                view = memory_view([variable("a", 1, kind, shown, text), variable("b", 1, kind, shown, text)])
                self.assertIn(REUSE_NOTE, view)

    def test_no_note_for_lists_big_ints_or_unshared_values(self):
        """Sharing those is the player's own doing, and one name is not sharing."""
        cases = [[variable("a", 1, "list", "[]"), variable("b", 1, "list", "[]")],
                 [variable("a", 1, shown="100000"), variable("b", 1, shown="100000")],
                 [variable("a", 1)]]
        for case in cases:
            self.assertNotIn(REUSE_NOTE, memory_view(case))

    def test_long_names_and_values_fit(self):
        """Every line fits inside a panel, and many names are cut off."""
        many = [variable("a_very_long_variable_name_indeed" + str(n), n, "str", "'" + "x" * 150 + "'")
                for n in range(40)]
        view = memory_view(many)
        self.assertLessEqual(max(len(line) for line in view.splitlines()), 74)
        self.assertIn("10 more names", view)
        self.assertLessEqual(len(REUSE_NOTE), 76)


class TestInTheGame(unittest.TestCase):
    """memory typed in the game."""

    def setUp(self):
        """A game where memory has been earned."""
        level = make_full_level()
        level.power_up = "memory"
        self.state = GameState([level])
        self.state.cleared.append(level.id)
        self.addCleanup(self.state.close)

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return answer

    def test_no_variables_yet(self):
        """A friendly answer before anything is made."""
        self.assertIn("No variables yet", self.type_lines("memory"))

    def test_console_variables_at_the_map(self):
        """Binding one name to another shares the box."""
        view = self.type_lines("power = 5", "backup = power", "power = 9", "memory")
        self.assertIn("[ 9 ]  int", view)
        self.assertIn("[ 5 ]  int", view)
        shared = self.type_lines("twin = backup", "memory")
        self.assertIn("backup --+----> [ 5 ]", shared)
        self.assertIn(REUSE_NOTE, shared)

    def test_the_code_of_a_wave(self):
        """In a wave the typed code is run and drawn."""
        view = self.type_lines("play 1-1", ":clear", "size = 3", "label = 'hi'", ":memory")
        self.assertIn("size  -------> [ 3 ]  int", view)
        self.assertIn("label -------> [ 'hi' ]  str", view)

    def test_an_error_shows_memory_up_to_there(self):
        """What was made before the error is drawn."""
        view = self.type_lines("play 1-1", ":clear", "size = 3", "print(oops)", ":memory")
        self.assertIn("size", view)
        self.assertIn("at the moment your code stopped", view)

    def test_blank_endless_loop_and_exit(self):
        """No crash and no hang."""
        self.assertIn("blank", self.type_lines("play 1-1", ":memory"))
        self.assertIn("seconds", self.type_lines(":clear", "while True:", "    pass", ":memory"))
        self.assertIn("closed Python", self.type_lines(":clear", "raise SystemExit", ":memory"))

    def test_locked_while_a_prediction_is_open(self):
        """In another wave memory would run code, so it is refused."""
        answer = self.type_lines("play 1-1", ":wave 3", ":wave 1", ":memory")
        self.assertIn("prediction is open", answer)


if __name__ == "__main__":
    unittest.main()
