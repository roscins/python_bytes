# Design: UX pass on World 1

**Status: approved** (see Decisions at the end). Built on one branch, `ux/pass`.

## How the audit was done

A script played all of World 1 and started Boss 1 in plain mode, typing what a
new student plausibly would: no colons, typos, a missing quote, a wrong
answer, code instead of a blank. It ran on the branch of PR #36. It is one
scripted run read by me, not a test with students, and it did not cover the
full-screen mode.

## Two bugs (fix first)

- **B1. Boss 1 never shows its code.** `play boss-1` gives the task, the health
  bar and the prompt `13 |`, but not the scrambled program. Only `:show`
  reveals it, and nothing says so.
- **B2. "LEVEL 1-1 CLEARED" before it is.** The animation plays whenever the
  stars go up. After wave 2 it says CLEARED, and the text below says "Pass
  every wave to clear this level." It then plays again after wave 3.

## Where a new student would hesitate

**Starting**
1. The title takes Enter, but the screen does not say so.
2. The map explains neither stars, `locked`, coins nor what to type besides `play 1-1`.
3. `x` gives "Unknown command", while `1` silently prints `1`: the map is also a
   Python console and nothing says so.
4. `help` lists commands without colons, then says to use one while coding.
5. `play` alone and `play 1.1` do not offer the level that is open.

**Reading a level**
6. Story, tips, instructions, goal and code arrive as one block of about 35 lines.
7. Lines reach 123 characters and wrap badly in an 80-column window.
8. The goal is inside a paragraph, and is gone after results or an error.
9. The command line under the code lists ten commands, `:run` not among them.
10. Playing a level again repeats the whole story and tips.

**Typing**
11. In a fill-in wave, typing the blank's content (`"SNEK ONLINE"`) adds line 2
    and leaves `___` in line 1.
12. `submit` without a colon becomes a line of code, and later fails with
    "I do not know the name submit".
13. `:sumbit` and `sumbit` suggest no command.
14. Replacing a line takes `:edit 1`, then the line. Arrow keys print `^[[D`
    (no `readline`; seen in the code, not in the scripted run).
15. A predict wave does not say "one printed line per typed line"; `ONE, THREE`
    on one line is the natural guess.

**Results**
16. Expected and printed text are stacked, with the difference not marked
    (`SNEK ONLINE` against `Snek online`).
17. A syntax error shows the line but not the column, and one message says
    "(line 1) (line 1)".
18. A test name like "prints the right output when unit_name = 'Bolt'" does not
    say that the grader changed the value.
19. "has a comment" is listed twice (test and code quality).
20. "LEVEL SCORE 20 % ☆☆☆", combo and coins are never explained.
21. The hint says "Type hint 1 again", which in a wave is code; it should say `:hint`.
22. After the last wave: "Type map", not which level to play next.
23. A boss shows the time and tries, but not that `:run` costs nothing.

## Proposed fixes

| # | Change | Fixes |
| --- | --- | --- |
| 1 | Footer naming the mode and 3-4 keys, e.g. `CODE · Enter = new line · :submit check · :hint · :help`; modes MAP, CODE, ANSWER, FILL, BOSS | 3, 4, 9 |
| 2 | Story, tips and goal on separate screens with "Enter to continue" (`s` skips to the code); all text wrapped to the window, at most 80 | 6, 7, 10 |
| 3 | A GOAL box above every wave, from a new one-line `goal` field per wave | 8, 15 |
| 4 | Fill-in: show the line with the blank highlighted and ask only for the blank, one blank at a time; a whole line typed by habit is recognised | 11 |
| 5 | `import readline` where it exists: arrows move, up/down recall earlier lines | 14 |
| 6 | Expected and yours side by side, first different line and column marked; `^` under the column of a syntax error; plain words for changed values | 16-19 |
| 7 | `submit` and `hint` without colon (see question 1); typos get "Did you mean :submit?" (`difflib`) | 5, 12, 13, 21 |
| 8 | A tutorial of about 60 seconds before 1-1 (type a line, `:run`, `:submit`, `:hint`); `skip` leaves it; shown once, never for an existing save | 1, 2, 20 |
| 9 | Check the window before full screen: "Needs 80 x 24, yours is 70 x 20: 10 columns wider, 4 rows taller. Enter checks again; p plays in plain mode." | - |

Also in these PRs: next-level line after a clear (22), and "`:run` is free" on
the boss screen (23).

**Plain and testing.** Every new screen is a function that returns text; the
window size and the Enter key are passed in, as now. Plain mode gets the same
words with `+ - |` boxes. Hidden boss tests are never shown side by side.

**Full screen.** The footer takes one row, leaving 18 rows of body at 80 x 24.

## Decisions

1. In a wave, a line that is exactly `submit`, `hint` or `hint 2` is the
   command. If your code has a name `submit` or `hint`, the line is code, and
   one note says so and points to `:submit`.
2. In plain mode the footer is one line printed after each screen, not before
   every typed line.
3. Every wave has a `goal` of at most 60 characters.
4. Replaying a level shows story and tips again; `s` skips.

One pull request, with a commit per step, bugs first.

## How some of it works

- A screen ends with "Enter to continue". `s` skips to the last screen. Any
  other line skips too and is then treated as typed, so nothing is lost.
- The footer replaces the long command line under the code.
- The tutorial is four screens of text, shown when there is no save at all.
- In full screen, a wave too tall for 18 rows is redrawn as GOAL box and code
  only while you type (the end of the code if it is longer than 13 lines);
  `:show` has it all. A boss starts that way, its task being on the first screen.
- The tutorial is text to read, not an exercise.
