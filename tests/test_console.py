"""Tests for engine/console.py: the quick console outside waves, :run, and the prompts that ask for more.

The console uses the real worker process (one per game), closed after each test.
"""

import unittest

from engine.code_mode import prompt_for
from engine.commands import handle_line
from engine.game_state import GameState
from tests.helpers import make_full_level, type_code


def new_state(color=False):
    """Return a game with Level 1-1 that closes its console when the test ends (see the test's addCleanup)."""
    state = GameState([make_full_level()])
    state.plain = True
    state.color = color
    return state


class ConsoleTestCase(unittest.TestCase):
    """Base class: every test gets a state whose console is closed afterwards."""

    def setUp(self):
        """A game, not yet playing."""
        self.state = new_state()
        self.addCleanup(self.state.close)

    def type(self, *lines):
        """Type lines; return the answers joined (empty answers left out)."""
        answers = []
        for line in lines:
            answer = handle_line(self.state, line)
            if isinstance(answer, list):
                answer = answer[-1]
            if answer:
                answers.append(answer)
        return "\n".join(answers)


class TestQuickConsole(ConsoleTestCase):
    """Python typed at the prompt, outside a wave."""

    def test_print_just_works(self):
        """The line from the brief."""
        self.assertEqual(self.type('print("hi")'), "hi")

    def test_variables_stay(self):
        """x = 2, then x * 3."""
        self.assertEqual(self.type("x = 2", "x * 3"), "6")

    def test_commands_win_over_python(self):
        """help is the command, not the Python help function."""
        self.assertIn("Commands", self.type("help"))

    def test_a_block_needs_a_blank_line_and_shows_the_continuation_prompt(self):
        """for ...: then the body, then Enter on an empty line."""
        self.assertEqual(self.type("for i in range(2):"), "")
        self.assertEqual(prompt_for(self.state), "... ")
        self.assertEqual(self.type("    print(i)", ""), "0\n1")
        self.assertEqual(prompt_for(self.state), "> ")

    def test_an_open_bracket_continues_on_the_next_line(self):
        """print( ... split over two lines."""
        self.type('print("a",')
        self.assertEqual(prompt_for(self.state), "... ")
        self.assertEqual(self.type('"b")', ""), "a b")

    def test_a_typo_in_a_command_is_still_unknown_command(self):
        """plya 1-1 is not Python, and neither is plya on its own."""
        self.assertIn("Unknown command: plya", self.type("plya 1-1"))
        self.assertIn("Unknown command: plya", self.type("plya"))

    def test_an_error_is_friendly_with_the_line_and_the_real_error(self):
        """1 / 0."""
        text = self.type("1 / 0")
        self.assertIn("Snek tripped on line 1: you divided by zero.", text)
        self.assertIn("  1 | 1 / 0", text)
        self.assertIn("ZeroDivisionError: division by zero", text)

    def test_a_name_error_for_a_name_with_more_to_it_is_a_python_error(self):
        """print(zzz) is Python, not a command."""
        self.assertIn('Text needs quotes: try print("zzz")', self.type("print(zzz)"))

    def test_a_line_that_looks_like_python_but_is_not_gets_a_friendly_syntax_error(self):
        """print("a) is a mistake in Python, not a mistyped command."""
        text = self.type('print("a)')
        self.assertIn("Snek tripped on line 1: a quote is missing.", text)
        self.assertNotIn("Unknown command", text)

    def test_a_line_with_no_python_signs_is_an_unknown_command(self):
        """Words and numbers only: more likely a typo of a command."""
        self.assertIn("Unknown command: hello", self.type("hello world"))

    def test_a_colon_command_cancels_a_half_typed_block(self):
        """Typing :map in the middle of a block leaves it."""
        self.type("for i in range(2):")
        text = self.type(":map")
        self.assertIn("WORLD 1", text)
        self.assertIsNone(self.state.pending)

    def test_cancel(self):
        """:cancel leaves the block."""
        self.type("for i in range(2):")
        self.assertEqual(self.type(":cancel"), "Cancelled.")
        self.assertEqual(prompt_for(self.state), "> ")
        self.assertEqual(self.type(":cancel"), "Nothing to cancel.")

    def test_inside_a_wave_the_same_line_is_code_not_python(self):
        """Typed during code mode, print("hi") only goes into the code."""
        self.type("play 1-1")
        self.type(":clear")
        self.assertEqual(self.type('print("hi")'), "")
        self.assertIn('print("hi")', self.state.wave_text(self.state.levels[0], 1))

    def test_the_console_survives_going_into_and_out_of_a_wave(self):
        """Variables are kept."""
        self.type("x = 7")
        self.type("play 1-1", ":map")
        self.assertEqual(self.type("x"), "7")

    def test_a_loop_that_never_ends_resets_the_console_and_says_so(self):
        """After the time limit."""
        self.state.repl_timeout = 0.5
        self.type("x = 1")
        text = self.type("while True:", "    pass", "")
        self.assertIn("never ends", text)
        self.assertIn("variables are gone", text)

    def test_close_ends_the_worker(self):
        """GameState.close()."""
        self.type("1")
        process = self.state.repl.process
        self.state.close()
        self.assertIsNotNone(process.poll())


