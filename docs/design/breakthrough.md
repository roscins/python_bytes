# Breakthrough: making Python Bytes feel like a real game

Status: **approved**, with one change: no lives and no XP (decision 7 below). PR A is built
and was merged into #19's branch (#20); PR #21 lands #19 and #20 on `main`. PR B is built on that.
B also contains the decision "a level clears only when all waves are passed", and A's "a half-typed line is lost" is accepted.
C is built on B's branch (PRs against `main`). Cut from the design: arrow keys in the title menu (the menu takes a typed number or letter) and the hand-drawn art review is left to you.
Three PRs, in this order: **A** (start, title, save), **B** (code inside the game),
**C** (full-screen look and feel). Each PR is fully tested and gets its own design
tick in `docs/plan.md` (a new "Phase 2.5 – Breakthrough" with three checkboxes).

PRs #18 (checker and tools) and #19 (map from `concepts.toml`) are open and touch
`engine/__main__.py`, `game_state.py`, `commands.py` and `hud.py`. **Recommendation:
merge #18 and #19 first, then branch A from `main`.** Otherwise A is stacked three deep.

## 0. Decisions I need from you (the rest of this file assumes my recommendation)

| # | Question | My recommendation |
| --- | --- | --- |
| 1 | **PR A's kill -9 test needs the code to live in the game.** Today the code is in external files, which the game cannot autosave. | **Move the code *buffer* and its simplest entry (type a line, `:submit`, `:show`, `:undo`, `:clear`) into A.** B then adds `:run`, `:edit`, `:hint`, the REPL, highlighting, friendly errors and deletes the workspace flow. The alternative (keep the split literally) makes A's test prove very little: see 2.6. |
| 2 | `[project.scripts]` only works after `pip install`. Installing needs a build backend. | Add `[build-system] requires = ["setuptools>=68"]` (build time only, no runtime dependency) and tell players to run `pip install -e .`. `python play.py` needs no install and is the documented way. |
| 3 | `main()` must be the CLI entry point *and* tests call `main(levels, save, ...)` with arguments. | Rename today's `main` to `run_game(...)` (tests use it); the new `main()` parses `sys.argv` (`--plain`, `--save PATH`) and calls `run_game`. About 10 test call sites change. |
| 4 | Indentation in the line editor. | No auto-indent. What you type is what is stored (Tab becomes 4 spaces). After a line ending in `:` the prompt shows a dim `⇥` hint. Students must learn indentation (outcome B8). |
| 5 | Does the REPL keep variables between lines, and does `input()` work in it? | Yes to variables (one long-lived sandbox process). `input()` works in `:run` (see 3.4), not in the REPL in v1. |
| 6 | Extra commands beyond your list. | Add `:del <n>`, `:ins <n>`, `:wave <n>` (go back to replay a wave), `:quit`. A line editor with only `:edit` is painful. |
| 7 | **Decided: no lives, no XP.** | A boss is just a harder task. You get **three tries**; if all three fail you restart the level. The HUD shows "tries left" only inside a boss. XP, XP bars and player levels are not built. |
| 8 | What happens to the existing XP code and combo multiplier? | **Nothing is deleted in these PRs.** XP stays in the engine and the save, unused and never shown (removing it is a later cleanup, so these PRs stay small and the save format stays readable). The combo stays as a **display-only streak** that flashes in the HUD; its XP multiplier simply has no visible effect. |
| 9 | `where` "as an advanced option". | `where` writes the current wave's code to `workspace/<level>/waveN.py` and prints the path. One-way export, no import. |
| 10 | **NEW GAME when a save exists.** | Never delete: ask for confirmation, then move the old save to `save.json.old` (one generation). |
| 11 | Sprites for happy / dizzy / celebrating Snek, and the logo. | I draw them (16×16, the existing palette and format). You review the art in PR C. |

## 1. Principles for all three PRs

1. **The save on disk is always the truth.** `kill -9`, a crash, power loss or a closed
   window may happen at any moment. Signal handlers are a courtesy; autosave is the guarantee.
2. **Rendering is pure.** Functions return strings or lists of frames. Time, keys and the
   terminal size are injected, so everything is testable without a terminal.
3. **`--plain` is the baseline.** No colour, no animation, no alternate screen, no
   box-drawing (ASCII `+-|`), line-based. It is also used automatically when stdout is not a
   terminal or `NO_COLOR` is set. The fancy mode only adds to it.
