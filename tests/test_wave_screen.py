"""Level 1-1 and Boss 1 played with keys only, and the wave screen's rules.

The whole game runs with the real levels, a scripted keyboard and a fake
terminal. Nothing is typed as a line.
"""

import io
import json
import unittest
from contextlib import redirect_stdout

from engine import __main__ as engine_main
from engine.game_state import GameState
from engine.key_display import KeyDisplay
from engine.level_pack import load_levels
from engine.wave_screen import WaveScreen
from render.ansi import strip_ansi, visible_length
from tests.helpers import make_temporary_folder
from tests.test_display import FakeTerminal
from tests.test_key_screens import FakeKeyboard, screen_text

LEVELS = load_levels(engine_main.LEVELS_FOLDER)


def typed(text):
    """Return the key presses that type `text`."""
    return ["enter" if character == "\n" else character for character in text]


def make_screen(level_id="1-1", wave=1, keys=()):
    """Return (wave screen, state, terminal, keyboard) with a wave of a real level open."""
    state = GameState(LEVELS)
    state.keys = True
    state.current_level = level_id
    state.current_wave = wave
    state.coding = True
    terminal = FakeTerminal()
    keyboard = FakeKeyboard(keys)
    display = KeyDisplay(state, terminal.write, keyboard, size=terminal.size, sleep=terminal.sleep, delay=0)
    screen = WaveScreen(display, state)
    screen.open()
    return screen, state, terminal, keyboard


def press(screen, *keys):
    """Press keys on an open wave screen."""
    for key in keys:
        screen.press(key)
        screen.sync()


def shown(screen, terminal):
    """Draw and return the screen as text."""
    screen.draw()
    return screen_text(terminal)


class TestOpening(unittest.TestCase):
    """Where the cursor starts."""

    def test_fill_in_starts_on_the_first_blank(self):
        """print(___)"""
        screen, _, terminal, _ = make_screen()
        self.assertEqual((screen.editor.row, screen.editor.column), (0, 6))
        text = shown(screen, terminal)
        self.assertIn("GOAL: Make Snek print SNEK ONLINE.", text)
        self.assertIn("TASK", text)
        self.assertIn("[Submit]  [Run]  [Hint]  [Restart wave]  [Map]  [Help]", text)

    def test_predict_shows_the_code_above_the_answer(self):
        """Both in one frame."""
        screen, _, terminal, _ = make_screen(wave=3)
        text = shown(screen, terminal)
        self.assertLess(text.index('# print("TWO")'), text.index("YOUR ANSWER"))

    def test_every_screen_fits_80_columns_and_24_rows(self):
        """Every wave of every level, panel open and closed."""
        for level in LEVELS:
            for number in range(1, len(level.waves) + 1):
                screen, _, terminal, _ = make_screen(level.id, number)
                for _ in range(2):
                    screen.draw()
                    rows = terminal.last_frame_rows()
                    self.assertEqual(max(rows), 24)
                    for row in rows.values():
                        self.assertLessEqual(visible_length(row), 80)
                    self.assertIn("[Submit]", rows[23])
                    screen.panel = None


