"""Run a player's code in a separate Python process.

The game never runs player code inside itself. Each program runs as its own
process, in its own temporary folder, with:

- a time limit, so a loop that never ends cannot freeze the game;
- fake input, so a program that calls input() can be tested without anyone
  typing;
- its output captured, so the grader can compare it with what was expected.

This protects the game against mistakes like infinite loops and crashes. It
is not a security sandbox: players run their own code on their own machine.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# How many seconds a program may run before it is stopped.
DEFAULT_TIME_LIMIT = 2.0

# How many characters of output are kept. A program that prints in a loop
# that never ends could print millions of lines; the rest is cut off.
MAX_OUTPUT_CHARACTERS = 100_000

# The file name the player's code gets when only one file is run.
MAIN_FILE = "main.py"


class RunResult:
    """What happened when a program ran.

    Attributes:
        stdout: everything the program printed.
        stderr: the error messages it wrote, for example a traceback.
        exit_code: 0 when the program ended normally, another number when it
            crashed, or None when it was stopped by the time limit.
        timed_out: True if the program was stopped by the time limit.
        output_cut: True if stdout or stderr was too long and was cut off.
    """

    def __init__(self, stdout, stderr, exit_code, timed_out=False, output_cut=False):
        """Remember every part of the result."""
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.output_cut = output_cut

    def finished_cleanly(self):
        """Return True if the program ended by itself, without an error."""
        return not self.timed_out and self.exit_code == 0

    def error_line(self):
        """Return the last line of the error message, or "" if there was no error.

        The last line of a Python traceback names the error, for example
        "NameError: name 'SNEK' is not defined", which is what a player needs
        to see first.
        """
        if self.exit_code == 0 or self.exit_code is None:
            return ""
        lines = self.stderr.strip().splitlines()
        if not lines:
            return ""
        return lines[-1]


    def error_line_number(self):
        """Return the line of the player's code where the error happened, or None.

        It is the last "File "main.py", line N" in the traceback.
        """
        found = None
        for match in re.finditer(r'File "(?:main|player)\.py", line (\d+)', self.stderr):
            found = int(match.group(1))
        return found


def as_text(output):
    """Return `output` as a string.

    When a program is stopped by the time limit, the output printed so far
    can come back as bytes instead of text, or as None if there was none.
    """
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def cut_output(text):
    """Return `text` cut to MAX_OUTPUT_CHARACTERS, and whether it was cut."""
    if len(text) <= MAX_OUTPUT_CHARACTERS:
        return text, False
    return text[:MAX_OUTPUT_CHARACTERS], True


def shorten_paths(text, folder):
    """Remove the temporary folder's path from `text`.

    A traceback then says File "main.py" instead of a long path like
    File "/tmp/tmpab12cd/main.py", which means nothing to the player.
    """
    return text.replace(str(folder) + "/", "").replace(str(folder) + "\\", "")


def run_files(files, main_file, stdin_text="", time_limit=DEFAULT_TIME_LIMIT):
    """Write `files` into a new temporary folder, run `main_file` there, return a RunResult.

    `files` is a dict from file name to the file's text, for example
    {"main.py": 'print("HI")'}. `stdin_text` is sent to the program as if
    it were typed. The folder is deleted afterwards.
    """
    with tempfile.TemporaryDirectory() as folder_name:
        folder = Path(folder_name)
        for name in files:
            (folder / name).write_text(files[name], encoding="utf-8")

        # -I (isolated mode): the program does not see the game's folder or
        # the player's environment variables.
        # -X utf8: the program reads and writes UTF-8 on every system.
        command = [sys.executable, "-I", "-X", "utf8", main_file]
        try:
            finished = subprocess.run(
                command,
                cwd=folder,
                input=stdin_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=time_limit,
            )
            stdout = finished.stdout
            stderr = finished.stderr
            exit_code = finished.returncode
            timed_out = False
        except subprocess.TimeoutExpired as stopped:
            # subprocess.run has already stopped the program; keep what it
            # printed before that.
            stdout = as_text(stopped.stdout)
            stderr = as_text(stopped.stderr)
            exit_code = None
            timed_out = True

        stdout, stdout_cut = cut_output(stdout)
        stderr, stderr_cut = cut_output(shorten_paths(stderr, folder))
        return RunResult(stdout, stderr, exit_code, timed_out, stdout_cut or stderr_cut)


def run_code(code, stdin_text="", time_limit=DEFAULT_TIME_LIMIT):
    """Run one piece of code as main.py and return a RunResult."""
    return run_files({MAIN_FILE: code}, MAIN_FILE, stdin_text, time_limit)
