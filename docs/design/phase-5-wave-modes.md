# Phase 5 design: review waves, choice waves and wave data files

Status: **approved**, with key-driven answering and the console lock added.

World 4 needs three engine features. Each gets its own branch and PR, in
this order: choice waves, review waves (reuses the answer sheet), data files.

## Shared: modes, key screens and the answer sheet

`mode` already holds `"predict"`. It gains `"choice"` and `"review"`, allowed
on `fill-in` and `debug` waves. Not on `build` (no code, so no quality score)
and not on bosses (none needs it). Level order stays fill-in, build, debug.

In key mode nothing is typed:

- **Choice:** Up and Down move over the options, Enter picks one and moves to
  the next question; Left and Right change question.
- **Review:** Up and Down move over the code lines, Space marks the line and
  opens the category list, Enter picks a category. Space on a marked line
  removes the mark.
- Ctrl-S submits, and the buttons work as in other waves.

In `--plain` and line mode the player types an **answer sheet** (`1: b`, or
`4: a`). The key screens write the same sheet as the wave's saved text, so
grading and saving are shared.

- A wave of either mode has `wrong` (a sheet that must not pass). The right
  sheet is built from the key, so it is never written twice.
- Run is refused ("nothing to run here").
- A choice wave about code behaviour locks the console and power-ups like a
  predict wave: any question with `code`, or `lock = true` on the wave. Other
  choice waves and review waves do not lock.
- Failed submits say how many answers are right, not which letter is correct.
- After the third failed submit the key and explanations are shown and the
  wave is done, as for predict. This stops letter-by-letter guessing.
- New module `grader/answer_sheet.py` parses and grades both sheets. A line
  it cannot read is reported and the submit does not count as an attempt.
- `check_level.py`, the level limits and the progression checker learn both
  modes. Code shown to the player must follow the construct rule.

## 1. Choice waves (`mode = "choice"`)

```toml
[[wave]]
kind = "debug"
mode = "choice"
goal = "Pick the structure for each job."
brief = "Write one letter after each number."
wrong = "1: a\n2: a"

[[wave.question]]
ask = "Part names in delivery order, repeats kept."
options = ["list", "set", "dict"]
answer = "a"
explanation = "A list keeps order and repeats."
```

- 1 to 6 questions, 2 to 5 options each, lettered a, b, c in file order.
- A question may have `code = '''...'''`, shown above its options.
- One correct letter per question. Multi-select is left out until needed.
- The editor starts as `1: `, `2: ` and so on.
- One check per question, so the score is the share answered right.

## 2. Review waves (`mode = "review"`)

```toml
[[wave]]
kind = "debug"
mode = "review"
goal = "Mark the 2 faulty lines and name each fault."
brief = "For each fault write: line number, colon, category letter."
code = '''...'''
categories = ["wrong boundary", "unclear name", "missing check"]
wrong = "1: a\n2: a"

[[wave.fault]]
line = 4
category = "a"
explanation = "< leaves out the limit itself."
```

- The code is shown with line numbers. A sheet line is `4: a`.
- 1 to 4 faults, 2 to 5 categories, one fault per line, at most 30 code lines.
- The player may mark **at most as many lines as there are faults**. A longer
  sheet is not graded, so marking every line cannot score.
- Two checks per fault: the line is marked, and its category is right.
- Check names do not give line numbers away ("finds fault 1").

## 3. Wave data files

```
levels/w4/4-3-the-archive/
    level.toml
    files/sensors.csv
    files/sensors-b.csv
```

```toml
[[wave]]
files = ["sensors.csv"]

[[wave.test]]
expected_stdout = "..."
files = { "sensors.csv" = "sensors-b.csv" }   # hidden dataset

[[wave.test]]
expected_file = { name = "summary.txt", contents = "..." }
```

- `files` lists what the wave's code can open, by plain name. A boss wave may
  use it too.
- Every run (Run, and each test) gets a **fresh temporary folder** with
  copies of those files. The originals are never touched.
- A test's `files` puts another file under the same name, so printing the
  expected text cannot pass. Use at least two datasets per graded program.
- `expected_file` is a new test kind: after the run, that file must hold
  `contents` (spaces at line ends and final blank lines ignored, as for
  stdout). It may also have `files` and `stdin`.
- Names must be plain file names (no folders, no `..`, not `.py`), the files
  must exist, be UTF-8 and at most 100 KB. The loader checks this.
- The player reads a data file with a new command, `show sensors.csv`. After
  Run, the panel also shows the files the program wrote (first 20 lines).
- The console and power-ups get a copy in their own folder; `:where` exports
  the files next to the code.
- "Sandbox" means a throwaway working folder. It is **not** a security
  boundary: player code can still reach other paths, as it can today.
- Code: `runner/process.py` (copy in, read back), `grader/checks.py`,
  `engine/level_pack.py`, console, commands, level style guide.

## Boss 4

One timed `boss` wave: a single-file sensor-warning project that reads data
files, writes a report and includes assert tests. No phases and no review
part. B12 is therefore tested only by 4-4.

## Tests

Each PR adds unittests for loading and rejecting bad level files, grading
(including the cheats above), the editor and line-mode flow, and the checker.
