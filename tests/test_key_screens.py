"""Tests for the key-driven screens: engine/key_screens.py and engine/key_display.py.

The keyboard and the terminal are fakes: the test lists the keys pressed.
"""

import io
import json
import signal
import sys
import unittest
from contextlib import redirect_stdout

from engine import __main__ as engine_main
from engine.game_state import GameState
from engine.key_display import KeyDisplay
from engine.key_screens import (
    FULL,
    PLAIN,
    MapScreen,
    title_menu,
    wait_for_window_keys,
)
from engine.shutdown import GameInterrupted, ShutdownGuard
from engine.title import CONTINUE, NEW, QUIT, SaveInfo
from render.ansi import strip_ansi
from tests.helpers import make_levels, make_temporary_folder
from tests.test_display import FakeKeyboard, FakeTerminal


def make_key_display(keys, state=None, terminal=None):
    """Return (display, terminal, keyboard) with no animations."""
    if state is None:
        state = GameState(make_levels("1-1", "1-2"))
    if terminal is None:
        terminal = FakeTerminal()
    keyboard = FakeKeyboard(keys)
    display = KeyDisplay(state, terminal.write, keyboard, size=terminal.size, sleep=terminal.sleep, delay=0)
    return display, terminal, keyboard


def screen_text(terminal):
    """Return the last drawn screen as text without colours."""
    rows = terminal.last_frame_rows()
    return "\n".join(rows[number] for number in sorted(rows))


class TestTitleMenu(unittest.TestCase):
    """Up, Down and Enter on the title menu."""

    def choose(self, keys, status="ok"):
        """Return the choice made with `keys`."""
        display, _, _ = make_key_display(keys)
        return title_menu(display, SaveInfo(status, "1-1", 1))

    def test_enter_takes_the_first_option(self):
        """CONTINUE with a save, NEW GAME without."""
        self.assertEqual(self.choose(["enter"]), CONTINUE)
        self.assertEqual(self.choose(["enter"], status="none"), NEW)

    def test_down_moves_to_quit(self):
        """Two down from CONTINUE."""
        self.assertEqual(self.choose(["down", "down", "enter"]), QUIT)

    def test_new_game_over_a_save_asks_with_no_chosen(self):
        """Enter at the question goes back; then Yes."""
        self.assertEqual(self.choose(["down", "enter", "enter", "down", "enter"]), QUIT)
        self.assertEqual(self.choose(["down", "enter", "down", "enter"]), NEW)

    def test_the_end_of_input_quits(self):
        """And Ctrl-D."""
        self.assertEqual(self.choose([]), QUIT)
        self.assertEqual(self.choose(["ctrl-d"]), QUIT)


class TestMapScreen(unittest.TestCase):
    """Walking the map."""

    def line_for(self, keys):
        """Return the command line the map gives for `keys`."""
        state = GameState(make_levels("1-1", "1-2"))
        display, self.terminal, _ = make_key_display(keys, state)
        return MapScreen(display, state).next_line()

    def test_enter_plays_the_level_snek_is_at(self):
        """The first one, to begin with."""
        self.assertEqual(self.line_for(["enter"]), "play 1-1")

    def test_right_moves_snek_and_the_ends_stop_her(self):
        """Even to a locked level: play then says why."""
        self.assertEqual(self.line_for(["left", "right", "right", "enter"]), "play 1-2")

    def test_the_buttons(self):
        """Down, then Right and Enter."""
        self.assertEqual(self.line_for(["down", "right", "enter"]), "stats")
        self.assertEqual(self.line_for(["down", "right", "right", "right", "enter"]), "quit")
        self.assertEqual(self.line_for(["down", "up", "enter"]), "play 1-1")

    def test_a_colon_lets_a_command_be_typed(self):
        """On the last row, with the keyboard back to normal."""
        state = GameState(make_levels("1-1"))
        display, _, keyboard = make_key_display([":"], state)
        seen = []

        def read_line(prompt):
            seen.append(keyboard.started)
            return "stats"

        display.read_line = read_line
        self.assertEqual(MapScreen(display, state).next_line(), "stats")
        self.assertEqual(seen, [False])

    def test_the_map_names_the_level_and_shows_the_buttons(self):
        """What is drawn."""
        self.line_for(["enter"])
        text = screen_text(self.terminal)
        self.assertIn("[1-1]", text)
        self.assertIn("[Play]  [Stats]  [Help]  [Quit]", text)
        self.assertIn("Enter play", text)


