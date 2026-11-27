"""Tests for render/level_clear.py and render/boss_screen.py."""

import re
import unittest

from render.boss_screen import (
    BAR_BLOCKS,
    SCREEN_WIDTH,
    boss_name,
    boss_screen,
    header,
    health_bar,
    hp_drain_frames,
    load_boss_art,
    timer_text,
)
from render.level_clear import level_clear_frames, load_clear_art


def without_colours(text):
    """Return `text` without ANSI escape codes, as the player would read it."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestLevelClear(unittest.TestCase):
    """Check the level-clear animation."""

    def setUp(self):
        """Load the real icons."""
        self.art = load_clear_art()

    def frames(self, stars, power_up="status", coins=10):
        """Return the frames for level 1-1 with `stars` stars."""
        return level_clear_frames("1-1", "Hello, Terminal", 100, stars, coins, power_up, self.art)

    def test_stars_then_coins_then_the_power_up(self):
        """3 stars: 0, 1, 2, 3 stars and the green bar (5), 6 coin steps, one frame per letter."""
        self.assertEqual(len(self.frames(3)), 5 + 6 + len("status"))
        self.assertEqual(len(self.frames(1, power_up="", coins=0)), 3)

    def test_every_frame_has_the_same_height(self):
        """Frames are drawn over each other, so they must be the same size."""
        heights = []
        for frame in self.frames(3):
            heights.append(len(frame.split("\n")))
        self.assertEqual(len(set(heights)), 1)

    def test_the_last_frame_has_the_banner_score_coins_and_the_new_command(self):
        """No XP anywhere."""
        text = without_colours(self.frames(2)[-1])
        self.assertTrue(text.startswith("LEVEL 1-1 CLEARED · HELLO, TERMINAL"))
        self.assertIn("SCORE 100 %", text)
        self.assertIn("COINS +10", text)
        self.assertIn("NEW COMMAND: status", text)
        self.assertNotIn("XP", text)

    def test_coins_count_up_and_never_go_down(self):
        """The counter rises to the total."""
        shown = []
        for frame in self.frames(1, power_up=""):
            line = [row for row in without_colours(frame).split("\n") if row.startswith("COINS +")][0]
            shown.append(int(line.split("+")[1]))
        self.assertEqual(shown, sorted(shown))
        self.assertEqual(shown[0], 0)
        self.assertEqual(shown[-1], 10)

    def test_the_power_up_is_revealed_one_letter_at_a_time(self):
        """NEW COMMAND: s, st, sta ..."""
        texts = [without_colours(frame) for frame in self.frames(1)]
        for letters in range(1, len("status") + 1):
            self.assertIn("NEW COMMAND: " + "status"[:letters], texts[-(len("status") - letters + 1)])

    def test_no_new_command_line_without_a_power_up(self):
        """A level without a power-up has none."""
        self.assertNotIn("NEW COMMAND", "".join(self.frames(1, power_up="")))

    def test_no_coin_frames_without_coins(self):
        """Nothing to count."""
        self.assertEqual(len(self.frames(1, power_up="", coins=0)), 3)

    def test_the_picture_changes_as_stars_fill_in(self):
        """Each star frame differs from the one before it."""
        frames = self.frames(3)
        for index in range(1, 4):
            self.assertNotEqual(frames[index], frames[index - 1])

    def test_last_frame_has_a_green_bar(self):
        """The final frame's bar is Green (76, 217, 100)."""
        picture_first_line = self.frames(2)[-1].split("\n")[1]
        self.assertIn("76;217;100", picture_first_line)


class TestBossScreen(unittest.TestCase):
    """Check the parts of the boss screen."""

    def setUp(self):
        """Load the real boss art."""
        self.art = load_boss_art("boss-placeholder")

    def test_boss_name(self):
        """boss-1 is shown as BOSS 1."""
        self.assertEqual(boss_name("boss-1"), "BOSS 1")

    def test_header_has_the_tries_at_the_right(self):
        """The tries end at the right edge of the 80-column screen."""
        line = header("boss-1", "The Corrupted Bootloader", 2)
        self.assertTrue(line.startswith("BOSS 1 · THE CORRUPTED BOOTLOADER"))
        self.assertTrue(line.endswith("TRIES 2 of 3"))
        self.assertEqual(len(line), SCREEN_WIDTH)

    def test_health_bar_matches_the_plan(self):
        """5 of 10 failing fills half the 20 blocks, as in the plan's mock-up."""
        self.assertEqual(health_bar(5, 10),
                         "BOSS HP [██████████░░░░░░░░░░]  5 of 10 hidden tests still failing")

    def test_health_bar_ends(self):
        """Full health fills every block; no health fills none."""
        self.assertIn("█" * BAR_BLOCKS, health_bar(3, 3))
        self.assertIn("░" * BAR_BLOCKS, health_bar(0, 3))
        self.assertIn("1 of 1 hidden test still", health_bar(1, 1))

    def test_timer(self):
        """Seconds are shown as minutes and seconds, never below zero."""
        self.assertEqual(timer_text(462), "TIME 07:42")
        self.assertEqual(timer_text(-5), "TIME 00:00")

    def test_whole_screen(self):
        """Header, 8 picture lines (16 pixels), the bar and the timer."""
        text = boss_screen("boss-1", "The Test Boss", 1, 3, 2, 90, self.art)
        lines = text.split("\n")
        self.assertEqual(len(lines), 1 + 8 + 2)
        self.assertIn("TRIES 2 of 3", lines[0])
        self.assertIn("1 of 3 hidden tests", lines[-2])
        self.assertEqual(lines[-1], "TIME 01:30")

    def test_drain_goes_one_test_at_a_time(self):
        """From 3 to 1 failing: frames at 3, 2 and 1."""
        frames = hp_drain_frames("boss-1", "Boss", 3, 1, 3, 2, 60, self.art)
        self.assertEqual(len(frames), 3)
        self.assertIn("3 of 3", frames[0])
        self.assertIn("1 of 3", frames[-1])

    def test_no_drain_gives_one_frame(self):
        """If the health did not go down, there is one frame."""
        self.assertEqual(len(hp_drain_frames("boss-1", "Boss", 2, 2, 3, 2, 60, self.art)), 1)


if __name__ == "__main__":
    unittest.main()
