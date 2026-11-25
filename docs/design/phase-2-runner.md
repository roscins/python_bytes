# Phase 2 design: run player code in a separate process

Roadmap checkbox (docs/plan.md, Phase 2): "Run player code in a separate
process with a time limit and fake input". Approved before coding, on branch
`phase-2/runner`. The other Phase 2 branches (grader, scoring, screens) are
stacked on top of this one.

## Files

- `runner/process.py`:
  - `RunResult`: a plain class with `stdout`, `stderr`, `exit_code`,
    `timed_out` and `output_cut`, plus:
    - `finished_cleanly()`: True when the program ended by itself with exit
      code 0
    - `error_line()`: the last line of the traceback, for example
      `NameError: name 'SNEK' is not defined`, or `""` if there was no error
  - `run_files(files, main_file, stdin_text="", time_limit=2.0)` writes
    each file (a dict from file name to text) into a new temporary folder
    and runs `main_file` there. The grader needs more than one file for
    function tests (the player's code plus a small script that calls it),
    and Phase 6 needs folders of starter files.
  - `run_code(code, stdin_text="", time_limit=2.0)` is the common case:
    one file, `main.py`.
- `runner/__main__.py`: `python -m runner <file.py> [input text]` runs a file
  the way the game will and prints the result, for trying the runner by hand.
- `tests/test_runner.py`.
- `docs/plan.md`: tick the three Phase 1 boxes that were merged in #8–#10.

## How a program is run

- With `subprocess.run([sys.executable, "-I", "-X", "utf8", "main.py"])`,
  in the temporary folder, so the player's files never mix with the game's.
- `-I` (isolated mode) means the player's program does not see the game's
  folder or the player's environment variables. A file the player calls
  `json.py` cannot break the game, and the game's modules cannot be
  imported by accident.
- `-X utf8` makes the program read and write UTF-8 on every system, so
  `print("★")` works on Windows too. `-I` ignores `PYTHONIOENCODING`, so
  the flag is needed.
- **Fake input**: `stdin_text` is sent to the program as if typed. When it
  runs out, `input()` raises `EOFError`, as it does in a real terminal on
  Ctrl-D.
- **Time limit**: after `time_limit` seconds (2 by default) the program is
  stopped. `timed_out` is True and the output printed so far is kept.
- **Output limit**: at most 100 000 characters of output are kept; the rest
  is cut off and `output_cut` is True, so a runaway `print` loop cannot
  flood the screen.
- **Tracebacks are shortened**: the temporary folder's path is removed, so
  the player sees `File "main.py", line 3` instead of a long `/tmp/...`
  path.
- The temporary folder is deleted afterwards, also when the program crashes
  or times out.

## Decisions

- **Not a security sandbox.** As the plan says, the runner protects against
  infinite loops and crashes, not against harmful code: players run their
  own code on their own machine.
- **Plain class, not a dataclass**, like the rest of the code.
- **2 seconds** is generous for every task in Worlds 1–4; a level can ask
  for a different limit later if one needs it.
