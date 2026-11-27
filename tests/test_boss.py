"""Tests for boss fights: engine/boss.py, engine/boss_turns.py and boss levels in the loader."""

import unittest

from engine.boss import HIT, RESTART, WON, BossFight
from engine.commands import handle_line
from engine.game_state import GameState
from engine.level_pack import LevelError, load_level
from grader.checks import CheckResult
from grader.wave_grader import WaveResult
from tests.helpers import (
    VALID_BOSS_TOML,
    FakeClock,
    make_boss_level,
    make_levels,
    make_temporary_folder,
    type_code,
    write_level_pack,
)


def result_with(passed, total):
    """Return a WaveResult with `passed` of `total` checks passed."""
    checks = []
    for index in range(total):
        checks.append(CheckResult(index < passed, "check"))
    return WaveResult(checks)


class TestBossFight(unittest.TestCase):
    """Check lives, health and the timer of a fight."""

    def setUp(self):
        """A fight against the 3-test boss with a 600-second limit and a fake clock."""
        self.clock = FakeClock()
        self.fight = BossFight(make_boss_level(), clock=self.clock)

    def test_new_fight(self):
        """3 lives, full health and the whole time limit."""
        self.assertEqual(self.fight.lives, 3)
        self.assertEqual(self.fight.hp_left, 3)
        self.assertEqual(self.fight.hp_total, 3)
        self.assertEqual(self.fight.time_left(), 600)

    def test_hit_costs_a_life_and_drains_health(self):
        """Passing 1 of 3 tests: 2 still failing, one life lost."""
        self.assertEqual(self.fight.submit_result(result_with(1, 3)), HIT)
        self.assertEqual(self.fight.hp_left, 2)
        self.assertEqual(self.fight.lives, 2)

    def test_health_never_goes_back_up(self):
        """A worse attempt does not heal the boss."""
        self.fight.submit_result(result_with(2, 3))
        self.fight.submit_result(result_with(0, 3))
        self.assertEqual(self.fight.hp_left, 1)

    def test_all_tests_passed_wins(self):
        """Every hidden test passed: the boss is defeated, no life lost."""
        self.assertEqual(self.fight.submit_result(result_with(3, 3)), WON)
        self.assertEqual(self.fight.hp_left, 0)
        self.assertEqual(self.fight.lives, 3)

    def test_last_life_restarts_the_fight(self):
        """The third failed submit restarts with full lives, health and timer."""
        self.fight.submit_result(result_with(1, 3))
        self.fight.submit_result(result_with(1, 3))
        self.clock.now = 100
        self.assertEqual(self.fight.submit_result(result_with(2, 3)), RESTART)
        self.assertEqual(self.fight.lives, 3)
        self.assertEqual(self.fight.hp_left, 3)
        self.assertEqual(self.fight.time_left(), 600)

    def test_time_runs_out(self):
        """After the time limit, time_left is 0 and the time is up."""
        self.clock.now = 599
        self.assertFalse(self.fight.time_is_up())
        self.clock.now = 700
        self.assertEqual(self.fight.time_left(), 0)
        self.assertTrue(self.fight.time_is_up())


class TestBossLevelLoading(unittest.TestCase):
    """Check boss levels in the loader."""

    def load(self, text, folder="boss-1-test-boss"):
        """Write `text` as a level pack and load it."""
        levels_folder = make_temporary_folder(self)
        return load_level(write_level_pack(levels_folder, "w1", folder, text))

    def test_boss_level_loads(self):
        """A boss needs no concepts, tips or power-up."""
        level = self.load(VALID_BOSS_TOML)
        self.assertTrue(level.boss)
        self.assertEqual(level.time_limit, 300)
        self.assertEqual(level.sprite, "boss-placeholder")
        self.assertEqual(level.new_concepts, [])
        self.assertEqual(level.power_up, "")
        self.assertEqual(level.waves[0].kind, "boss")

    def test_defaults(self):
        """Without time_limit, a boss gets 600 seconds."""
        level = self.load(VALID_BOSS_TOML.replace("time_limit = 300\n", ""))
        self.assertEqual(level.time_limit, 600)

    def test_boss_has_exactly_one_wave(self):
        """Two waves in a boss level is an error."""
        wave = VALID_BOSS_TOML[VALID_BOSS_TOML.index("[[wave]]"):]
        with self.assertRaisesRegex(LevelError, "exactly one"):
            self.load(VALID_BOSS_TOML + wave)

    def test_boss_wave_only_in_boss_levels(self):
        """kind = "boss" in a normal level is an error, and so is "build" in a boss."""
        with self.assertRaisesRegex(LevelError, "kind must be one of"):
            self.load(VALID_BOSS_TOML.replace('kind = "boss"', 'kind = "build"'))

    def test_boss_must_be_true_or_false(self):
        """boss = "yes" is rejected."""
        with self.assertRaisesRegex(LevelError, "boss must be true or false"):
            self.load(VALID_BOSS_TOML.replace("boss = true", 'boss = "yes"'))


