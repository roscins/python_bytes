"""Plan-first and require_call tests, the code-quality rule and review comments."""

import unittest

from engine.game_state import GameState
from engine.level_pack import load_levels
from engine.progress import progress_from_dict
from engine.results_screen import reward_lines
from engine.review_picker import ReviewPicker
from engine.rewards import apply_submission
from engine.scoring import stars_for
from engine.submission import WaveSubmission
from grader.answer_sheet import comparison_lines, read_comments
from grader.checks import CheckResult, run_check
from grader.wave_grader import WaveResult, grade_wave
from tests.helpers import make_full_level

LEVELS = {level.id: level for level in load_levels("levels")}
PLAN = {"require_plan": 3}


def graded(number, wave, passed, quality=None):
    """Return a submission whose tests pass or fail, with a given quality share."""
    rules = None
    if quality is not None:
        rules = [CheckResult(index < quality * 4, "rule") for index in range(4)]
    return WaveSubmission(number, wave, "your code",
                          WaveResult([CheckResult(passed, "test")], rules))


def play(world, quality):
    """Pass every wave of a small level of `world` with the build code at `quality`."""
    level = make_full_level()
    level.world = world
    state = GameState([level])
    for number, wave in enumerate(level.waves, start=1):
        share = quality if wave.kind == "build" else None
        reward = apply_submission(state, level, [graded(number, wave, True, share)])
    return state, level, reward


class TestPlanAndCalls(unittest.TestCase):
    """The two new kinds of test."""

    def test_three_comment_lines_before_the_code(self):
        """Blank lines are fine; later or empty comments do not count."""
        self.assertTrue(run_check(PLAN, "# a\n\n# b\n# c\nx = 1\n").passed)
        for code in ["# a\n# b\nx = 1\n# c\n", "# a\n#\n# b\nx = 1\n", "x = 1  # a\n# b\n# c\n"]:
            with self.subTest(code=code):
                self.assertFalse(run_check(PLAN, code).passed)

    def test_the_plan_missions_require_a_plan(self):
        """2-5, 4-5 and Boss 4: the reference passes, without its plan it fails."""
        for level_id in ["2-5", "4-5", "boss-4"]:
            wave = LEVELS[level_id].waves[0 if level_id == "boss-4" else 1]
            with self.subTest(level=level_id):
                self.assertIn(PLAN, [{key: test[key] for key in test if key == "require_plan"}
                                     for test in wave.tests])
                bare = "".join(line for line in wave.reference.splitlines(True)
                               if not line.startswith("# "))
                self.assertFalse(run_check(PLAN, bare).passed)

    def test_archive_build_needs_with_csv_and_path(self):
        """Reading the file another way is not enough."""
        wave = LEVELS["4-3"].waves[1]
        changed = wave.reference.replace("source = Path(log_name)", "source = log_name")
        self.assertFalse(grade_wave(wave, changed).all_passed())
        check = {"require_call": ["csv.reader"]}
        self.assertTrue(run_check(check, "csv.reader(x)\n").passed)
        self.assertFalse(run_check(check, "reader(x)\n").passed)


class TestQualityRule(unittest.TestCase):
    """Clearing and stars."""

    def test_world_three_needs_half_the_quality_rules(self):
        """Below 50 % the level stays closed and the panel says why."""
        state, level, reward = play(3, 0.25)
        self.assertNotIn(level.id, state.cleared)
        self.assertIn("improve wave 2", "\n".join(reward_lines(level, reward)))
        self.assertIn(play(3, 0.5)[1].id, play(3, 0.5)[0].cleared)

    def test_improving_the_build_wave_clears_the_level(self):
        """No other wave has to be done again."""
        state, level, _ = play(3, 0.25)
        apply_submission(state, level, [graded(2, level.waves[1], True, 1.0)])
        self.assertIn(level.id, state.cleared)

    def test_early_worlds_have_no_gate(self):
        """World 2 clears with any quality."""
        state, level, _ = play(2, 0.25)
        self.assertIn(level.id, state.cleared)

    def test_quality_of_failing_code_does_not_count(self):
        """Tidy code that fails its tests cannot open the gate."""
        state, level, _ = play(3, 0.25)
        apply_submission(state, level, [graded(2, level.waves[1], False, 1.0)])
        self.assertNotIn(level.id, state.cleared)

    def test_three_stars_need_full_quality(self):
        """Even with a score of 100."""
        self.assertEqual(stars_for(100, False, full_quality=False), 2)

    def test_an_old_save_keeps_its_quality(self):
        """Saves without passed_quality use best_quality."""
        data = play(3, 1.0)[0].progress["1-1"].to_dict()
        del data["passed_quality"]
        self.assertEqual(progress_from_dict(data, 3).passed_quality, 1.0)


class TestReviewComments(unittest.TestCase):
    """The ungraded comment of 3-4's review wave."""

    def test_typing_a_comment_after_the_category(self):
        """It is saved on the sheet and does not change the grade."""
        wave = LEVELS["3-4"].waves[3]
        picker = ReviewPicker(wave, "")
        for key in [" ", "enter", *"use None", "enter"]:
            picker.press(key)
        self.assertEqual(picker.sheet(), "1: a  # use None\n")
        self.assertFalse(picker.choosing)
        self.assertEqual(read_comments(picker.sheet()), {1: "use None"})
        self.assertEqual(grade_wave(wave, picker.sheet()).passed_count(), 2)
        self.assertIn("Line 1, yours: use None", comparison_lines(wave, picker.sheet()))

    def test_waves_without_model_comments_ask_for_none(self):
        """4-4 goes straight back to the code."""
        picker = ReviewPicker(LEVELS["4-4"].waves[2], "")
        picker.press(" ")
        picker.press("enter")
        self.assertFalse(picker.typing)


if __name__ == "__main__":
    unittest.main()
