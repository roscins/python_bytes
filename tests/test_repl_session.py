"""Tests for runner/repl.py and runner/repl_worker.py: the sandbox behind the quick console.

These start the real worker process. One long-lived process keeps the
player's variables from line to line.
"""

import unittest

from runner.repl import ReplSession, classify


class TestClassify(unittest.TestCase):
    """Is a typed line finished, unfinished, or not Python?"""

    def test_complete_lines(self):
        """Statements and expressions."""
        for source in ['print("hi")', "x = 1", "1 + 2", "import math", "[1, 2, 3]"]:
            with self.subTest(source=source):
                self.assertEqual(classify(source), "complete")

    def test_blocks_and_open_brackets_are_incomplete(self):
        """Python wants more lines."""
        for source in ["for i in range(3):", "if x:\n    y = 1", "def f():", 'print("a",', "x = [1,", "class A:"]:
            with self.subTest(source=source):
                self.assertEqual(classify(source), "incomplete")

    def test_a_block_is_complete_after_a_blank_line(self):
        """The blank line ends it."""
        self.assertEqual(classify("for i in range(3):\n    print(i)\n"), "complete")

    def test_not_python(self):
        """Things that cannot be completed by typing more."""
        for source in ["play 1-1", "hello world", "x = = 1", "print(1))", "3x"]:
            with self.subTest(source=source):
                self.assertEqual(classify(source), "invalid")


class TestSession(unittest.TestCase):
    """The worker process."""

    def setUp(self):
        """Start a session; close it when the test ends."""
        self.session = ReplSession(timeout=3)
        self.addCleanup(self.session.close)

    def test_print(self):
        """Output comes back."""
        result = self.session.run('print("hi")')
        self.assertEqual(result.output, "hi\n")
        self.assertEqual(result.error, "")

    def test_an_expression_shows_its_value_like_the_python_console(self):
        """1 + 2 shows 3."""
        self.assertEqual(self.session.run("1 + 2").output, "3\n")

    def test_variables_stay_between_lines(self):
        """That is the point of a console."""
        self.session.run("x = 5")
        self.assertEqual(self.session.run("x * 2").output, "10\n")

    def test_functions_and_blocks(self):
        """A block with a trailing blank line, then a call."""
        self.session.run("def double(n):\n    return n * 2\n")
        self.assertEqual(self.session.run("double(21)").output, "42\n")
        self.assertEqual(self.session.run("for i in range(2):\n    print(i)\n").output, "0\n1\n")

    def test_an_error_is_returned_separately_with_the_repl_file_name(self):
        """stdout and the traceback are not mixed."""
        result = self.session.run("print(unknown_name)")
        self.assertEqual(result.output, "")
        self.assertIn('File "<repl>", line 1', result.error)
        self.assertIn("NameError: name 'unknown_name' is not defined", result.error)

    def test_a_syntax_error_is_an_error_too(self):
        """Not a crash of the worker."""
        result = self.session.run('print("a)')
        self.assertIn("SyntaxError", result.error)
        self.assertEqual(self.session.run("1 + 1").output, "2\n")

    def test_printed_text_before_an_error_is_kept(self):
        """Both parts arrive."""
        result = self.session.run('for i in range(3):\n    print("before", i)\n    1 / 0\n')
        self.assertEqual(result.output, "before 0\n")
        self.assertIn("ZeroDivisionError", result.error)

    def test_unicode_survives(self):
        """Text with accents and emoji."""
        self.assertEqual(self.session.run('print("é ü 😀")').output, "é ü 😀\n")

    def test_input_is_not_available_and_says_why(self):
        """input() would wait for the game's own pipe, so it explains instead."""
        result = self.session.run("input()")
        self.assertIn("input() does not work in the quick console", result.error)

    def test_a_loop_that_never_ends_is_stopped_and_the_console_is_reset(self):
        """After the time limit the process is killed and a new one starts."""
        self.session.run("x = 5")
        slow = ReplSession(timeout=0.5)
        self.addCleanup(slow.close)
        slow.run("x = 5")
        result = slow.run("while True:\n    pass\n")
        self.assertTrue(result.timed_out)
        self.assertTrue(result.was_reset)
        self.assertIn("name 'x' is not defined", slow.run("x").error)
        self.assertEqual(slow.run("1 + 1").output, "2\n")

    def test_exit_closes_the_worker_and_the_next_line_starts_a_new_one(self):
        """exit() is the player's mistake, not ours."""
        self.session.run("x = 1")
        result = self.session.run("exit()")
        self.assertTrue(result.was_reset)
        self.assertEqual(self.session.run('print("back")').output, "back\n")

    def test_huge_output_is_cut(self):
        """A print loop cannot flood the game."""
        result = self.session.run('print("x" * 500000)')
        self.assertLessEqual(len(result.output), 100_000 + 100)
        self.assertTrue(result.output_cut)

    def test_close_ends_the_process(self):
        """No worker is left behind."""
        self.session.run("1")
        process = self.session.process
        self.session.close()
        self.assertIsNotNone(process.poll())
        self.assertIsNone(self.session.process)

    def test_close_without_ever_starting_is_fine(self):
        """The worker starts on the first line."""
        session = ReplSession()
        session.close()

    def test_the_worker_does_not_see_the_games_modules(self):
        """It runs isolated: the player's code cannot import the game's own code by accident."""
        result = self.session.run("import engine")
        self.assertIn("ModuleNotFoundError", result.error)


if __name__ == "__main__":
    unittest.main()