4. **Standard library only**, readable for first-year students (CLAUDE.md): docstrings on
   every function and class, no clever one-liners.
5. **Platform differences live in one file**, `engine/terminal.py`:

| | Linux / macOS | Windows Terminal |
| --- | --- | --- |
| Single keys | `termios` + `tty`, `select` for "was a key pressed" | `msvcrt.getwch`, `kbhit` |
| Colour escapes | built in | enable virtual-terminal mode with `ctypes` (`SetConsoleMode`); on failure fall back to `--plain` |
| Line editing in `input()` | `import readline`: arrows and history for free | built into the console |
| Signals | `SIGINT`, `SIGTERM`, `SIGHUP` | `SIGINT`, `SIGBREAK`; closing the window via `SetConsoleCtrlHandler` (runs in another thread, ~5 s) |
| Atomic save | `os.replace` | `os.replace`, retried a few times: antivirus or the indexer can briefly lock the target (`PermissionError`) |

I cannot run Windows here. Windows-only code is kept tiny, unit-tested with fakes, and
listed in a manual checklist in each PR description.

## 2. PR A: one command, instant start, unkillable save

### 2.1 Starting
- `play.py` in the repo root: three lines that call `engine.__main__.main()` and exit with its code.
- `pyproject.toml`: `[project.scripts] python-bytes = "engine.__main__:main"` plus the
  build-system and package list (decision 2). Levels and art are found relative to the
  package, so an *editable* install is the supported one.
- `main()` options: `--plain`, `--save PATH` (used by tests and teachers), `--help`.
- No welcome or help text before the title screen.

### 2.2 Title screen (plain version; the pixel-art version is PR C)
```
 PYTHON BYTES

   1  CONTINUE   (level 1-1, wave 2)
   2  NEW GAME
   3  QUIT

 > _
```
- CONTINUE only if a readable save exists, and it says where you will land. Enter picks the
  default (CONTINUE, else NEW GAME). `1/2/3` or `c/n/q` also work.
- A damaged save is moved aside as today (`.broken`), and the title says so in one line.
- NEW GAME with an existing save: confirm, then keep the old one as `.old` (decision 10).
- The loop is entered with the player already in the right place; CONTINUE shows the
  current wave with the saved code (2.5).

### 2.3 Autosave after every state change
New `engine/autosave.py` with one object, `AutoSaver(state, path)`, and one method, `save()`.
It is called:

| Event | Where |
| --- | --- |
| level entered (`play`) | after the command |
| a line typed into the code buffer, `:undo`, `:clear` | after **each line**, before anything runs |
| a wave graded (pass or fail), reward applied | after grading |
| hint bought | after the purchase |
| quit | last |

`save_progress` already writes a temp file and `os.replace`s it. Added:
- `flush()` + `os.fsync()` on the temp file before the replace (power loss);
- a per-process temp name (`save.json.<pid>.tmp`), so two games cannot corrupt each other's temp;
- the Windows retry loop (table above);
- directory fsync on POSIX, best effort;
- one `SAVE_VERSION = 3`: adds `current_wave` and `buffers` (2.5). Versions 1 and 2 still load.

Honest limit: the unit saved is a **completed line** (the moment the player presses Enter).
A line half typed when the process dies is lost. Saving per keystroke would need a raw-mode
editor; not in scope.

### 2.4 Signals
- `SIGINT`, `SIGTERM`, `SIGHUP` (when it exists) and `SIGBREAK` (Windows) share one handler.
- **The handler saves nothing itself.** A save from inside a handler could write a
  half-updated state (coins added, level not yet marked cleared). Instead:
  - if the game is waiting for the player to type, the handler raises `GameInterrupted` (a
    `SystemExit` subclass). This is needed because since PEP 475 a handler that returns
    normally lets `input()` resume waiting;
  - if a command is running, it sets `shutdown_requested`; the loop checks it right after
    the command (a consistent state), saves, and exits. A second signal exits at once;
  - the exit path (`finally`) always saves once and restores the terminal (C).
- Writes to a closed terminal (`OSError`/`BrokenPipeError` after `SIGHUP`) are ignored.
- Exit codes: 0 normal, `128 + signal` for signals.
- Windows: the console-close handler runs in another thread, so `save()` takes a
  `threading.Lock`; the same lock guards normal saves.

