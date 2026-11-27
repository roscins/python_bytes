# Level style guide

Every level in Python Bytes follows this guide. If a level breaks a rule, the pull request is not merged.

## Folder and file naming

```
levels/w<world>/<level-id>-<short-name>/level.toml
```

Examples: `levels/w1/1-1-hello-terminal/level.toml`, `levels/w2/2-3-charging/level.toml`.
Bosses: `levels/w1/boss-1-corrupted-bootloader/level.toml`. The last boss is `boss-8`, in `levels/w8/`.

## Required parts of a level

| Part | What it is | Limit |
| --- | --- | --- |
| `[level]` | id, title, world, new concepts, power-up | 2–4 new concepts, the same as `concepts` of this level in `levels/concepts.toml` |
| `cutscene` | Story scene with working code in it | 25 lines |
| `tips` | One-line explanations of the new syntax (go to the Codex) | 1 tip per new concept |
| Wave 1 `fill-in` | Given code with `___` blanks to complete | 1–3 blanks |
| Wave 2 `build` | Write a program from a short brief, optionally from a `starter` | Brief: 5 sentences |
| Wave 3 `debug` | Predict the output, or find and fix one bug | 10 lines of code; from World 3: up to 3 bugs and 30 lines |
| Tests | At least 2 tests per wave. In a predict-mode debug wave, `answer` and `wrong` count as its tests | – |
| `explanation` (predict waves) | Why the answer is right; shown after 3 wrong guesses | Every predict wave |
| `goal` (every wave) | The task in one line, shown in the GOAL box | 60 characters |
| Reference + wrong solution | One solution that must pass, one typical mistake that must fail | Per wave |
| `hints` (optional) | A nudge, an outline and a partial solution, bought with coins | Exactly 3 per wave |
| `time_limit` (optional, per wave) | Seconds the player's code may run, for missions that time code (Level 8-2) | Runner default if left out |

## Hard rules

1. A level uses only constructs taught in earlier levels, plus its own new concepts. `docs/curriculum.md` and `levels/concepts.toml` decide what each level teaches; never add a construct to a level that is not listed there. The progression checker enforces this (the rules are in section 6 of `docs/curriculum.md`).
2. At most 4 new concepts per level.
3. Everything is in English.
4. Every wave has a reference solution that passes and a wrong solution that fails. A predict-mode debug wave has a right `answer` and a `wrong` answer instead.
5. The cutscene shows the new syntax working **before** the tips explain it.
6. Code in levels follows the style the game grades: snake_case names, 4-space indents, comments where useful.

## Bigger waves from World 3

From World 3, a debug wave may hold up to 3 bugs and 30 lines (3-4 asks the player to fix three aliasing bugs). A build wave may have a `starter`: code the player builds on, for example a long script to split into functions (3-3). Bosses keep their one wave. Before World 3 the limits in the table above apply.

## What is never taught

`global` is never taught, and level code never uses it. A function that changes a variable outside itself cannot be read, tested or reused on its own, and first-year students then learn to fix a bug by adding another global. The player passes values in and returns values out; where a count must survive several calls (the call counter in 4-5), a mutable object such as a list is passed in.

## Checking a level

Two scripts in `tools/` help while writing a level:

- `python tools/level_brief.py 3-2` prints a short brief of one level: story, mission, outcomes, recycled levels and every construct the level may use, with the new ones starred. Paste it into a model's context before writing the level.
- `python tools/check_level.py levels/w1/1-2-memory-cells` checks a level (or several, or all of `levels/` with no argument). It prints `PASS <id>`, or `FAIL <id>` with one line for each problem: the progression rules, the limits in this guide, and the reference and wrong solutions of every wave. A level is not done until it prints `PASS`.

## Kinds of test

