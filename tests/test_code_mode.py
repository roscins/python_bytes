"""Tests for engine/code_mode.py: typing code into the game, one line at a time."""

import unittest

from engine.code_mode import add_code_line, buffer_lines, lines_to_text, prompt_for
from engine.commands import handle_line
from engine.game_state import GameState
from tests.helpers import make_boss_level, make_full_level, type_code


def new_game(plain=True):
    """Return a game with the three-wave Level 1-1, already started (wave 1, fill-in)."""
    state = GameState([make_full_level()])
    state.plain = plain
    handle_line(state, "play 1-1")
    return state


def code_of(state, number=None):
    """Return the code typed so far for a wave of Level 1-1 (the current wave by default)."""
    if number is None:
        number = state.current_wave
    return state.wave_text(state.levels[0], number)


class TestBufferHelpers(unittest.TestCase):
    """Lines and texts."""

    def test_lines_round_trip(self):
        """A list of lines becomes a text with a newline after each, and back."""
        self.assertEqual(lines_to_text(["a", "b"]), "a\nb\n")
        self.assertEqual(buffer_lines("a\nb\n"), ["a", "b"])
        self.assertEqual(lines_to_text([]), "")

    def test_blank_lines_in_the_middle_survive(self):
        """Blank lines between two functions are part of the code."""
        self.assertEqual(buffer_lines(lines_to_text(["a", "", "b"])), ["a", "", "b"])


class TestEnteringAWave(unittest.TestCase):
    """What play does."""

    def test_play_starts_code_mode_on_wave_one(self):
        """The player is coding, on the first wave."""
        state = new_game()
        self.assertTrue(state.coding)
        self.assertEqual(state.current_wave, 1)

    def test_play_shows_the_story_and_the_first_wave(self):
        """The intro ends with the wave: its task and the starter code."""
        state = GameState([make_full_level()])
        text = handle_line(state, "play 1-1")
        self.assertIn("TIPS", text)
        self.assertIn("WAVE 1 of 3 · FILL-IN", text)
        self.assertIn("  1 │ print(___)", text)

    def test_a_fill_in_wave_starts_with_its_starter_code(self):
        """The blanks are in the buffer, ready to be edited."""
        self.assertEqual(code_of(new_game()), "print(___)\n")

    def test_a_build_wave_starts_empty(self):
        """Nothing to start from."""
        state = new_game()
        handle_line(state, ":wave 2")
        self.assertEqual(code_of(state), "")

    def test_playing_again_goes_to_the_first_unfinished_wave_and_keeps_the_code(self):
        """Leaving with :map and coming back loses nothing."""
        state = new_game()
        type_code(state, 'print("a")')
        handle_line(state, ":map")
        self.assertFalse(state.coding)
        handle_line(state, "play 1-1")
        self.assertTrue(state.coding)
        self.assertEqual(code_of(state), 'print("a")\n')


class TestTypingLines(unittest.TestCase):
    """Every line that is not a command is code."""

    def test_lines_are_added_in_order(self):
        """Each typed line goes to the end of the code."""
        state = new_game()
        type_code(state, "a = 1\nb = 2")
        self.assertEqual(code_of(state), "a = 1\nb = 2\n")

    def test_indentation_is_kept_exactly(self):
        """Leading spaces are the player's indentation."""
        state = new_game()
        type_code(state, "if x:\n    y = 1\n        z = 2")
        self.assertEqual(code_of(state), "if x:\n    y = 1\n        z = 2\n")

    def test_a_tab_becomes_four_spaces(self):
        """Pressing Tab indents by four."""
        state = new_game()
        type_code(state, "if x:\n\ty = 1")
        self.assertEqual(code_of(state), "if x:\n    y = 1\n")

    def test_words_that_are_commands_outside_code_mode_are_code_inside_it(self):
        """help, map and quit typed while coding are lines of code."""
        state = new_game()
        type_code(state, "map")
        self.assertEqual(code_of(state), "map\n")
        self.assertTrue(state.coding)

    def test_a_line_that_only_looks_like_a_command_with_a_leading_space_is_code(self):
        """A space before the colon makes it code (for a line inside a long string)."""
        state = new_game()
        type_code(state, " :not a command")
        self.assertEqual(code_of(state), " :not a command\n")

    def test_empty_lines_are_kept_between_code_but_not_piled_up(self):
        """One blank line is fine; pressing Enter again adds nothing."""
        state = new_game()
        type_code(state, "a = 1")
        for line in ["", "", "b = 2"]:
            add_code_line(state, line)
        self.assertEqual(code_of(state), "a = 1\n\nb = 2\n")

    def test_an_empty_line_at_the_start_adds_nothing(self):
        """Enter on an empty buffer does nothing."""
        state = new_game()
        handle_line(state, ":clear")
        add_code_line(state, "")
        self.assertEqual(code_of(state), "")

    def test_each_line_is_a_new_undo_step(self):
        """:undo removes one typed line at a time."""
        state = new_game()
        type_code(state, "a = 1\nb = 2")
        handle_line(state, ":undo")
        self.assertEqual(code_of(state), "a = 1\n")