### 2.5 The code buffer (decision 1)
- `GameState.current_wave` (1-based) and `GameState.buffers[level_id][wave_index] = text`.
- Entering a wave fills the buffer from the starter (fill-in, fix-the-bug) or leaves it empty,
  exactly as `engine/workspace.starting_text` does today. An existing buffer is never overwritten.
- A wave screen shows the brief, then the numbered buffer, then a prompt `  3 │ `.
- In a wave a line that does not start with `:` is **appended** to the buffer.
  A predict wave's buffer is the typed answer.
- Commands in A: `:submit` (grade this wave only: `grade_submission` already takes a list of
  waves), `:show`, `:undo`, `:clear`, `:map`, `:help`, `:quit`. Outside a wave the old word
  commands (`map`, `play 1-1`, `hint 2` ...) still work; `:` before them is also accepted.
- Grading reads the buffer instead of the workspace file. The workspace code stays until B
  but is no longer used by `submit`.
- Resume: CONTINUE restores level, wave, buffer, hints bought, combo, boss state as today
  (a boss fight restarts, as the plan says).

### 2.6 If decision 1 is "keep the split literally"
A would store level, wave and a snapshot of the workspace file in the save, and the test
would write the workspace file itself (an editor cannot be "autosaved"). The test would prove
that state survives, not that *typing* does. I advise against it.

### 2.7 Tests (written first)
1. **The kill test, for real.** `tests/test_crash_recovery.py` starts `play.py --plain --save
   <tmp>` as a subprocess with pipes, reads output with a reader thread and timeouts, sends
   `2` (NEW GAME), `play 1-1`, two lines of an answer, waits until the prompt for line 3 is
   printed, then `process.kill()` (SIGKILL on Linux/macOS, TerminateProcess on Windows).
   It starts a second process, sends `1` (CONTINUE) and asserts the output shows level 1-1,
   the right wave, and exactly those two lines at lines 1 and 2.
2. Signals (skipped on Windows): `SIGTERM` and `SIGHUP` while waiting for input, and while a
   long grading command runs; exit code, save content, and that the save is whole JSON.
3. Atomicity: `os.replace` made to raise after the temp file is written leaves the old save
   readable; temp names include the pid; fsync is called (spy); a retry on `PermissionError`.
4. Autosave events: each row of the table in 2.3 causes exactly one save (spy).
5. Title screen: with and without a save, a damaged save, NEW GAME keeps `.old`, no help text first.
6. Save v3 round trip; v1 and v2 files still load; buffers for removed levels are dropped.
7. `play.py` and `main()` flags; `run_game` keeps the old signature for the existing tests.

## 3. PR B: code inside the game

### 3.1 Modes
| Mode | Prompt | A typed line is |
| --- | --- | --- |
| MENU (map, between waves) | `> ` | a command (`map`, `play 1-2`, `:hint` ...) else Python (3.3) |
| CODE (in a wave) | `  3 │ ` | a line of code, unless it starts with `:` |

`:` commands work in both modes. In CODE mode an unknown `:word` says so and changes nothing.
A code line inside a multi-line string that must start with `:` needs a leading space.

### 3.2 Code mode commands
`:run` test-run without submitting · `:submit` · `:show` (numbered, highlighted) · `:undo`
(a stack of snapshots, so `:undo` also undoes `:clear`) · `:clear` · `:edit <n>` ·
`:hint` (buys the next hint of this wave, as `hint` does now) · `:map` · `:help`, and, with
decision 6, `:del <n>`, `:ins <n>`, `:wave <n>`, `:quit`.
`:edit` and `:ins` ask for the new text; where `readline` allows it (Linux, maybe macOS) the
old text is pre-filled with `set_pre_input_hook`, otherwise it is printed above the prompt.

### 3.3 The REPL outside waves
- A line that is not a command goes to `codeop.compile_command`. Incomplete (`for i in
  range(3):`, an open bracket) shows the continuation prompt `... `; complete runs; a syntax
  error becomes a friendly message (3.5). `print("hi")` works everywhere.
- Command names win over Python: `map` is a command. (A variable named `map` is therefore
  reached with `print(map)` or `map = 1`; the second parses as a statement, not a command.)