class TestPauses(unittest.TestCase):
    """Screens that wait for a key."""

    def test_pages_go_back_and_forth(self):
        """Enter pages on, Up goes back, Enter on the last page ends."""
        display, _, keyboard = make_key_display(["enter", "up", "down", "enter"])
        self.assertEqual(display.browse([["one"], ["two"]]), "Continue")
        self.assertEqual(keyboard.keys, [])

    def test_escape_skips_screens(self):
        """Story and tips."""
        display, _, keyboard = make_key_display(["escape", "enter"])
        display.show("first\fsecond\fthird")
        self.assertEqual(keyboard.keys, [])

    def test_the_next_level_button(self):
        """After the last wave it stands for the play command."""
        state = GameState(make_levels("1-1", "1-2"))
        state.cleared = ["1-1"]
        display, _, _ = make_key_display(["enter"], state)
        self.assertEqual(display.show("That was the last wave. Next: play 1-2"), "play 1-2")
        display, _, _ = make_key_display(["right", "enter"], state)
        self.assertIsNone(display.show("That was the last wave. Next: play 1-2"))

    def test_a_signal_that_came_while_drawing_stops_the_wait(self):
        """The flag is looked at before waiting."""
        display, _, _ = make_key_display(["enter"])
        display.guard = ShutdownGuard()
        display.guard.handle(signal.SIGTERM, None)
        with self.assertRaises(GameInterrupted) as caught:
            display.wait_key()
        self.assertEqual(caught.exception.code, 128 + signal.SIGTERM)


class TestWindowCheck(unittest.TestCase):
    """A window that is too small."""

    def test_p_plays_plain_and_a_bigger_window_goes_on(self):
        """The keyboard is put back either way."""
        keyboard = FakeKeyboard(["p"])
        self.assertEqual(wait_for_window_keys(keyboard, lambda: (10, 10), lambda text: None), PLAIN)
        self.assertFalse(keyboard.started)
        sizes = iter([(10, 10), (80, 24)])
        keyboard = FakeKeyboard([None])
        self.assertEqual(wait_for_window_keys(keyboard, lambda: next(sizes), lambda text: None), FULL)


class TestWholeGameWithKeys(unittest.TestCase):
    """run_game with the real levels and a scripted keyboard."""

    def play(self, keys, lines=()):
        """Play; `lines` are what is typed when a line is asked for. Return the exit code."""
        self.save_path = make_temporary_folder(self) / "save.json"
        self.terminal = FakeTerminal()
        self.keyboard = FakeKeyboard(keys)
        typed = list(lines)

        def factory(state):
            return KeyDisplay(state, self.terminal.write, self.keyboard, size=self.terminal.size,
                              sleep=self.terminal.sleep, delay=0)

        def read_line(prompt):
            return typed.pop(0)

        with redirect_stdout(io.StringIO()):
            return engine_main.run_game(save_path=self.save_path, read_line=read_line,
                                        display_factory=factory, concepts_file=None)

    def test_from_the_title_into_a_level_and_out_through_the_map(self):
        """Title, tutorial (Esc), map, Enter, story (Esc), a typed character, ^O, the Quit button."""
        keys = ["enter", "enter",              # title, NEW GAME
                "escape", "enter",             # skip the tutorial, play 1-1
                "escape",                      # skip the story
                "7", "ctrl-o",                 # type on the blank, then the map
                "down", "right", "right", "right", "enter"]
        code = self.play(keys)
        self.assertEqual(code, 0)
        self.assertEqual(self.keyboard.keys, [])
        self.assertFalse(self.keyboard.started)
        with open(self.save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["buffers"]["1-1"]["1"], "print(7)\n")
        self.assertIn("Left and Right move Snek", strip_ansi(self.terminal.text()))

    def test_the_keyboard_is_put_back_after_an_error(self):
        """A crash inside the game."""
        with self.assertRaises(IndexError):
            # Ctrl-E asks for a line, and there is none to give.
            self.play(["enter", "enter", "escape", "enter", "escape", "ctrl-e"], [])
        self.assertFalse(self.keyboard.started)


if __name__ == "__main__":
    unittest.main()