class TestPrompt(unittest.TestCase):
    """The prompt tells the player where they are."""

    def test_map_prompt(self):
        """Outside a wave."""
        self.assertEqual(prompt_for(GameState([make_full_level()])), "> ")

    def test_code_prompt_counts_the_next_line(self):
        """It shows the number of the line that will be typed."""
        state = new_game()
        self.assertEqual(prompt_for(state), "  2 | ")
        type_code(state, "a = 1\nb = 2")
        self.assertEqual(prompt_for(state), "  3 | ")

    def test_fancy_prompt_uses_a_box_character(self):
        """Not plain: a vertical bar from the box-drawing set."""
        self.assertEqual(prompt_for(new_game(plain=False)), "  2 │ ")


class TestShowUndoClear(unittest.TestCase):
    """:show, :undo and :clear."""

    def test_show_numbers_the_lines(self):
        """The task, then the numbered code."""
        state = new_game()
        type_code(state, "a = 1\nb = 2")
        text = handle_line(state, ":show")
        self.assertIn("WAVE 1 of 3", text)
        self.assertIn("  1 | a = 1", text)
        self.assertIn("  2 | b = 2", text)

    def test_clear_empties_and_undo_brings_it_back(self):
        """:clear is never a loss."""
        state = new_game()
        type_code(state, "a = 1")
        self.assertIn("Cleared", handle_line(state, ":clear"))
        self.assertEqual(code_of(state), "")
        self.assertIn("Undone", handle_line(state, ":undo"))
        self.assertEqual(code_of(state), "a = 1\n")

    def test_undo_with_nothing_to_undo(self):
        """A polite answer."""
        state = new_game()
        self.assertEqual(handle_line(state, ":undo"), "There is nothing to undo.")

    def test_undo_is_per_wave(self):
        """Another wave's changes are not undone here."""
        state = new_game()
        handle_line(state, ":wave 2")
        type_code(state, "b = 1")
        handle_line(state, ":wave 1")
        self.assertEqual(handle_line(state, ":undo"), "There is nothing to undo.")
        self.assertEqual(code_of(state, 2), "b = 1\n")


class TestEditInsertDelete(unittest.TestCase):
    """:edit, :ins and :del, with the new text on the same line."""

    def setUp(self):
        """Three lines of code on wave 2."""
        self.state = new_game()
        handle_line(self.state, ":wave 2")
        type_code(self.state, "a = 1\nb = 2\nc = 3")

    def test_edit_replaces_a_line(self):
        """:edit 2 text."""
        handle_line(self.state, ":edit 2 b = 20")
        self.assertEqual(code_of(self.state), "a = 1\nb = 20\nc = 3\n")

    def test_edit_keeps_the_indentation_after_the_first_space(self):
        """Four spaces of indentation need five spaces after the number."""
        handle_line(self.state, ":edit 2     b = 20")
        self.assertEqual(code_of(self.state), "a = 1\n    b = 20\nc = 3\n")

    def test_edit_can_fix_a_blank_in_the_starter(self):
        """The fill-in wave: replace the line that has ___."""
        state = new_game()
        handle_line(state, ':edit 1 print("SNEK ONLINE")')
        self.assertEqual(code_of(state), 'print("SNEK ONLINE")\n')

    def test_ins_puts_a_line_before_n(self):
        """:ins 2 text."""
        handle_line(self.state, ":ins 2 x = 0")
        self.assertEqual(code_of(self.state), "a = 1\nx = 0\nb = 2\nc = 3\n")

    def test_ins_after_the_last_line_adds_at_the_end(self):
        """n = number of lines + 1."""
        handle_line(self.state, ":ins 4 d = 4")
        self.assertEqual(code_of(self.state), "a = 1\nb = 2\nc = 3\nd = 4\n")

    def test_del_removes_a_line(self):
        """:del 2."""
        handle_line(self.state, ":del 2")
        self.assertEqual(code_of(self.state), "a = 1\nc = 3\n")

    def test_changes_can_be_undone(self):
        """Every change is one undo step."""
        handle_line(self.state, ":del 1")
        handle_line(self.state, ":undo")
        self.assertEqual(code_of(self.state), "a = 1\nb = 2\nc = 3\n")

    def test_line_numbers_out_of_range(self):
        """A message that says how many lines there are, and nothing changes."""
        for command in [":edit 9 x", ":del 0", ":ins 9 x", ":edit 4 x"]:
            with self.subTest(command=command):
                self.assertIn("Your code has 3 lines", handle_line(self.state, command))
        self.assertEqual(code_of(self.state), "a = 1\nb = 2\nc = 3\n")

    def test_usage_messages(self):
        """Missing or bad numbers say how to type the command."""
        self.assertIn("Usage: :edit", handle_line(self.state, ":edit"))
        self.assertIn("Usage: :edit", handle_line(self.state, ":edit two x"))
        self.assertIn("Usage: :ins", handle_line(self.state, ":ins"))
        self.assertIn("Usage: :del", handle_line(self.state, ":del x"))

    def test_edit_on_an_empty_wave(self):
        """Nothing to edit."""
        state = new_game()
        handle_line(state, ":wave 2")
        self.assertIn("no lines yet", handle_line(state, ":edit 1 x"))


