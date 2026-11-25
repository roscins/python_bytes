"""Tests for engine/scoring.py, engine/progress.py, engine/rewards.py and engine/hud.py."""

import unittest

from engine.game_state import GameState
from engine.hud import hud_text, map_status
from engine.level_pack import Wave
from engine.progress import LevelProgress, progress_from_dict
from engine.rewards import apply_submission
from engine.scoring import (
    STARTING_COINS,
    combo_multiplier,
    is_unlocked,
    level_score,
    star_text,
    stars_for,
    xp_for,
)
from engine.submission import WaveSubmission
from grader.checks import CheckResult
from grader.wave_grader import WaveResult
from tests.helpers import make_level, make_levels

THREE_WAVES = [Wave("fill-in", "a"), Wave("build", "b"), Wave("debug", "c")]


def result_with(passed, total, quality=None):
    """Return a WaveResult with `passed` of `total` checks passed.

    `quality` is the number of the 4 quality rules passed, or None.
    """
    checks = []
    for index in range(total):
        checks.append(CheckResult(index < passed, "check"))
    rules = None
    if quality is not None:
        rules = []
        for index in range(4):
            rules.append(CheckResult(index < quality, "rule"))
    return WaveResult(checks, rules)


class TestLevelScore(unittest.TestCase):
    """Check the weighted level score."""

    def test_perfect_level_scores_100(self):
        """Every wave and full quality give 100 %."""
        self.assertEqual(level_score(THREE_WAVES, [1.0, 1.0, 1.0], 1.0), 100)

    def test_weights(self):
        """Fill-in 20, build 50, debug 15, quality 15."""
        self.assertEqual(level_score(THREE_WAVES, [1.0, 0.0, 0.0], 0.0), 20)
        self.assertEqual(level_score(THREE_WAVES, [0.0, 1.0, 0.0], 0.0), 50)
        self.assertEqual(level_score(THREE_WAVES, [0.0, 0.0, 1.0], 0.0), 15)
        self.assertEqual(level_score(THREE_WAVES, [0.0, 0.0, 0.0], 1.0), 15)

    def test_half_a_build_wave(self):
        """Half the build tests and 3 of 4 quality rules: 20 + 25 + 15 + 11.25."""
        self.assertEqual(level_score(THREE_WAVES, [1.0, 0.5, 1.0], 0.75), 71)

    def test_other_waves_are_scaled_to_100(self):
        """A level with only a build wave and quality still reaches 100 %."""
        self.assertEqual(level_score([Wave("build", "b")], [1.0], 1.0), 100)
        self.assertEqual(level_score([Wave("build", "b")], [1.0], 0.0), 77)

    def test_no_waves(self):
        """A level with nothing to score scores 0."""
        self.assertEqual(level_score([], [], None), 0)


class TestStarsXpAndCombo(unittest.TestCase):
    """Check stars, XP and the combo multiplier."""

    def test_stars(self):
        """1 at 70, 2 at 85, 3 only at 100 without hints."""
        self.assertEqual(stars_for(69, False), 0)
        self.assertEqual(stars_for(70, False), 1)
        self.assertEqual(stars_for(85, False), 2)
        self.assertEqual(stars_for(100, False), 3)
        self.assertEqual(stars_for(100, True), 2)

    def test_star_text(self):
        """Stars are drawn as filled and empty stars."""
        self.assertEqual(star_text(2), "★★☆")

    def test_xp_only_for_improving(self):
        """XP is 10 per point above the old best, times the multiplier."""
        self.assertEqual(xp_for(0, 85, 1.0), 850)
        self.assertEqual(xp_for(85, 100, 2.0), 300)
        self.assertEqual(xp_for(100, 100, 2.0), 0)
        self.assertEqual(xp_for(90, 80, 1.0), 0)

    def test_combo_multiplier(self):
        """×1 below 3, ×1.5 from 3, ×2 from 5."""
        self.assertEqual(combo_multiplier(2), 1.0)
        self.assertEqual(combo_multiplier(3), 1.5)
        self.assertEqual(combo_multiplier(4), 1.5)
        self.assertEqual(combo_multiplier(5), 2.0)


class TestUnlocking(unittest.TestCase):
    """Check the 70 % unlock rule."""

    def test_first_level_is_open(self):
        """The first level is always open."""
        levels = make_levels("1-1", "1-2")
        self.assertTrue(is_unlocked(levels, [], levels[0]))

    def test_next_level_opens_when_the_one_before_is_cleared(self):
        """1-2 opens when 1-1 is cleared, and 1-3 waits for 1-2."""
        levels = make_levels("1-1", "1-2", "1-3")
        self.assertFalse(is_unlocked(levels, [], levels[1]))
        self.assertTrue(is_unlocked(levels, ["1-1"], levels[1]))
        self.assertFalse(is_unlocked(levels, ["1-1"], levels[2]))

    def test_unknown_level_is_locked(self):
        """A level that is not in the list is never open."""
        self.assertFalse(is_unlocked(make_levels("1-1"), [], make_level("9-9")))


