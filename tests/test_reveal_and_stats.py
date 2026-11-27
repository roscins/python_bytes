"""Revealing a predict answer after three wrong guesses, and the stats command."""

import tempfile
import unittest
from pathlib import Path

from engine.commands import handle_line
from engine.game_state import GameState
from engine.predict_lock import locked_message
from engine.progress import progress_from_dict
from engine.save_file import load_progress, save_progress
from tests.helpers import make_full_level, make_levels


def text_of(answer):
    """Return an answer as one text (a level-clear animation is a list of frames)."""
    if isinstance(answer, list):
        return answer[-1]
    return answer


class TestReveal(unittest.TestCase):
    """The third wrong guess shows the answer; the wave then counts at half."""

    def setUp(self):
        """Pass the two code waves of a small level, so wave 3 (print("a")) is next."""
        self.level = make_full_level()
        self.level.waves[2].explanation = "The program prints one letter."
        self.state = GameState([self.level])
        self.addCleanup(self.state.close)
        self.type_lines("play 1-1", ":clear", 'print("a")', ":submit",
                        ":clear", "# a", 'print("a")', ":submit")

    def type_lines(self, *lines):
        """Type lines into the game and return the last answer as text."""
        answer = ""
        for line in lines:
            answer = handle_line(self.state, line)
        return text_of(answer)

    def guess(self):
        """Hand in a wrong answer to the predict wave."""
        return self.type_lines(":clear", "zzz", ":submit")

    def test_two_wrong_guesses_reveal_nothing(self):
        """The player is told how many guesses are left, and code stays locked."""
        self.assertIn("left before Snek shows the output: 2", self.guess())
        second = self.guess()
        self.assertIn("output: 1", second)
        self.assertNotIn("The program prints:", second)
        self.assertTrue(locked_message(self.state))

    def test_third_guess_reveals_clears_and_unlocks(self):
        """Answer, explanation, half score, two stars at most, lock gone."""
        self.guess()
        self.guess()
        third = self.guess()
        self.assertIn("The program prints:\n    a", third)
        self.assertIn("The program prints one letter.", third)
        self.assertIn(self.level.id, self.state.cleared)
        progress = self.state.progress_for(self.level)
        self.assertEqual(progress.revealed, [False, False, True])
        self.assertEqual(progress.best_score, 92)   # 92.5, rounded to even
        self.assertEqual(progress.stars, 2)
        self.assertEqual(locked_message(self.state), "")

    def test_a_right_second_guess_scores_in_full(self):
        """Nothing is revealed and the score is 100."""
        self.guess()
        self.type_lines(":clear", "a", ":submit")
        progress = self.state.progress_for(self.level)
        self.assertEqual((progress.best_score, progress.revealed[2]), (100, False))

    def test_empty_answers_are_not_guesses(self):
        """Submitting nothing costs nothing."""
        for _ in range(4):
            self.type_lines(":clear", ":submit")
        self.assertEqual(self.state.progress_for(self.level).wave_attempts[2], 0)

    def test_guesses_and_reveal_survive_a_restart(self):
        """Both are in the save."""
        self.guess()
        self.guess()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            save_progress(self.state, path)
            again = GameState([self.level])
            load_progress(again, path)
            self.state = again
            self.assertIn("The program prints:", self.type_lines("play 1-1", ":clear", "zzz", ":submit"))
            save_progress(again, path)
            third = GameState([self.level])
            load_progress(third, path)
        self.assertTrue(third.progress_for(self.level).revealed[2])

    def test_old_saves_load_and_bad_values_do_not(self):
        """No "revealed" list means nothing was revealed."""
        data = self.state.progress_for(self.level).to_dict()
        del data["revealed"]
        self.assertEqual(progress_from_dict(data, 3).revealed, [False, False, False])
        data["revealed"] = "yes"
        with self.assertRaises(ValueError):
            progress_from_dict(data, 3)


class TestStats(unittest.TestCase):
    """The stats table."""

    def setUp(self):
        """Two worlds, one level of the first cleared with two stars."""
        levels = make_levels("1-1", "1-2", "2-1")
        levels[2].world = 2
        self.state = GameState(levels)
        self.addCleanup(self.state.close)
        self.state.cleared.append("1-1")
        self.state.progress_for(self.state.levels[0]).stars = 2

    def test_rows_and_total(self):
        """One row per world, then the total."""
        answer = handle_line(self.state, "stats").splitlines()
        self.assertEqual(answer[2], "1  Boot Sector              1/2        ★ 2/6")
        self.assertEqual(answer[3], "2  Sensor Fields            0/1        ★ 0/3")
        self.assertEqual(answer[4], "TOTAL                       1/3        ★ 2/9")

    def test_in_a_wave_it_keeps_the_wave(self):
        """:stats does not leave code mode or add code."""
        handle_line(self.state, "play 1-1")
        self.assertIn("STATS", handle_line(self.state, ":stats"))
        self.assertTrue(self.state.coding)

    def test_a_variable_called_stats_is_python(self):
        """stats = 5 assigns."""
        self.assertEqual(handle_line(self.state, "stats = 5"), "")


if __name__ == "__main__":
    unittest.main()