class TestWaves(unittest.TestCase):
    """:wave and :submit move between waves."""

    def test_wave_goes_to_another_wave(self):
        """The screen of that wave is shown."""
        state = new_game()
        text = handle_line(state, ":wave 3")
        self.assertEqual(state.current_wave, 3)
        self.assertIn("WAVE 3 of 3 · DEBUG", text)
        self.assertIn("YOUR ANSWER", text)

    def test_wave_out_of_range(self):
        """Level 1-1 has three waves."""
        state = new_game()
        self.assertIn("waves 1 to 3", handle_line(state, ":wave 4"))
        self.assertEqual(state.current_wave, 1)

    def test_a_passed_wave_moves_on_and_a_failed_one_stays(self):
        """Wave 1 passes with the right line, and the game shows wave 2."""
        state = new_game()
        handle_line(state, ':edit 1 print("a")')
        text = handle_line(state, ":submit")
        self.assertEqual(state.current_wave, 2)
        self.assertIn("WAVE 2 of 3 · BUILD", text if isinstance(text, str) else text[-1])

        type_code(state, 'print("b")')
        text = handle_line(state, ":submit")
        self.assertEqual(state.current_wave, 2)
        self.assertIn("Not yet", text if isinstance(text, str) else text[-1])

    def test_last_wave_ends_code_mode(self):
        """After the last wave passes, the player is back at the prompt for commands."""
        state = new_game()
        handle_line(state, ":wave 3")
        type_code(state, "a")
        text = handle_line(state, ":submit")
        final = text if isinstance(text, str) else text[-1]
        self.assertIn("last wave", final)
        self.assertFalse(state.coding)

    def test_only_the_current_wave_is_graded(self):
        """Wave 2 and 3 are not touched by a submit of wave 1."""
        state = new_game()
        handle_line(state, ':edit 1 print("a")')
        handle_line(state, ":submit")
        progress = state.progress_for(state.levels[0])
        self.assertEqual(progress.wave_attempts, [1, 0, 0])

    def test_empty_code_is_not_graded(self):
        """An empty wave asks for code and records no attempt."""
        state = new_game()
        handle_line(state, ":clear")
        self.assertIn("Your code is empty", handle_line(state, ":submit"))
        self.assertEqual(state.progress_for(state.levels[0]).wave_attempts, [0, 0, 0])


class TestCommandsEverywhere(unittest.TestCase):
    """Commands with a colon work in both modes."""

    def test_colon_commands_work_outside_code_mode(self):
        """:help and :play."""
        state = GameState([make_full_level()])
        self.assertIn("Commands", handle_line(state, ":help"))
        handle_line(state, ":play 1-1")
        self.assertTrue(state.coding)

    def test_help_lists_the_code_commands(self):
        """The player can find :edit and :undo."""
        text = handle_line(new_game(), ":help")
        for name in (":show", ":undo", ":clear", ":edit", ":ins", ":del", ":wave", "submit"):
            self.assertIn(name, text)

    def test_unknown_colon_command(self):
        """Says so, and changes nothing."""
        state = new_game()
        self.assertIn("Unknown command: :dance", handle_line(state, ":dance"))
        self.assertEqual(code_of(state), "print(___)\n")

    def test_code_mode_commands_need_the_colon(self):
        """Outside code mode, plain 'undo' is just an unknown command."""
        state = GameState([make_full_level()])
        self.assertIn("Unknown command: undo", handle_line(state, "undo"))

    def test_code_commands_before_play(self):
        """No level yet."""
        self.assertIn("play <level>", handle_line(GameState([make_full_level()]), ":show"))

    def test_hint_without_a_number_means_this_wave(self):
        """:hint buys the hint for the wave on screen."""
        level = make_full_level()
        level.waves[0].hints = ["nudge", "outline", "partial"]
        state = GameState([level])
        handle_line(state, "play 1-1")
        self.assertIn("nudge", handle_line(state, ":hint"))


class TestBossInCodeMode(unittest.TestCase):
    """A boss has one wave, typed the same way."""

    def test_boss_fight_is_typed_and_submitted(self):
        """Typing the reference solution defeats the boss."""
        state = GameState([make_boss_level()])
        handle_line(state, "play boss-1")
        self.assertTrue(state.coding)
        type_code(state, make_boss_level().waves[0].reference)
        answer = handle_line(state, ":submit")
        self.assertIn("BOSS DEFEATED.", answer[-1])


if __name__ == "__main__":
    unittest.main()
