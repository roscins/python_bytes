"""Choice waves: loading, the answer sheet, the key screen, typed mode and the lock."""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.key_display import KeyDisplay
from engine.level_pack import LevelError, make_wave
from engine.predict_lock import locked_message
from engine.wave_screen import WaveScreen
from grader.answer_sheet import read_sheet
from grader.level_limits import check_wave
from grader.wave_grader import grade_wave
from render.ansi import strip_ansi, visible_length
from tests.helpers import make_full_level
from tests.test_display import FakeKeyboard, FakeTerminal
from tests.test_key_screens import screen_text


def choice_table(**changes):
    """Return a [[wave]] table with two questions; keyword arguments replace parts."""
    questions = [
        {"ask": "Keeps order and repeats?", "options": ["list", "set"], "answer": "a",
         "explanation": "A list keeps both."},
        {"ask": "No repeats?", "options": ["list", "set"], "answer": "b",
         "explanation": "A set keeps one of each."},
    ]
    table = {"kind": "debug", "mode": "choice", "brief": "Pick.", "goal": "Pick.",
             "wrong": "1: b\n2: b", "question": questions}
    table.update(changes)
    return table


def make_game(keys=True, **changes):
    """Return a state on wave 3 of a small level whose third wave is a choice wave."""
    level = make_full_level()
    level.waves[2] = make_wave(choice_table(**changes), "test")
    state = GameState([level])
    state.keys = keys
    state.current_level = level.id
    state.current_wave = 3
    state.coding = True
    state.wave_text(level, 3)
    return state


def make_screen():
    """Return (screen, state, terminal) with the choice wave open."""
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

    def test_the_right_sheet_comes_from_the_questions(self):
        """It passes, the wrong one does not."""
        wave = make_wave(choice_table(), "test")
        self.assertEqual(wave.answer, "1: a\n2: b\n")
        self.assertTrue(grade_wave(wave, wave.answer).all_passed())
        self.assertEqual(grade_wave(wave, wave.wrong).passed_count(), 1)
        self.assertEqual(check_wave(4, 3, wave), [])

    def test_an_unreadable_wrong_sheet_is_a_problem(self):
        """It would fail for the wrong reason."""
        wave = make_wave(choice_table(wrong="1: b, 2: a"), "test")
        self.assertIn("cannot be graded", " ".join(check_wave(4, 3, wave)))

    def test_bad_waves_are_rejected(self):
        """Wrong kind, unknown mode, bad answer letter, no questions."""
        bad_question = dict(choice_table()["question"][0], answer="c")
        for changes in [{"kind": "build"}, {"mode": "guess"}, {"question": []},
                        {"question": [bad_question]}, {"lock": "yes"}]:
            with self.subTest(changes=changes), self.assertRaises(LevelError):
                make_wave(choice_table(**changes), "test")

    def test_a_later_line_replaces_an_earlier_one(self):
        """So a typed answer can be changed."""
        self.assertEqual(read_sheet("1: a\n 1 : B \n"), ({1: "b"}, ""))
        self.assertNotEqual(read_sheet("one: a")[1], "")


class TestKeyScreen(unittest.TestCase):
    """Arrows and Enter."""

    def test_picking_writes_the_sheet_and_submit_passes(self):
        """a, then b; the cursor ends on the buttons."""
        screen, state, _ = make_screen()
        press(screen, "enter", "down", "enter")
        self.assertEqual(state.buffers["1-1"][3], "1: a\n2: b\n")
        self.assertTrue(screen.on_buttons)
        press(screen, "ctrl-s")
        self.assertEqual(state.progress["1-1"].wave_best[2], 1.0)

    def test_typing_does_nothing(self):
        """No answer sheet is typed in key mode."""
        screen, state, _ = make_screen()
        press(screen, "1", ":", "a")
        self.assertEqual(state.buffers["1-1"][3], "")

    def test_the_screen_fits_and_shows_the_options(self):
        """80 by 24."""
        screen, _, terminal = make_screen()
        screen.draw()
        text = screen_text(terminal)
        self.assertIn("> [ ] a) list", strip_ansi(text))
        rows = terminal.last_frame_rows()
        self.assertEqual(max(rows), 24)
        for row in rows.values():
            self.assertLessEqual(visible_length(row), 80)

    def test_three_failures_show_the_answers(self):
        """The wave is then done."""
        screen, state, _ = make_screen()
        press(screen, "down", "enter", "enter")
        press(screen, "ctrl-s", "ctrl-s", "ctrl-s")
        self.assertTrue(state.progress["1-1"].revealed[2])
        self.assertIn("A set keeps one of each.", " ".join(screen.panel.lines))


class TestTypedModeAndLock(unittest.TestCase):
    """--plain play, and the console."""

    def test_a_typed_sheet_passes(self):
        """Lines are typed, then :submit."""
        state = make_game(keys=False)
        handle_line(state, "1: a")
        handle_line(state, "2: b")
        handle_line(state, ":submit")
        self.assertEqual(state.progress["1-1"].wave_best[2], 1.0)

    def test_an_unreadable_sheet_costs_no_attempt(self):
        """The player is told the format."""
        state = make_game(keys=False)
        handle_line(state, "list")
        self.assertIn("number: letter", handle_line(state, ":submit"))
        self.assertEqual(state.progress_for(state.levels[0]).wave_attempts[2], 0)

    def test_only_questions_about_code_lock_the_console(self):
        """Question code or lock = true."""
        self.assertEqual(locked_message(make_game()), "")
        self.assertIn("question about code", locked_message(make_game(lock=True)))
        with_code = choice_table()["question"]
        with_code[0]["code"] = "print(1)"
        self.assertNotEqual(locked_message(make_game(question=with_code)), "")


if __name__ == "__main__":
    unittest.main()
