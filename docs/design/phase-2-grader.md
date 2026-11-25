# Phase 2 design: the grader, the workspace and submit

Roadmap checkbox (docs/plan.md, Phase 2): "Output tests, function tests, AST
rules ("must use a for loop") and style rules". Approved before coding, on
branch `phase-2/grader` (built on `phase-2/runner`, which it uses).

## The kinds of test

Each `[[wave.test]]` table has exactly one of these keys, which says what
kind of test it is:

| Key | Example | Passes when |
| --- | --- | --- |
| `expected_stdout` | `expected_stdout = "SNEK ONLINE\n"` | the program prints exactly this |
| `expected_stdout_contains` | `expected_stdout_contains = ["Battery: 10 %"]` | every piece of text appears in the output |
| `call` | `call = "celsius_to_kelvin"`, `args = [0]`, `expected = 273.15` | the function returns `expected` |
| `require` | `require = ["While"]` | the code uses every one of these Python constructs |
| `forbid` | `forbid = ["For"]` | the code uses none of them |
| `require_comment` | `require_comment = true` | the code has at least one `#` comment |

- `stdin = "..."` can go with the first three, as fake input.
- `require` and `forbid` name Python's own AST node types (`For`, `While`,
  `If`, `Call`, `FunctionDef`, …), as in the plan's level-pack example. The
  player is shown a friendly name, for example "a while loop".
- Output is compared without spaces at the ends of lines and without blank
  lines at the end, so an invisible trailing space never fails a player.
  Everything else must match exactly.
- In a function test, numbers with a decimal point match when they are
  equal to 9 decimal places (`0.1 + 0.2` matches `0.3`), and a returned
  tuple matches a TOML list, because TOML has no tuples.

## Files

- `grader/checks.py`:
  - `CheckResult`: `passed`, `name` (what was tested, for example
    `prints the right output`) and `message` (why it failed, or `""`)
  - one function per kind of test, and `run_check(test, code)` that picks
    the right one
  - function tests run the player's code as `player.py` next to a small
    generated `call_function.py`, which loads it, calls the function and
    prints the result as JSON on a marked line (`run_files` from the
    runner)
- `grader/style.py`: the code-quality rules, each giving a `CheckResult`:
  1. names are snake_case (variables, functions and arguments), or
     UPPER_CASE for constants; class names are CapWords
  2. indents are 4 spaces, never tabs
  3. the code has at least one comment
  4. every function and class has a docstring (this first matters in 3-2,
     the first level with `def`)
  Code that Python cannot read fails every rule.
- `grader/wave_grader.py`:
  - `WaveResult`: `checks` (list of `CheckResult`), `quality` (list of
    `CheckResult`, only for build waves), and `passed_count()`,
    `test_count()`, `all_passed()`, `share_passed()`,
    `quality_share()`
  - `grade_wave(wave, text)`:
    - predict waves: one check, the player's answer against `answer`
    - fill-in waves: if the code still has a `___` blank, one failed check
      ("fill in every blank") and nothing is run
    - otherwise every test of the wave, plus the style rules for build
      waves
  - `normalise_output(text)`, shared by output tests and predict answers
- `engine/level_pack.py`: the loader checks the tests too: exactly one kind
  key per test, `require`/`forbid` name real AST node types, `call` tests
  have `expected`, `args` is a list.
- `engine/workspace.py`:
  - `WORKSPACE_FOLDER` is `workspace/` in the game folder (gitignored)
  - `wave_file_name(wave, number)`: `wave1.py`, `wave2.py`, and
    `wave3.txt` for a predict wave (the answer is text, not code)
  - `prepare_workspace(level, root)` makes `workspace/<level>/` and writes
    each wave file that does not exist yet: the starter code for fill-in
    and fix-the-bug waves, an empty file otherwise. A file that is there is
    never overwritten, so replaying never loses the player's work.
  - `read_wave_file(level, number, root)`: the file's text, or `None`
- `engine/game_state.py`: `GameState(levels, workspace_root=None)`. With
  `None` (most tests) there is no workspace: `play` writes no files.
- `engine/commands.py`:
  - `play` prepares the workspace and ends with
    `Your files are in <path>. Write your code there, then type submit.`
  - `submit` grades every wave file and shows, for each wave,
    `WAVE 1 · FILL-IN  2/2 tests passed`, the failed checks with their
    messages, and for the build wave `Code quality 3/4` with the failed
    rules. A wave without a file says which file to write.
  - new `where` command: the full path of the current level's workspace
- `engine/level_screen.py`: the line "Grading arrives in a later version"
  goes; the wave numbers say which file each wave goes in.
- `engine/__main__.py`: `main(levels_folder, save_path, workspace_root)`,
  with the real `workspace/` by default.
- `.gitignore`: `workspace/`.
- Tests: `tests/test_checks.py`, `tests/test_style.py`,
  `tests/test_wave_grader.py`, `tests/test_workspace.py`, plus updates to
  the loader, command and main tests.
- **Gate test** in `tests/test_levels.py`: for every real level, each
  wave's reference solution passes every test (and gets full code quality
  in build waves), and each wrong solution fails at least one test.

## Decisions

- **Scores, stars and XP are the next branch.** Here `submit` only reports
  which tests passed.
- **Own style rules only**, with `ast` and `tokenize`; no pycodestyle (no
  dependencies). Comments are found with `tokenize`, because the AST
  leaves them out.
- **The player never sees the hidden tests' expected values for `call`
  tests that pass**; a failed test says what was expected and what came
  back, so the player can fix it.
- **The build wave's file starts empty**, not with the brief as a comment,
  because a comment there would pass "add a comment" for free.
