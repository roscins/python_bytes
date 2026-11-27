"""Review waves: loading, grading, the key screen and typed mode."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.key_display import KeyDisplay
from engine.level_pack import LevelError, make_wave
from engine.predict_lock import locked_message
from engine.wave_screen import WaveScreen
from grader.level_limits import check_wave
from grader.wave_grader import grade_wave
from render.ansi import strip_ansi, visible_length
from tests.helpers import make_full_level
from tests.test_display import FakeKeyboard, FakeTerminal
from tests.test_key_screens import screen_text


def review_table(**changes):
    """Return a [[wave]] table with one fault on line 2."""
    table = {"kind": "debug", "mode": "review", "brief": "Review.", "goal": "Find the fault.",
             "code": "limit = 5\nprint(limit < 5)\nprint(limit)\n",
             "categories": ["wrong boundary", "unclear name"], "wrong": "1: a",
             "fault": [{"line": 2, "category": "a", "explanation": "Needs <=."}]}
    table.update(changes)
    return table


def make_game(keys=True):
    """Return a state on wave 3 of a small level whose third wave is a review."""
    level = make_full_level()
    level.waves[2] = make_wave(review_table(), "test")
    state = GameState([level])
    state.keys = keys
    state.current_level = level.id
    state.current_wave = 3
    state.coding = True
    state.wave_text(level, 3)
    return state


def make_screen():
    """Return (screen, state, terminal) with the review wave open."""
    state = make_game()
    terminal = FakeTerminal()
    display = KeyDisplay(state, terminal.write, FakeKeyboard([]), size=terminal.size,
                         sleep=terminal.sleep, delay=0)
    screen = WaveScreen(display, state)
    screen.open()
    return screen, state, terminal


def press(screen, *keys):
    """Press keys and save, as the screen's loop does."""
    for key in keys:
        screen.press(key)
        screen.sync()


class TestLoadingAndGrading(unittest.TestCase):
    """The wave file and the sheet."""

    def test_line_and_category_are_checked_separately(self):
        """Right line with the wrong name scores half."""
        wave = make_wave(review_table(), "test")
        self.assertTrue(grade_wave(wave, "2: a").all_passed())
        self.assertEqual(grade_wave(wave, "2: b").passed_count(), 1)
        self.assertEqual(check_wave(4, 3, wave), [])

    def test_marking_every_line_cannot_score(self):
        """More marks than faults is not graded."""
        wave = make_wave(review_table(), "test")
        self.assertEqual(grade_wave(wave, "1: a\n2: a\n3: a").passed_count(), 0)

    def test_bad_waves_are_rejected(self):
        """A line outside the code, a bad letter, one category, a lock."""
        for changes in [{"fault": [{"line": 9, "category": "a", "explanation": "x"}]},
                        {"fault": [{"line": 2, "category": "c", "explanation": "x"}]},
                        {"fault": []}, {"categories": ["one"]}, {"lock": True}]:
            with self.subTest(changes=changes), self.assertRaises(LevelError):
                make_wave(review_table(**changes), "test")


class TestKeyScreen(unittest.TestCase):
    """Arrows, Space and Enter."""

    def test_mark_pick_and_submit(self):
        """Line 2, category a."""
        screen, state, _ = make_screen()
        press(screen, "down", " ", "enter")
        self.assertEqual(state.buffers["1-1"][3], "2: a\n")
        press(screen, "ctrl-s")
        self.assertEqual(state.progress["1-1"].wave_best[2], 1.0)

    def test_escape_closes_the_list_and_space_removes_a_mark(self):
        """Only one line can be marked here."""
        screen, state, _ = make_screen()
        press(screen, " ", "escape")
        self.assertFalse(screen.picker.choosing)
        press(screen, " ", "enter", "down", " ")
        self.assertIn("Only 1", screen.picker.notice)
        press(screen, "up", " ")
        self.assertEqual(state.buffers["1-1"][3], "")

    def test_the_screen_fits(self):
        """80 by 24, with the categories open."""
        screen, _, terminal = make_screen()
        press(screen, " ")
        screen.draw()
        self.assertIn("b) unclear name", strip_ansi(screen_text(terminal)))
        rows = terminal.last_frame_rows()
        self.assertEqual(max(rows), 24)
        for row in rows.values():
            self.assertLessEqual(visible_length(row), 80)


class TestTypedMode(unittest.TestCase):
    """--plain play."""

    def test_a_typed_sheet_passes_without_a_lock(self):
        """line: letter."""
        state = make_game(keys=False)
        self.assertEqual(locked_message(state), "")
        handle_line(state, "2: a")
        handle_line(state, ":submit")
        self.assertEqual(state.progress["1-1"].wave_best[2], 1.0)


if __name__ == "__main__":
    unittest.main()
