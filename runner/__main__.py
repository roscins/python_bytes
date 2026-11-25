"""Try the runner by hand: python -m runner <file.py> [input text]

The file is run the way the game runs a player's code: in a separate
process, in a temporary folder, with a time limit. The input text is sent
as if it were typed; write \\n for a new line, for example:

    python -m runner workspace/1-1/wave2.py "Snek\\n12\\n"
"""

import sys
from pathlib import Path

from runner.process import DEFAULT_TIME_LIMIT, run_code


def describe(result):
    """Return a short report of a RunResult, as lines of text."""
    lines = ["--- output ---", result.stdout.rstrip("\n"), "--- end of output ---"]
    if result.timed_out:
        lines.append(f"Stopped: the program ran for more than {DEFAULT_TIME_LIMIT} seconds.")
    elif result.exit_code == 0:
        lines.append("The program finished without errors.")
    else:
        lines.append(f"The program stopped with an error (exit code {result.exit_code}):")
        lines.append(result.stderr.rstrip("\n"))
    if result.output_cut:
        lines.append("The output was too long and was cut off.")
    return lines


def main(arguments):
    """Run the file named in `arguments` and print what happened. Returns an exit code."""
    if len(arguments) not in (1, 2):
        print("Usage: python -m runner <file.py> [input text]")
        return 2
    path = Path(arguments[0])
    if not path.is_file():
        print(f"There is no file {path}.")
        return 2
    stdin_text = ""
    if len(arguments) == 2:
        # On the command line a new line is written as \n; turn it into a real one.
        stdin_text = arguments[1].replace("\\n", "\n")
    result = run_code(path.read_text(encoding="utf-8"), stdin_text)
    for line in describe(result):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