Each `[[wave.test]]` table has exactly one of these keys (`expected_file` is under Data files and `catches` under Testing the player's tests, below). Two more: `require_call = ["csv.reader"]` passes when the code calls those names, and `require_plan = 3` when at least 3 comment lines come before the first statement (say so in the brief):

| Key | Passes when |
| --- | --- |
| `expected_stdout = "..."` | the program prints exactly this (spaces at line ends and blank lines at the end are ignored) |
| `expected_stdout_contains = ["...", "..."]` | every piece appears in the output |
| `call = "name"`, `args = [...]`, `expected = ...` | the function returns `expected` |
| `require = ["While"]` | the code uses these Python AST node types |
| `forbid = ["For"]` | the code uses none of them |
| `require_comment = true` | the code has a `#` comment |

`stdin = "..."` gives fake input to the first three.

`values = { capacity = 400 }` goes with the first two: the first line `capacity = ...` of the player's code gets this value before it runs. Use it in every code wave from 1-2, so that printing the expected text cannot pass. A value may also be a list, to swap a whole dataset. The brief or starter must name the variable. Build waves are also scored on code quality: snake_case names, 4-space indents, a comment, and docstrings on functions and classes.

## Boss levels

A boss lives in `levels/w<world>/boss-<world>-<short-name>/level.toml` and has `boss = true` in `[level]`. It teaches nothing new, so `new_concepts`, `tips` and `power_up` are left out. It has `time_limit` (seconds, 600 if left out), `sprite` (a file in `art/`, `boss-placeholder` if left out), a cutscene, and exactly one `[[wave]]` with `kind = "boss"`, a reference and a wrong solution. Its tests are hidden: each one is a block of the boss's health bar. See `docs/design/phase-2-screens.md`.

## Tone

- The narrator speaks to the player in the second person: "You patch in more power…"
- Snek speaks in short UPPER-CASE lines: `Snek: "VOICE MODULE ONLINE."`
- Comments in cutscene code start with `# >>` for story lines and plain `#` for explanations.
- Friendly and a little dry. No jokes at the player's expense, and no "easy" or "simple" (it may not be for the player).

## Complete example: Level 1-1

```toml
[level]
id = "1-1"
title = "Hello, Terminal"
world = 1
new_concepts = ["print()", "string literals", "comments"]
power_up = "explain"

cutscene = '''
# >> The lab is dark. One terminal blinks. Snek's voice module is offline.
# >> A note taped to the screen says: "Type this to wake her."
print("SYSTEM CHECK")
print("VOICE MODULE OK")
# >> A speaker crackles.
# >> Snek: "HELLO... TECHNICIAN?"
'''

tips = [
  "print(...) shows whatever is inside the brackets on the screen.",
  "Text inside quotes is a string literal: \"HELLO\" or 'HELLO'.",
  "A line starting with # is a comment. Python ignores it; humans read it.",
]

[[wave]]
kind = "fill-in"
goal = "Make Snek print SNEK ONLINE."
brief = "Fill in the blank so Snek says SNEK ONLINE."
starter = '''print(___)'''
reference = '''print("SNEK ONLINE")'''
wrong = '''print(SNEK ONLINE)'''
hints = [
  "Python reads words without quotes as names. Is SNEK ONLINE a name, or text?",
  "Text goes inside quotes, and the quotes go inside the brackets.",
  "The line starts like this: print(\"SNEK",
]

[[wave.test]]
expected_stdout = "SNEK ONLINE\n"

[[wave.test]]
require = ["Call"]

[[wave]]
kind = "build"
goal = "Print the three start-up lines, with a comment."
brief = """
Make Snek print exactly three lines: SYSTEM CHECK, VOICE MODULE OK, and
HELLO, TECHNICIAN. Add a comment above the code saying what it does.
"""
reference = '''
# Snek's start-up message
print("SYSTEM CHECK")
print("VOICE MODULE OK")
print("HELLO, TECHNICIAN")
'''
wrong = '''
print("SYSTEM CHECK", "VOICE MODULE OK", "HELLO, TECHNICIAN")
'''
hints = [
  "Each print() call prints one line.",
  "Write one # comment line, then three print() lines, one per message.",
  "Start with: # Snek's start-up message, then print(\"SYSTEM CHECK\") and two more lines like it.",
]

[[wave.test]]
expected_stdout = "SYSTEM CHECK\nVOICE MODULE OK\nHELLO, TECHNICIAN\n"

[[wave.test]]
require_comment = true

[[wave]]
kind = "debug"
goal = "Type exactly what the program prints."
mode = "predict"
brief = "What does this program print? Type the output exactly."
code = '''
print("ONE")
# print("TWO")
print("THREE")
'''
answer = "ONE\nTHREE"
wrong = "ONE\nTWO\nTHREE"
explanation = '''
The first and third lines call print(), so ONE and THREE appear.
The second line starts with #: it is a comment, and Python skips it.
'''
hints = [
  "Look at the start of each line. Does Python run all of them?",
  "Python skips a line that starts with #. Only two lines run.",
  "The first line of the output is ONE.",
]
```

This is the format the level loader (`engine/level_pack.py`) reads. The loader checks the structure, and `tests/test_levels.py` checks every level in `levels/` against the limits in this guide. This example is saved as `levels/w1/1-1-hello-terminal/level.toml`.

## Choice waves

A `fill-in` or `debug` wave with `mode = "choice"` asks multiple-choice questions. The player picks with the arrow keys; in plain mode they type `1: a`. It has `wrong` (a sheet that must fail, such as `"1: b"`) and 1 to 6 questions; the right sheet comes from the questions. It has no `reference`, `starter` or tests.

```toml
[[wave.question]]
ask = "Part names in delivery order, repeats kept."
options = ["list", "set", "dict"]
answer = "a"
explanation = "A list keeps order and repeats."
```

A question has 2 to 5 options and one right letter, and may show `code` of at most 8 lines. The console is locked while a wave with question code is open; set `lock = true` for a question about code behaviour that shows none. After 3 failed submits the answers are shown.

## Review waves

A `fill-in` or `debug` wave with `mode = "review"` shows a solution to review. The player marks each faulty line with Space and picks a category; in plain mode they type `4: a` (line, category). It has `code` (at most 30 lines of 60 characters), 2 to 5 `categories`, 1 to 4 faults and a `wrong` sheet.

```toml
categories = ["wrong boundary", "unclear name", "missing check"]

[[wave.fault]]
line = 4
category = "a"
explanation = "< leaves out the limit itself."
```

The player may mark only as many lines as there are faults. After 3 failed submits the faults are shown. Review waves do not lock the console.

## Data files

A wave lists the files its code can open: `files = ["sensors.csv"]`. They live in the level's `files/` folder, have plain names (not `.py`), are UTF-8 and at most 100 KB. Every run gets fresh copies in a throwaway folder, which is not a security boundary. The player reads one with `show sensors.csv`. A boss wave may use them too.

```toml
[[wave.test]]
expected_stdout = "..."
files = { "sensors.csv" = "sensors-b.csv" }   # another dataset under the same name

[[wave.test]]
expected_file = { name = "summary.txt", contents = "..." }
```

Grade every program on at least two datasets, so that printing or writing fixed text cannot pass.

## Testing the player's tests

When a wave asks for a test function, grade that it can tell right from wrong:

```toml
[[wave.test]]
catches = { test = "test_is_low", function = "is_low", correct = '''
def is_low(value):
    return value <= 5
''', broken = '''
def is_low(value):
    return value < 5
''' }
```

The player's `test_is_low()` (no parameters) runs twice, with `is_low` swapped for each version. It must pass with `correct` and fail an `assert` with `broken`. Add one test per fault the player should catch. The brief must name both functions.

A level may have extra review waves after its three waves (3-4 does). A fault may have `model_comment = "..."`: the player can then comment on each marked line (in plain mode `4: a # why`), and sees the model comments once the wave is done. Comments are not graded.

## Code quality and clearing

From World 3, a level with a build wave is cleared only when build code that passes every test also meets at least 50 % of the code-quality rules. Three stars always need full quality.