class TestKeys(unittest.TestCase):
    """Focus, shortcuts and buttons."""

    def test_down_from_the_last_line_goes_to_the_buttons_and_tab_moves_on(self):
        """Up goes back to the editor."""
        screen, _, _, _ = make_screen()
        press(screen, "down")
        self.assertTrue(screen.on_buttons)
        press(screen, "tab")
        self.assertEqual(screen.buttons.label(), "Run")
        press(screen, "up")
        self.assertFalse(screen.on_buttons)

    def test_tab_in_the_editor_indents(self):
        """It does not leave the code."""
        screen, state, _, _ = make_screen(wave=2)
        press(screen, "tab", "x")
        self.assertEqual(state.buffers["1-1"][2], "    x\n")

    def test_ctrl_z_undoes(self):
        """Back to the blank."""
        screen, state, _, _ = make_screen()
        press(screen, "1", "ctrl-z")
        self.assertEqual(state.buffers["1-1"][1], "print(___)\n")

    def test_a_wrong_line_is_marked_and_the_mark_goes_when_it_is_edited(self):
        """Fix with arrows and Ctrl-S."""
        screen, _, terminal, _ = make_screen()
        press(screen, *typed("SNEK ONLINE"), "ctrl-s")
        self.assertEqual((screen.mark.row, screen.mark.column), (0, 6))
        text = shown(screen, terminal)
        self.assertIn('Text needs quotes: try print("SNEK ONLINE")', text)
        self.assertIn("^", text)
        press(screen, "left")
        self.assertIsNotNone(screen.mark)
        press(screen, "backspace")
        self.assertIsNone(screen.mark)

    def test_a_hint_is_asked_for_and_no_is_chosen(self):
        """Enter alone spends nothing; Right and Enter buys."""
        screen, state, terminal, _ = make_screen()
        press(screen, "ctrl-t")
        self.assertIn("Buy the nudge hint for", shown(screen, terminal))
        press(screen, "enter")
        self.assertEqual(state.coins, 10)
        press(screen, "ctrl-t", "right", "enter")
        self.assertLess(state.coins, 10)
        self.assertIn("HINT 1 of 3", shown(screen, terminal))

    def test_restart_wave_touches_only_this_wave(self):
        """The button; the passed wave 1 keeps its code."""
        screen, state, _, _ = make_screen()
        press(screen, *typed('"SNEK ONLINE"'), "ctrl-s", "enter")
        press(screen, "x")
        screen.do("Restart wave")
        press(screen, "right", "enter")
        self.assertEqual(state.current_wave, 2)
        self.assertEqual(state.buffers["1-1"], {1: 'print("SNEK ONLINE")\n', 2: ""})

    def test_restart_level_typed_after_ctrl_e(self):
        """Every wave, then wave 1; progress stays."""
        screen, state, _, _ = make_screen()
        press(screen, *typed('"SNEK ONLINE"'), "ctrl-s", "enter")      # passed; Next wave
        press(screen, "x", "escape", "escape")                         # hide the panel, buttons
        self.assertEqual(state.current_wave, 2)
        coins = state.coins
        screen.display.read_line = lambda prompt: "restart level"
        press(screen, "ctrl-e", "right", "enter")
        self.assertEqual(state.current_wave, 1)
        self.assertEqual(state.buffers["1-1"], {1: "print(___)\n", 2: ""})
        self.assertEqual(state.coins, coins)
        self.assertEqual(state.progress["1-1"].wave_best[0], 1.0)
        self.assertEqual(screen.labels()[0], "Next wave")

    def test_run_asks_for_input_first(self):
        """Then Ctrl-R runs with it."""
        screen, _, terminal, _ = make_screen(wave=2)
        press(screen, *typed("print(input())"), "ctrl-r")
        self.assertIn("INPUT the program will read", shown(screen, terminal))
        press(screen, *typed("hello"), "ctrl-r")
        self.assertIn("RUN (not graded)", shown(screen, terminal))
        self.assertEqual(screen.panel.lines, ["hello"])

    def test_run_is_refused_while_a_prediction_is_open(self):
        """No colon commands in the answer."""
        screen, _, terminal, _ = make_screen(wave=3)
        press(screen, "ctrl-r")
        text = shown(screen, terminal)
        self.assertIn("Ctrl-S", text)
        self.assertNotIn(":submit", text)

    def test_ctrl_e_runs_a_typed_word_without_a_colon(self):
        """stats, in the panel."""
        screen, _, terminal, _ = make_screen()
        screen.display.read_line = lambda prompt: "stats"
        press(screen, "ctrl-e")
        self.assertIn("STATS", shown(screen, terminal))