class TestBossCommands(unittest.TestCase):
    """Check play and submit in a boss level."""

    def setUp(self):
        """Level 1-1 (cleared) and the test boss, with a workspace."""
        self.root = make_temporary_folder(self)
        self.state = GameState(make_levels("1-1") + [make_boss_level()], workspace_root=self.root)
        self.state.cleared = ["1-1"]
        self.intro = handle_line(self.state, "play boss-1")

    def submit(self, code):
        """Type the boss code, submit it, and return the last frame as text."""
        type_code(self.state, code)
        answer = handle_line(self.state, ":submit")
        if isinstance(answer, list):
            return answer[-1]
        return answer

    def test_play_shows_the_boss_screen(self):
        """play starts the fight and shows the cutscene, task and boss screen."""
        self.assertIn("The boss wakes.", self.intro)
        self.assertIn("BOSS WAVE", self.intro)
        self.assertIn("3 hidden tests, 3 tries, 10 minutes", self.intro)
        self.assertIn("BOSS 1 · THE TEST BOSS", self.intro)
        self.assertIn("TRIES 3 of 3", self.intro)
        self.assertIsNotNone(self.state.boss_fight)

    def test_wrong_code_is_a_hit_without_revealing_tests(self):
        """The wrong solution passes 1 of 3: a life is lost, the tests stay hidden."""
        text = self.submit(make_boss_level().waves[0].wrong)
        self.assertIn("HIT! 2 hidden tests still failing. One try is used up: 2 left.", text)
        self.assertIn("TRIES 2 of 3", text)
        self.assertNotIn("should return", text)

    def test_a_crash_is_explained(self):
        """A syntax error is shown, because it says nothing about the tests."""
        text = self.submit("def add(a, b)\n    return a + b\n")
        self.assertIn("Snek tripped on line 1: a colon : is missing", text)
        self.assertIn("SyntaxError", text)

    def test_three_misses_restart_the_fight(self):
        """After the third failed submit, the fight starts again."""
        self.submit("x = 1\n")
        self.submit("x = 1\n")
        text = self.submit("x = 1\n")
        self.assertIn("The boss knocked you out", text)
        self.assertEqual(self.state.boss_fight.lives, 3)

    def test_win_clears_the_boss(self):
        """The reference solution defeats the boss and clears the level."""
        text = self.submit(make_boss_level().waves[0].reference)
        self.assertIn("BOSS DEFEATED.", text)
        self.assertIn("LEVEL SCORE 100 %", text)
        self.assertIn("boss-1", self.state.cleared)
        self.assertIsNone(self.state.boss_fight)

    def test_time_up_restarts_without_grading(self):
        """When the time is up, submit restarts the fight and costs no life."""
        clock = FakeClock()
        self.state.boss_fight.clock = clock
        self.state.boss_fight.restart()
        clock.now = 1000
        text = self.submit(make_boss_level().waves[0].reference)
        self.assertIn("TIME'S UP", text)
        self.assertNotIn("boss-1", self.state.cleared)

    def test_empty_file(self):
        """Submitting no code asks for code first."""
        self.assertIn("Type your code first", self.submit(""))

    def test_fight_starts_again_after_a_restart_of_the_game(self):
        """With no fight in memory (after quitting), submit starts a new one."""
        self.state.boss_fight = None
        text = self.submit(make_boss_level().waves[0].wrong)
        self.assertIn("One try is used up: 2 left.", text)


if __name__ == "__main__":
    unittest.main()
