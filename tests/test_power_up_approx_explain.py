"""The approx and explain power-ups."""

import unittest
from pathlib import Path

from engine.commands import handle_line
from engine.game_state import GameState
from engine.level_pack import load_levels
from engine.powerups import POWER_UPS
from engine.powerups.approx import do_approx
from engine.powerups.explain import do_explain
from tests.helpers import make_full_level

LEVELS_FOLDER = Path(__file__).parent.parent / "levels"


class TestApprox(unittest.TestCase):
    """The stored digits of floats."""

    def test_one_number(self):
        """What you see and what is stored."""
        view = do_approx(GameState(), "0.1 + 0.2")
        self.assertIn("0.30000000000000004", view)
        self.assertIn("0.3000000000000000444089209850062616169452667236328125", view)

    def test_two_numbers(self):
        """== fails, isclose succeeds."""
        view = do_approx(GameState(), "0.1 + 0.2, 0.3")
        self.assertIn("==            False", view)
        self.assertIn("math.isclose  True", view)
        self.assertIn("0.299999999999999988897769753748434595763683319091796875", view)

    def test_extreme_and_bad_input_stays_on_screen(self):
        """Huge, tiny, infinite and wrong input: short lines and no crash."""
        for text in ["1e308", "5e-324", "float('inf')", "float('nan'), 1.0", "10 ** 400, 1.5",
                     "'a'", "1 / 0", "1, 2, 3", "nothing", "9 ** 9 ** 9", "(", "[1]"]:
            with self.subTest(text=text):
                view = do_approx(GameState(), text)
                self.assertLessEqual(max(len(line) for line in view.splitlines()), 100)
                if view.startswith("APPROX"):
                    self.assertLessEqual(max(len(line) for line in view.splitlines()), 74)


class TestExplain(unittest.TestCase):
    """The parts of a line."""

    def test_call_string_comment_and_screen(self):
        """Each part is marked under its characters."""
        view = do_explain(GameState(), 'print("# 1 ready")  # start-up').splitlines()
        self.assertEqual(view[2], "^^^^^                           call: show something")
        self.assertEqual(view[3], "      ^^^^^^^^^^^               string: this # is only text")
        self.assertEqual(view[4], "                    ^^^^^^^^^^  comment: Python skips it")
        self.assertEqual(view[5], "SCREEN: # 1 ready")

    def test_a_commented_out_line_shows_nothing(self):
        """The whole line is a comment."""
        view = do_explain(GameState(), '# print("TWO")')
        self.assertIn("comment", view)
        self.assertIn("SCREEN: (nothing)", view)
        self.assertNotIn("call:", view)

    def test_it_runs_nothing(self):
        """A name or a sum is not worked out."""
        for line in ["print(x)", "print(1 + 1)", "x = 1", "print(f'{x}')"]:
            with self.subTest(line=line):
                self.assertIn("runs nothing", do_explain(GameState(), line))

    def test_bad_and_long_lines(self):
        """A friendly answer."""
        self.assertIn("cannot read", do_explain(GameState(), 'print("a'))
        self.assertIn("at most 40", do_explain(GameState(), "print(" + "1, " * 20 + "1)"))
        self.assertIn("Usage", do_explain(GameState(), ""))


class TestAllWorldOnePowerUps(unittest.TestCase):
    """Every power-up a World 1 level announces exists."""

    def test_each_level_has_its_tool(self):
        """No level promises a command that does nothing."""
        for level in load_levels(LEVELS_FOLDER):
            if level.world == 1 and not level.boss:
                with self.subTest(level=level.id):
                    self.assertIn(level.power_up, POWER_UPS)

    def test_they_work_in_a_boss_fight(self):
        """In a boss wave every tool answers with its colon."""
        level = make_full_level()
        level.power_up = "explain"
        boss = load_levels(LEVELS_FOLDER)[-1]
        state = GameState([level, boss])
        self.addCleanup(state.close)
        state.cleared.append(level.id)
        state.cleared.extend(["1-2", "1-3", "1-4", "1-5"])
        state.current_level = boss.id
        state.coding = True
        self.assertTrue(boss.boss)
        self.assertIn("SCREEN: hi", handle_line(state, ':explain print("hi")'))


if __name__ == "__main__":
    unittest.main()
