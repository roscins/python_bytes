"""While a predict wave is unanswered, nothing runs the player's code."""

import tempfile
import unittest
from pathlib import Path

from engine.commands import handle_line
from engine.game_state import GameState
from engine.predict_lock import locked_message, unanswered_predict
from engine.save_file import load_progress, save_progress
from tests.helpers import make_full_level


class TestPredictLock(unittest.TestCase):
    """The lock starts when the predict wave is seen and ends when it is passed."""

    def setUp(self):
        """A game on a small level whose third wave is a prediction of print("a")."""
        self.level = make_full_level()
        self.state = GameState([self.level])
        self.addCleanup(self.state.close)
        handle_line(self.state, "play 1-1")

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return answer

    def test_not_locked_before_the_predict_wave_is_seen(self):
        """On wave 1 code runs."""
        self.assertEqual(locked_message(self.state), "")
        self.assertIn("42", self.type_lines(":map", "print(6 * 7)"))

    def test_quick_console_is_locked_after_leaving_the_wave(self):
        """Seeing wave 3 and going to the map locks the console."""
        answer = self.type_lines(":wave 3", ":map", "print(6 * 7)")
        self.assertIn("prediction is open", answer)
        self.assertNotIn("42", answer)

    def test_run_in_another_wave_is_locked(self):
        """:run on wave 1 cannot be used to try the predict code."""
        answer = self.type_lines(":wave 3", ":wave 1", ":clear", "print(6 * 7)", ":run")
        self.assertIn("prediction is open", answer)

    def test_a_block_is_locked_too(self):
        """A for loop typed line by line does not run either."""
        answer = self.type_lines(":wave 3", ":map", "for i in range(2):", "    print(i)", "")
        self.assertIn("prediction is open", answer)

    def test_a_wrong_answer_keeps_the_lock(self):
        """One guess does not unlock running."""
        self.type_lines(":wave 3", "b", ":submit")
        self.assertIsNotNone(unanswered_predict(self.state))

    def test_the_right_answer_lifts_the_lock(self):
        """After passing, code runs again."""
        self.type_lines(":wave 3", "a", ":submit")
        self.assertEqual(locked_message(self.state), "")
        self.assertIn("42", self.type_lines(":map", "print(6 * 7)"))

    def test_a_mistyped_command_is_still_called_unknown(self):
        """The lock message is for code, not for typos."""
        self.assertIn("Unknown command", self.type_lines(":wave 3", ":map", "plya"))

    def test_the_lock_survives_a_restart(self):
        """The seen wave is in the save."""
        self.type_lines(":wave 3", ":map")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            save_progress(self.state, path)
            again = GameState([self.level])
            load_progress(again, path)
        self.assertIsNotNone(unanswered_predict(again))


if __name__ == "__main__":
    unittest.main()