class TestPendingEdit(ConsoleTestCase):
    """:edit and :ins with no text ask for it."""

    def setUp(self):
        """Wave 2 with three lines."""
        super().setUp()
        self.type("play 1-1", ":wave 2")
        type_code(self.state, "a = 1\nb = 2\nc = 3")

    def code(self):
        """The code of wave 2."""
        return self.state.wave_text(self.state.levels[0], 2)

    def test_edit_without_text_shows_the_old_line_and_asks(self):
        """The prompt becomes the line number."""
        text = self.type(":edit 2")
        self.assertIn("b = 2", text)
        self.assertEqual(prompt_for(self.state), "  2 | ")

    def test_the_next_line_replaces_it(self):
        """Typed text, then back to normal."""
        self.type(":edit 2")
        self.type("b = 20")
        self.assertEqual(self.code(), "a = 1\nb = 20\nc = 3\n")
        self.assertEqual(prompt_for(self.state), "  4 | ")

    def test_an_empty_line_keeps_the_old_line(self):
        """Enter alone cancels."""
        self.type(":edit 2")
        self.assertIn("Kept", self.type(""))
        self.assertEqual(self.code(), "a = 1\nb = 2\nc = 3\n")

    def test_ins_without_text_asks_for_the_new_line(self):
        """The new line goes before n."""
        self.type(":ins 2")
        self.type("x = 0")
        self.assertEqual(self.code(), "a = 1\nx = 0\nb = 2\nc = 3\n")

    def test_the_indentation_typed_is_kept(self):
        """Four spaces stay four spaces."""
        self.type(":edit 2")
        self.type("    b = 20")
        self.assertEqual(self.code(), "a = 1\n    b = 20\nc = 3\n")

    def test_a_colon_command_leaves_the_edit(self):
        """:show instead of text."""
        self.type(":edit 2")
        self.type(":show")
        self.assertIsNone(self.state.pending)
        self.assertEqual(self.code(), "a = 1\nb = 2\nc = 3\n")

    def test_edit_of_a_line_that_does_not_exist_asks_nothing(self):
        """An error, no pending."""
        self.assertIn("Your code has 3 lines", self.type(":edit 9"))
        self.assertIsNone(self.state.pending)


class TestRun(ConsoleTestCase):
    """:run tries the code without grading it."""

    def setUp(self):
        """Playing wave 2 (a build wave)."""
        super().setUp()
        self.type("play 1-1", ":wave 2")

    def test_run_shows_the_output_and_does_not_grade(self):
        """No attempt is recorded."""
        type_code(self.state, 'print("hi")')
        text = self.type(":run")
        self.assertIn("hi", text)
        self.assertEqual(self.state.progress_for(self.state.levels[0]).wave_attempts, [0, 0, 0])

    def test_run_with_no_output(self):
        """Says so."""
        type_code(self.state, "x = 1")
        self.assertIn("(no output)", self.type(":run"))

    def test_run_of_empty_code(self):
        """Nothing to run."""
        self.assertIn("empty", self.type(":run"))

    def test_run_shows_a_friendly_error_with_the_players_line(self):
        """The line number is the number on the screen."""
        type_code(self.state, 'x = 1\nprint(x + y)')
        text = self.type(":run")
        self.assertIn("Snek tripped on line 2: I do not know the name y", text)
        self.assertIn("  2 | print(x + y)", text)

    def test_run_that_never_ends(self):
        """The time limit."""
        type_code(self.state, "while True:\n    pass")
        self.assertIn("never ends", self.type(":run"))

    def test_run_refuses_a_leftover_blank(self):
        """The ___ of a fill-in."""
        self.type(":wave 1")
        self.assertIn("blank", self.type(":run"))

    def test_run_for_a_predict_wave_does_not_tell_the_answer(self):
        """Snek will not tell you."""
        self.type(":wave 3")
        self.assertIn("will not tell", self.type(":run"))

    def test_run_asks_for_input_when_the_code_reads_it(self):
        """The player types the lines, an empty line starts the program."""
        type_code(self.state, 'name = input()\nprint("Hello, " + name)')
        text = self.type(":run")
        self.assertIn("asks for input", text)
        self.assertEqual(prompt_for(self.state), "input 1 > ")
        self.type("Snek")
        self.assertEqual(prompt_for(self.state), "input 2 > ")
        self.assertIn("Hello, Snek", self.type(""))
        self.assertIsNone(self.state.pending)

    def test_run_with_too_little_input_says_so(self):
        """The program wants more than was typed."""
        type_code(self.state, "a = input()\nb = input()")
        self.type(":run")
        self.type("one")
        text = self.type("")
        self.assertIn("asked for input, but there was none", text)

    def test_run_outside_a_wave(self):
        """No level."""
        state = new_state()
        self.addCleanup(state.close)
        self.assertIn("play <level>", handle_line(state, ":run"))


class TestHelp(ConsoleTestCase):
    """The player can find the new commands."""

    def test_help_lists_run_and_cancel(self):
        """:run and :cancel."""
        text = self.type(":help")
        self.assertIn(":run", text)
        self.assertIn(":cancel", text)


if __name__ == "__main__":
    unittest.main()