class TestProgress(unittest.TestCase):
    """Check LevelProgress and reading it back from a save."""

    def test_perfect_needs_full_quality_in_build_waves(self):
        """A build wave with every test passed but quality 3/4 is not perfect yet."""
        progress = LevelProgress(1)
        progress.wave_best = [1.0]
        progress.best_quality = 0.75
        self.assertFalse(progress.wave_is_perfect(1, Wave("build", "b")))
        self.assertTrue(progress.wave_is_perfect(1, Wave("fill-in", "f")))
        progress.best_quality = 1.0
        self.assertTrue(progress.wave_is_perfect(1, Wave("build", "b")))

    def test_round_trip(self):
        """to_dict and progress_from_dict give back the same progress."""
        progress = LevelProgress(3)
        progress.wave_best = [1.0, 0.5, 0.0]
        progress.stars = 1
        loaded = progress_from_dict(progress.to_dict(), 3)
        self.assertEqual(loaded.to_dict(), progress.to_dict())

    def test_wrong_types_are_rejected(self):
        """A progress dict with the wrong types raises ValueError."""
        good = LevelProgress(1).to_dict()
        for key, value in [("wave_best", "1.0"), ("wave_best", [True]), ("stars", None),
                           ("quality_rewarded", 1)]:
            broken = dict(good)
            broken[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    progress_from_dict(broken, 1)
        with self.assertRaises(ValueError):
            progress_from_dict([], 1)


class TestApplySubmission(unittest.TestCase):
    """Check how a graded submit changes the player's progress."""

    def setUp(self):
        """A three-wave level 1-1, followed by 1-2."""
        self.levels = make_levels("1-1", "1-2")
        self.level = self.levels[0]
        self.level.waves = list(THREE_WAVES)
        self.state = GameState(self.levels)

    def submit(self, results):
        """Apply one submit; `results` has one WaveResult (or None) per wave."""
        submissions = []
        for index in range(len(results)):
            submissions.append(WaveSubmission(index + 1, self.level.waves[index],
                                              f"wave{index + 1}", results[index]))
        return apply_submission(self.state, self.level, submissions)

    def test_perfect_first_submit(self):
        """All three waves first try: 100 %, 3 stars, combo 3 (XP ×1.5), coins."""
        reward = self.submit([result_with(2, 2), result_with(2, 2, 4), result_with(1, 1)])
        self.assertEqual(reward.best_score, 100)
        self.assertEqual(reward.stars, 3)
        self.assertEqual(reward.combo, 3)
        self.assertEqual(reward.multiplier, 1.5)
        self.assertEqual(reward.xp_gained, 1500)
        self.assertEqual(reward.coins_gained, 3 * 5 + 5)
        self.assertTrue(reward.cleared_now)
        self.assertEqual(reward.opened_level.id, "1-2")
        self.assertEqual(self.state.xp, 1500)
        self.assertEqual(self.state.coins, STARTING_COINS + 20)
        self.assertEqual(self.state.cleared, ["1-1"])

    def test_best_attempt_counts(self):
        """A worse second try does not lower the best share or score."""
        self.submit([result_with(2, 2), result_with(2, 2, 4), None])
        reward = self.submit([None, result_with(0, 2, 0), None])
        self.assertEqual(self.state.progress["1-1"].wave_best[1], 1.0)
        self.assertEqual(reward.best_score, 85)
        self.assertEqual(reward.xp_gained, 0)

    def test_combo_resets_on_a_failed_wave(self):
        """A failed wave sets the combo back to 0."""
        self.submit([result_with(2, 2), result_with(1, 2, 4), None])
        self.assertEqual(self.state.combo, 0)

    def test_second_try_pass_earns_no_coins_and_resets_combo(self):
        """Passing a wave after a failed try is not a first try."""
        self.submit([result_with(0, 2), None, None])
        reward = self.submit([result_with(2, 2), None, None])
        self.assertEqual(reward.coins_gained, 0)
        self.assertEqual(reward.combo, 0)

    def test_quality_coins_only_once(self):
        """Full quality gives 5 coins the first time only."""
        first = self.submit([None, result_with(0, 2, 4), None])
        second = self.submit([None, result_with(0, 2, 4), None])
        self.assertEqual(first.coins_gained, 5)
        self.assertEqual(second.coins_gained, 0)

    def test_hints_cap_the_stars(self):
        """A perfect level after buying a hint earns 2 stars."""
        self.state.progress_for(self.level).hints_bought = [1, 0, 0]
        reward = self.submit([result_with(2, 2), result_with(2, 2, 4), result_with(1, 1)])
        self.assertEqual(reward.stars, 2)

    def test_not_started_waves_score_zero(self):
        """Only the fill-in wave: 20 %, not cleared."""
        reward = self.submit([result_with(2, 2), None, None])
        self.assertEqual(reward.best_score, 20)
        self.assertFalse(reward.cleared_now)
        self.assertIsNone(reward.opened_level)

    def test_clearing_the_last_level_opens_nothing(self):
        """The last level on the map has no next level."""
        self.level = self.levels[1]
        self.level.waves = list(THREE_WAVES)
        reward = self.submit([result_with(2, 2), result_with(2, 2, 4), result_with(1, 1)])
        self.assertTrue(reward.cleared_now)
        self.assertIsNone(reward.opened_level)


class TestHud(unittest.TestCase):
    """Check the HUD text and map status built from the game state."""

    def test_hud_counts_the_world_stars(self):
        """Stars are counted out of 3 per level in the world."""
        levels = make_levels("1-1", "1-2")
        state = GameState(levels)
        state.xp = 50
        state.progress_for(levels[0]).stars = 3
        self.assertEqual(hud_text(state, levels), f"XP 50   ★ 3/6   COINS {STARTING_COINS}")

    def test_map_status_locks(self):
        """Only the first level is open in a new game."""
        levels = make_levels("1-1", "1-2")
        status = map_status(GameState(levels), levels)
        self.assertEqual(status.locked, [False, True])
        self.assertEqual(status.stars, [0, 0])


if __name__ == "__main__":
    unittest.main()
