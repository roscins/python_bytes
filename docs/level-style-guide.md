# Level style guide

Every level in Python Bytes follows this guide. If a level breaks a rule, the pull request is not merged.

## Folder and file naming

```
levels/w<world>/<level-id>-<short-name>/level.toml
```

Examples: `levels/w1/1-1-hello-terminal/level.toml`, `levels/w2/2-3-charging/level.toml`.
Bosses: `levels/w1/boss-1-corrupted-bootloader/level.toml`.

## Required parts of a level

| Part | What it is | Limit |
| --- | --- | --- |
| `[level]` | id, title, world, new concepts, power-up | 2–4 new concepts |
| `cutscene` | Story scene with working code in it | 25 lines |
| `tips` | One-line explanations of the new syntax (go to the Codex) | 1 tip per new concept |
| Wave 1 `fill-in` | Given code with `___` blanks to complete | 1–3 blanks |
| Wave 2 `build` | Write a program from a short brief | Brief: 5 sentences |
| Wave 3 `debug` | Predict the output, or find and fix one bug | 10 lines of code |
| Tests | At least 2 tests per wave. In a predict-mode debug wave, `answer` and `wrong` count as its tests | – |
| Reference + wrong solution | One solution that must pass, one typical mistake that must fail | Per wave |

## Hard rules

1. A level uses only constructs taught in earlier levels, plus its own new concepts. The progression checker enforces this.
2. At most 4 new concepts per level.
3. Everything is in English.
4. Every wave has a reference solution that passes and a wrong solution that fails. A predict-mode debug wave has a right `answer` and a `wrong` answer instead.
5. The cutscene shows the new syntax working **before** the tips explain it.
6. Code in levels follows the style the game grades: snake_case names, 4-space indents, comments where useful.

## Kinds of test

Each `[[wave.test]]` table has exactly one of these keys:

| Key | Passes when |
| --- | --- |
| `expected_stdout = "..."` | the program prints exactly this (spaces at line ends and blank lines at the end are ignored) |
| `expected_stdout_contains = ["...", "..."]` | every piece appears in the output |
| `call = "name"`, `args = [...]`, `expected = ...` | the function returns `expected` |
| `require = ["While"]` | the code uses these Python AST node types |
| `forbid = ["For"]` | the code uses none of them |
| `require_comment = true` | the code has a `#` comment |

`stdin = "..."` gives fake input to the first three. Build waves are also scored on code quality: snake_case names, 4-space indents, a comment, and docstrings on functions and classes.

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
power_up = "status"

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
brief = "Fill in the blank so Snek says SNEK ONLINE."
starter = '''print(___)'''
reference = '''print("SNEK ONLINE")'''
wrong = '''print(SNEK ONLINE)'''

[[wave.test]]
expected_stdout = "SNEK ONLINE\n"

[[wave.test]]
require = ["Call"]

[[wave]]
kind = "build"
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

[[wave.test]]
expected_stdout = "SYSTEM CHECK\nVOICE MODULE OK\nHELLO, TECHNICIAN\n"

[[wave.test]]
require_comment = true

[[wave]]
kind = "debug"
mode = "predict"
brief = "What does this program print? Type the output exactly."
code = '''
print("ONE")
# print("TWO")
print("THREE")
'''
answer = "ONE\nTHREE"
wrong = "ONE\nTWO\nTHREE"
```

This is the format the level loader (`engine/level_pack.py`) reads. The loader checks the structure, and `tests/test_levels.py` checks every level in `levels/` against the limits in this guide. This example is saved as `levels/w1/1-1-hello-terminal/level.toml`.