class TestPanel(unittest.TestCase):
    """Outdated results, and the panel making room while typing."""

    def submitted(self):
        """Return (screen, terminal) after a wrong Submit."""
        screen, _, terminal, _ = make_screen()
        press(screen, *typed("SNEK ONLINE"), "ctrl-s")
        return screen, terminal

    def test_editing_marks_the_results_as_outdated_and_dims_them(self):
        """Until the next check."""
        screen, terminal = self.submitted()
        self.assertNotIn("edited since", shown(screen, terminal))
        press(screen, "left", "x")
        self.assertIn("RESULTS · edited since last check", shown(screen, terminal))
        self.assertIn("\x1b[2mNot yet.", terminal.text())
        press(screen, "ctrl-s")
        self.assertNotIn("edited since", shown(screen, terminal))

    def test_undoing_the_edit_makes_them_current_again(self):
        """The code is what was checked."""
        screen, terminal = self.submitted()
        press(screen, "x", "backspace")
        self.assertNotIn("edited since", shown(screen, terminal))

    def test_a_task_panel_is_never_outdated(self):
        """It is not about the code."""
        screen, _, terminal, _ = make_screen()
        press(screen, "x")
        self.assertNotIn("edited since", shown(screen, terminal))

    def panel_text_rows(self, screen):
        """Return how many rows of text are inside the panel."""
        lines = [strip_ansi(line) for line in screen.lines(19)]
        top = next(index for index, line in enumerate(lines) if "RESULTS" in line)
        bottom = next(index for index in range(top, len(lines)) if lines[index].startswith("└"))
        return bottom - top - 1

    def test_typing_shrinks_the_panel_to_three_lines(self):
        """Moving the cursor does not; the code gets the room."""
        screen, _ = self.submitted()
        press(screen, "left")
        self.assertEqual(self.panel_text_rows(screen), 6)
        press(screen, "x")
        self.assertEqual(self.panel_text_rows(screen), 3)
        self.assertEqual(screen.editor_rows(19), 11)
        self.assertEqual(len(screen.lines(19)), 19)

    def test_escape_hides_it_and_f1_or_the_button_shows_it(self):
        """Full size again."""
        screen, terminal = self.submitted()
        press(screen, "escape")
        self.assertNotIn("RESULTS", shown(screen, terminal))
        self.assertIn("[Panel]", screen_text(terminal))
        press(screen, "f1")
        self.assertIn("RESULTS", shown(screen, terminal))
        press(screen, "escape")
        screen.do("Panel")
        self.assertIn("RESULTS", shown(screen, terminal))
        self.assertNotIn("[Panel]", screen_text(terminal))

    def test_the_longest_button_row_fits(self):
        """[Next level], six buttons and [Panel] in 80 columns."""
        screen, state, terminal, _ = make_screen(wave=3)
        state.progress_for(screen.level).wave_best = [1.0, 1.0, 1.0]
        state.cleared = ["1-1"]
        press(screen, "x")
        screen.focus_buttons()
        text = shown(screen, terminal)
        self.assertIn("[Next level]", text)
        self.assertIn("[Panel]", text)


class TestAutosave(unittest.TestCase):
    """The code is saved while it is typed."""

    def test_saved_after_every_edit(self):
        """Each key is followed by a save that already holds it."""
        screen, state, _, _ = make_screen(wave=2, keys=["a", "b", "ctrl-o"])
        saved = []
        screen.save = lambda: saved.append(state.buffers["1-1"].get(2))
        self.assertEqual(screen.run(), ":map")
        self.assertEqual(saved[:2], ["a\n", "ab\n"])


