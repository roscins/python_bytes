"""A level is cleared only when EVERY wave is passed. Stars still come from the score."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.results_screen import reward_lines
from engine.rewards import apply_submission
from engine.submission import grade_text
from tests.helpers import make_full_level, make_levels


def submit_wave(state, level, number, text):
    """Grade `text` as wave `number` of `level`, apply it to the state, return the Reward."""
    submission = grade_text(level.waves[number - 1], number, text)
    return apply_submission(state, level, [submission])


GOOD_FILL_IN = 'print("a")'
GOOD_BUILD = '# say a\nprint("a")'
GOOD_PREDICT = "a"


class TestClearOnlyWhenEveryWaveIsPassed(unittest.TestCase):
    """The rule, in the rewards."""

    def setUp(self):
        """A three-wave level and a game."""
        self.level = make_full_level()
        self.state = GameState([self.level])

    def test_two_perfect_waves_score_85_but_do_not_clear(self):
        """85 % is 2 stars, but the third wave is still open."""
        submit_wave(self.state, self.level, 1, GOOD_FILL_IN)
        reward = submit_wave(self.state, self.level, 2, GOOD_BUILD)
        self.assertGreaterEqual(reward.best_score, 85)
        self.assertEqual(reward.stars, 2)
        self.assertFalse(reward.cleared_now)
        self.assertEqual(self.state.cleared, [])

    def test_the_last_wave_clears_the_level(self):
        """All three passed: cleared, 3 stars."""
        submit_wave(self.state, self.level, 1, GOOD_FILL_IN)
        submit_wave(self.state, self.level, 2, GOOD_BUILD)
        reward = submit_wave(self.state, self.level, 3, GOOD_PREDICT)
        self.assertTrue(reward.cleared_now)
        self.assertEqual(reward.stars, 3)
        self.assertEqual(self.state.cleared, ["1-1"])

    def test_waves_passed_in_any_order_clear_at_the_end(self):
        """Going back to an earlier wave is allowed."""
        submit_wave(self.state, self.level, 3, GOOD_PREDICT)
        submit_wave(self.state, self.level, 1, GOOD_FILL_IN)
        self.assertEqual(self.state.cleared, [])
        submit_wave(self.state, self.level, 2, GOOD_BUILD)
        self.assertEqual(self.state.cleared, ["1-1"])

    def test_a_wave_with_most_tests_passed_is_not_passed(self):
        """Passing one of two tests is not enough, even with a high score elsewhere."""
        submit_wave(self.state, self.level, 1, GOOD_FILL_IN)
        submit_wave(self.state, self.level, 3, GOOD_PREDICT)
        submit_wave(self.state, self.level, 2, 'print("b")')            # wrong output
        self.assertEqual(self.state.cleared, [])
        reward = submit_wave(self.state, self.level, 2, 'print("a")')   # right output, no comment
        self.assertTrue(reward.cleared_now)
        self.assertEqual(self.state.cleared, ["1-1"])

    def test_cleared_stays_cleared(self):
        """A bad replay does not take it away, and clearing is reported only once."""
        submit_wave(self.state, self.level, 1, GOOD_FILL_IN)
        submit_wave(self.state, self.level, 2, GOOD_BUILD)
        first = submit_wave(self.state, self.level, 3, GOOD_PREDICT)
        again = submit_wave(self.state, self.level, 1, "print(")
        self.assertTrue(first.cleared_now)
        self.assertFalse(again.cleared_now)
        self.assertEqual(self.state.cleared, ["1-1"])

    def test_a_one_wave_level_clears_with_that_wave(self):
        """Levels with one wave (and bosses) clear when it passes."""
        levels = make_levels("1-1")
        levels[0].waves[0].tests = [{"expected_stdout": "OK\n"}]
        state = GameState(levels)
        reward = submit_wave(state, levels[0], 1, 'print("OK")')
        self.assertTrue(reward.cleared_now)


class TestMessages(unittest.TestCase):
    """What the player reads."""

    def test_results_say_every_wave_must_pass(self):
        """Not cleared yet: the line says what is missing."""
        level = make_full_level()
        state = GameState([level])
        reward = submit_wave(state, level, 1, GOOD_FILL_IN)
        text = "\n".join(reward_lines(level, reward))
        self.assertIn("Pass every wave to clear this level.", text)
        self.assertNotIn("70 %", text)

    def test_locked_level_message_names_the_level_before(self):
        """The next level asks for every wave of the one before."""
        state = GameState(make_levels("1-1", "1-2"))
        text = handle_line(state, "play 1-2")
        self.assertEqual(text, "Level 1-2 is locked. Pass every wave of 1-1 first.")


if __name__ == "__main__":
    unittest.main()
