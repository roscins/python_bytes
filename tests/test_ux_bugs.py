"""Two bugs found by the World 1 audit (docs/design/ux-pass.md)."""

import unittest
from pathlib import Path

from engine.commands import handle_line
from engine.game_state import GameState
from engine.level_pack import load_levels
from tests.helpers import make_full_level, type_code

LEVELS_FOLDER = Path(__file__).parent.parent / "levels"


def text_of(answer):
    """Return an answer as one text (an animation is a list of frames)."""
    if isinstance(answer, list):
        return "\n".join(answer)
    return answer


class TestBossShowsItsCode(unittest.TestCase):
    """B1: the program to repair is on the screen when the fight starts."""

    def test_play_boss_1_shows_the_scrambled_program(self):
        """Every line of the starter is there."""
        state = GameState(load_levels(LEVELS_FOLDER))
        state.plain = True
        state.cleared = ["1-1", "1-2", "1-3", "1-4", "1-5"]
        answer = text_of(handle_line(state, "play boss-1"))
        for line in state.find_level("boss-1").waves[0].starter.strip().splitlines():
            self.assertIn(line, answer)


class TestClearedOnlyWhenCleared(unittest.TestCase):
    """B2: no CLEARED banner while a wave is still missing."""

    def test_banner_comes_only_with_the_last_wave(self):
        """Stars appear after wave 2, but the level is not cleared yet."""
        level = make_full_level()
        state = GameState([level])
        state.plain = True
        handle_line(state, "play 1-1")
        answers = []
        for text in ['print("a")', '# a\nprint("a")', "a"]:
            type_code(state, text)
            answers.append(text_of(handle_line(state, ":submit")))
        self.assertNotIn("CLEARED ·", answers[0])
        self.assertNotIn("CLEARED ·", answers[1])
        self.assertIn("CLEARED ·", answers[2])


if __name__ == "__main__":
    unittest.main()
