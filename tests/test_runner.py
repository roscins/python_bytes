"""Tests for runner/process.py and runner/__main__.py."""

import io
import os
import unittest
from contextlib import redirect_stdout

from runner import __main__ as runner_main
from runner.process import MAX_OUTPUT_CHARACTERS, RunResult, run_code, run_files
from tests.helpers import write_temporary_file


class TestRunCode(unittest.TestCase):
    """Check that player code runs in its own process and its output is caught."""

    def test_output_is_captured(self):
        """What the program prints comes back in stdout."""
        result = run_code('print("SNEK ONLINE")')
        self.assertEqual(result.stdout, "SNEK ONLINE\n")
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)
        self.assertTrue(result.finished_cleanly())

    def test_fake_input_is_read_by_input(self):
        """stdin_text is read by input() as if it were typed."""
        code = 'name = input()\nbattery = input()\nprint(name, battery)'
        result = run_code(code, stdin_text="Snek\n12\n")
        self.assertEqual(result.stdout, "Snek 12\n")

    def test_running_out_of_input_is_an_eof_error(self):
        """input() with no input left raises EOFError, as Ctrl-D would."""
        result = run_code("input()\ninput()", stdin_text="only one line\n")
        self.assertIn("EOFError", result.error_line())

    def test_infinite_loop_is_stopped(self):
        """A loop that never ends is stopped by the time limit."""
        result = run_code('print("START", flush=True)\nwhile True:\n    pass', time_limit=0.5)
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)
        self.assertFalse(result.finished_cleanly())
        self.assertEqual(result.error_line(), "")
        self.assertIn("START", result.stdout)

    def test_crash_gives_the_error_line(self):
        """A crash gives a non-zero exit code and the traceback's last line."""
        result = run_code("print(SNEK)")
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(result.finished_cleanly())
        self.assertEqual(result.error_line(), "NameError: name 'SNEK' is not defined")

    def test_syntax_error_gives_the_error_line(self):
        """Code that is not valid Python reports a SyntaxError."""
        result = run_code("print(SNEK ONLINE)")
        self.assertTrue(result.error_line().startswith("SyntaxError"))

    def test_traceback_has_short_file_names(self):
        """The traceback says main.py, not the temporary folder's path."""
        result = run_code("x = 1\nprint(y)")
        self.assertIn('File "main.py", line 2', result.stderr)
        self.assertNotIn("tmp", result.stderr)

    def test_unicode_output(self):
        """Characters outside ASCII are printed and read correctly."""
        result = run_code('print("★ Snek ♥")')
        self.assertEqual(result.stdout, "★ Snek ♥\n")

    def test_program_runs_in_its_own_folder(self):
        """The program does not run in the game's folder."""
        result = run_code("import os\nprint(os.getcwd())")
        self.assertNotEqual(result.stdout.strip(), os.getcwd())

    def test_temporary_folder_is_deleted(self):
        """The folder the program ran in is gone afterwards."""
        result = run_code("import os\nprint(os.getcwd())")
        self.assertFalse(os.path.exists(result.stdout.strip()))

    def test_game_modules_cannot_be_imported(self):
        """Isolated mode: the player's code cannot see the game's modules."""
        result = run_code("import engine")
        self.assertIn("ModuleNotFoundError", result.error_line())

    def test_very_long_output_is_cut(self):
        """Output longer than the limit is cut off and marked as cut."""
        result = run_code(f'print("x" * {MAX_OUTPUT_CHARACTERS + 10})')
        self.assertEqual(len(result.stdout), MAX_OUTPUT_CHARACTERS)
        self.assertTrue(result.output_cut)


class TestRunFiles(unittest.TestCase):
    """Check running a program made of several files."""

    def test_main_file_can_read_the_other_files(self):
        """Every file is written to the same folder before the program runs."""
        files = {
            "main.py": 'print(open("data.txt").read())',
            "data.txt": "BATTERY 12",
        }
        result = run_files(files, "main.py")
        self.assertEqual(result.stdout, "BATTERY 12\n")


class TestRunResult(unittest.TestCase):
    """Check the helper methods of RunResult."""

    def test_error_line_is_empty_without_an_error(self):
        """A program that ended normally has no error line, even with stderr text."""
        result = RunResult("", "a warning\n", 0)
        self.assertEqual(result.error_line(), "")

    def test_error_line_with_empty_stderr(self):
        """A crash with nothing in stderr gives an empty error line."""
        self.assertEqual(RunResult("", "", 1).error_line(), "")


class TestRunnerMain(unittest.TestCase):
    """Check python -m runner, the tool for trying the runner by hand."""

    def run_main(self, arguments):
        """Run runner_main.main and return its exit code and printed text."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = runner_main.main(arguments)
        return exit_code, output.getvalue()

    def test_runs_a_file_with_input(self):
        """The file runs, the input is used, and the output is shown."""
        path = write_temporary_file(self, "print(input().upper())", suffix=".py")
        exit_code, text = self.run_main([path, "snek\\n"])
        self.assertEqual(exit_code, 0)
        self.assertIn("SNEK", text)
        self.assertIn("finished without errors", text)

    def test_reports_a_crash(self):
        """A crash is reported with its traceback."""
        path = write_temporary_file(self, "print(1 / 0)", suffix=".py")
        exit_code, text = self.run_main([path])
        self.assertIn("ZeroDivisionError", text)

    def test_missing_file(self):
        """A file that does not exist gives a message and exit code 2."""
        exit_code, text = self.run_main(["no-such-file.py"])
        self.assertEqual(exit_code, 2)
        self.assertIn("There is no file", text)

    def test_usage(self):
        """No arguments gives the usage line."""
        exit_code, text = self.run_main([])
        self.assertEqual(exit_code, 2)
        self.assertIn("Usage", text)


if __name__ == "__main__":
    unittest.main()