- Execution happens in **one long-lived sandbox process** (`runner/repl.py`, a small loop over
  `code.InteractiveInterpreter`, JSON lines over pipes). Variables persist; expression
  values are echoed. Each line has the 2 s limit; on timeout the process is killed and
  restarted, and Snek says the variables were reset. Same "not a security sandbox" caveat as
  the runner.

### 3.4 `:run`
Runs the buffer in the existing runner. If the code contains `input(`, the game first asks
for the input lines ("Type the input your program will read. Empty line to start.") and passes
them as fake stdin: deterministic and testable. For a predict wave `:run` runs the *shown* code
and prints its real output (a hint that costs nothing but spoils the wave, so it is disabled
there: "Snek will not tell you").

### 3.5 Highlighting (`render/highlight.py`)
`highlight(code, theme) -> str` using `tokenize.generate_tokens` over the whole buffer, so
multi-line strings work. Tokens are collected inside a `try`; on `TokenError` or
`IndentationError` (half-typed code) the tokens already read are coloured and the rest is
scanned line by line, then left plain. Classes: keyword, builtin name, string, number,
comment, operator, name, and the fill-in blank `___` (inverse). Theme in the 16-colour palette:
keyword violet, string teal, number pink, comment steel, builtin cyan, blank inverse. (The art
guide's colour meanings are for sprites; this UI theme needs your OK.) No colour in `--plain`.

### 3.6 Friendly errors (`engine/friendly.py`)
`friendly_error(error_text) -> (headline, detail)`:
```
  Snek tripped on line 2: a quote is missing.
  you wrote:  print("hello)
  ───────── (dim grey) ─────────
  SyntaxError: unterminated string literal (detected at line 2)
```
A table maps Python's messages to headlines: unterminated string, `'(' was never closed`, expected
`:`, expected an indented block, unindent mismatch, "Perhaps you forgot a comma", `NameError`
("I do not know the name `x`: a typo, or not created yet?"), `TypeError`, `ZeroDivisionError`,
`IndexError`, `KeyError`, `ValueError`, `AttributeError`, and the time limit ("ran longer than
2 seconds: a loop that never ends?"). The line number is read from the last traceback frame of
the player's file; the shown source line comes from the buffer. Unknown errors get a generic
headline plus the real message. The grader's `problem_with_run` messages go through the same function.
"Small grey text" is dim/grey (a terminal has one text size).

### 3.7 Removing the workspace flow
`prepare_workspace`, the file reads in `grade_submission`, and the workspace line in the level
intro are removed from `play` and `submit`. `where` stays as the one-way export (decision 9). The
plan's open question "own editor or in the terminal?" is decided and the plan's architecture
text is updated. `tests/test_workspace.py` shrinks to the export.

### 3.8 Tests
Mode switching and the parsing of each colon command; the REPL (complete, incomplete,
syntax error, persistent variables, timeout restart, `print("hi")` in map mode, command names
win); highlighting golden strings per token class, plus half-typed code, a triple-quoted
string over several lines, and no colour in plain; friendly errors for every row of the table
using real error texts from the runner; `:run` with and without `input(`; undo/clear/edit/del/ins
line arithmetic; the level-1-1 reference solutions typed line by line through the whole loop
(the Phase 2 gate, now without files); the workspace is never created.

## 4. PR C: visual and fun overhaul

### 4.1 Rendering model
- `render/screen.py`: `compose(hud, body, status, input_row, size) -> list[str]`. Rows 1-2 are
  the HUD, the last two rows are the status line and the input line, the middle is the body.
  Every row is padded to the width; a frame is only redrawn where it changed (cursor-addressed
  writes, no full clear, so no flicker). Minimum 80×24: a smaller window gets one polite
  message. Resize is read before each frame (`SIGWINCH` on POSIX, polling elsewhere).
- Alternate screen: `enter` writes `ESC[?1049h` and hides the cursor only during animations;
  `leave` restores both. `Fullscreen` is a context manager and is also registered with `atexit`
  and run by the signal path of A, so a clean exit, an exception, `Ctrl-C`, `SIGTERM` and
  `SIGHUP` all restore the terminal. After `kill -9` nothing can: the README says to type `reset`.
- Colour depth: `COLORTERM=truecolor` gets 24-bit; otherwise colours are mapped to the nearest
  of 256 (macOS Terminal.app has no truecolor; the current renderer would show wrong colours).
- `render/panel.py`: `panel(title, lines, width)` with `┌─┐│└┘` (ASCII `+-|` in plain or when
  the output encoding cannot print them). Used for story, code, results and hints.
- Plain mode: the same screens printed once, below each other, no escape codes.

### 4.2 Screens
- **Title:** pixel-art "PYTHON BYTES" built from a small 5×7 pixel font table in the code
  (nine letters), drawn on the canvas, with Snek slithering across using the existing slither
  frames, "press Enter" blinking. Menu with arrow keys (raw keys) in fancy mode, as in A in plain.
- **HUD, every screen:** line 1 `WORLD 1 · BOOT SECTOR · 1-2 MEMORY CELLS`; line 2 stars,
  coins and the combo, and inside a boss fight the tries left:
  `★ 7/18   ◎ 35   COMBO x3` (boss: `TRIES 2 of 3`).
- **Cutscene:** a story panel typed letter by letter. `typewriter_frames(text, step)` returns
  frames; the display loop takes `sleep` and `skipped()` injected; Enter jumps to the last frame.
  Punctuation pauses a little longer. Plain: printed at once.
- **Snek reactions:** new sprites `snek-happy`, `snek-dizzy`, `snek-celebrate` (and `snek-idle`)
  beside the results panel: happy on pass, dizzy on fail, celebrating on level clear.
- **Level clear:** the existing frames extended: stars count up one by one, the coins
  earned fly into the coin counter, then the power-up is revealed in a violet frame
  ("NEW COMMAND: calc") with the name typed out.
- **Combo:** shown in the HUD; when it goes up it flashes for three frames (bold/inverse).
  No flashing in plain mode, which also covers the "no flashing" accessibility promise.

### 4.3 Input in full screen
Code lines stay in cooked mode (`input()` works in the alternate screen, with readline
editing on POSIX). Raw single-key reading is only used for the title menu and for "press Enter
to skip" during animations (`select`/`msvcrt`, behind `engine/terminal.py`).

### 4.4 Tests
All screens are functions: golden frames (ANSI stripped) for the HUD, the title, a cutscene
frame sequence (first, middle, last, and skip), a code panel, a results panel with each Snek
sprite, the level-clear sequence (star count, coin counter monotonic, power-up last). Structural
tests: every row is exactly the screen width, panel corners line up, the HUD is on **every**
screen function, ASCII fallback has no non-ASCII character, the 256-colour mapping is
monotonic. Terminal restore: with a fake writer the escape sequences enter/leave are
symmetric on normal exit, exception, and the signal path. A POSIX-only `pty` test starts the
game in an 80×24 pseudo-terminal, checks that it enters the alternate screen, sends `SIGTERM`
and checks that it left it again and that the save exists.

### 4.5 Consequences of "no lives, no XP"
- `docs/plan.md`: the reward table loses the XP and Lives rows; the boss text says "three tries,
  then the level restarts"; the Phase 2 mention of XP stays as history (ticked).
- `render/boss_screen.py` shows `TRIES 2 of 3` instead of hearts; the engine's counter and its
  tests keep their names (`lives`) to keep these PRs small.
- The level-clear screen and the results text stop mentioning XP; stars, coins, power-up remain.

## 5. Order, size and risk
| PR | Mostly new | Mostly changed | Risk |
| --- | --- | --- | --- |
| A | `autosave.py`, `terminal.py` (signals), `title.py`, `play.py`, crash tests | `__main__`, `save_file`, `loop`, `commands` | the buffer decision (1); signals on Windows (untestable here) |
| B | `highlight.py`, `friendly.py`, `runner/repl.py`, code-mode parser | `commands`, `submission`, `workspace`, plan | REPL process lifecycle; readline differences on macOS (libedit) |
| C | `screen.py`, `panel.py`, `terminal` keys, sprites, logo, animations | `hud`, `level_clear`, `boss_screen`, `loop` | biggest PR; art needs your review; colour depth. I can split it into C1 (frame, HUD, panels, title, terminal restore) and C2 (animations, Snek reactions, level clear) if you prefer smaller reviews. |

## 6. Out of scope (said once, so nothing is a surprise)
Per-keystroke autosave; syntax-aware auto-indent; mouse input; sound; a second running copy
of the game on the same save (last writer wins; no lock file); editing a line by moving the cursor
across several lines (use `:edit`); `input()` inside the REPL; a real security sandbox.