class TestPlayingWithKeysOnly(unittest.TestCase):
    """The real game, from the title to the end, with no typed line."""

    def play(self, keys, save=None):
        """Run the game with `keys`; return the saved data."""
        self.save_path = make_temporary_folder(self) / "save.json"
        if save is not None:
            self.save_path.write_text(json.dumps(save), encoding="utf-8")
        self.terminal = FakeTerminal()
        self.keyboard = FakeKeyboard(keys)

        def factory(state):
            return KeyDisplay(state, self.terminal.write, self.keyboard, size=self.terminal.size,
                              sleep=self.terminal.sleep, delay=0)

        def read_line(prompt):
            self.fail(f"A line was asked for: {prompt!r}")

        with redirect_stdout(io.StringIO()):
            code = engine_main.run_game(save_path=self.save_path, read_line=read_line,
                                        display_factory=factory)
        self.assertEqual(code, 0)
        self.assertEqual(self.keyboard.keys, [], "keys were left over")
        with open(self.save_path, encoding="utf-8") as save_file:
            return json.load(save_file)

    def text(self):
        """Return everything drawn, without colours."""
        return strip_ansi(self.terminal.text())

    def test_all_of_level_1_1(self):
        """Wrong first, fixed with arrows; then waves 2 and 3, and the level is cleared."""
        keys = ["enter", "enter",                 # title, NEW GAME
                "escape", "enter", "escape"]      # skip tutorial, play 1-1, skip the story
        keys += typed("SNEK ONLINE") + ["ctrl-s"]                 # no quotes
        keys += ["end", "left"] + ["left"] * 11 + ['"'] + ["right"] * 11 + ['"', "ctrl-s"]
        keys += ["enter"]                                          # Next wave
        keys += typed('# start-up\nprint("SYSTEM CHECK")\nprint("VOICE MODULE OK")\n'
                      'print("HELLO, TECHNICIAN")') + ["ctrl-s", "enter"]
        keys += typed("ONE\nTHREE") + ["ctrl-s"]
        keys += ["enter"]                                          # the level-clear animation
        keys += ["right", "right", "right", "right", "right", "enter"]   # the Map button
        keys += ["down", "right", "right", "right", "enter"]       # Quit
        # Buttons after the last wave: Next level, Submit, Run, Hint, Restart level, Map.
        save = self.play(keys)
        self.assertIn("1-1", save["cleared"])
        self.assertEqual(save["levels"]["1-1"]["wave_best"], [1.0, 1.0, 1.0])
        self.assertIn('Text needs quotes: try print("SNEK ONLINE")', self.text())
        self.assertIn("LEVEL 1-1 CLEARED", self.text())
        self.assertIn("[Next level]", self.text())

    def test_all_of_boss_1(self):
        """The starter crashes (line marked), then the program is repaired and the boss falls."""
        boss = next(level for level in LEVELS if level.id == "boss-1")
        starter = boss.waves[0].starter.strip()
        repaired = boss.waves[0].reference.strip()
        cleared = ["1-1", "1-2", "1-3", "1-4", "1-5"]
        save = {"version": 1, "current_level": "boss-1", "current_wave": 1, "coding": False,
                "cleared": cleared, "xp": 0, "coins": 10, "combo": 0, "levels": {}, "buffers": {}}
        keys = ["enter", "enter", "enter", "escape"]               # title, CONTINUE, play, skip intro
        keys += ["ctrl-s"]                                         # the broken starter
        # Remove everything (Delete works from line 1), then type the repair.
        keys += ["page-up"] + ["up"] * 20 + ["home"] + ["delete"] * len(starter)
        keys += typed(repaired) + ["ctrl-r", "ctrl-s"]
        keys += ["enter"]                                          # the boss's last picture
        keys += ["ctrl-o"]
        keys += ["down", "right", "right", "right", "enter"]
        result = self.play(keys, save)
        self.assertIn("boss-1", result["cleared"])
        self.assertEqual(result["buffers"]["boss-1"]["1"], repaired + "\n")
        self.assertIn("HIT!", self.text())
        self.assertIn("BOSS DEFEATED.", self.text())


if __name__ == "__main__":
    unittest.main()
