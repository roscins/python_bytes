# Design: full-screen, key-driven interface

**Status: proposed.** Nothing here is built. It comes before World 2 and builds
on the UX pass (PR #38).

## Goal

On a real terminal the player never types a command to do an ordinary thing:
arrows move, Enter chooses, code is written in an editor. `--plain`, pipes and
tests keep today's line mode, unchanged.

## When each mode is used

Key mode needs all of: stdin and stdout are terminals, no `--plain`, no
`NO_COLOR`, a window of at least 80 x 24, and the keyboard could be set up.
Anything else is line mode. Key mode replaces today's full-screen mode with a
typing row; there is no third mode.

## The wave screen (80 x 24)

```
rows 1-3    HUD and rule
rows 4-6    GOAL box
rows 7-21   editor frame: "WAVE 2 of 3 · BUILD", 13 numbered lines
row  22     message ("Hint bought", "Blank 1 of 2: ...")
row  23     [Submit] [Run] [Hint] [Restart level] [Map] [Help]
row  24     footer: ^S submit  ^R run  ^T hint  ^G help  ^O map  ^Z undo  ^E command
```

- The editor always has 13 lines (the longest starter today has 12). Longer
  code scrolls. A line has room for 71 characters; a longer one scrolls
  sideways, with `<` and `>` marking the hidden part.
- The task text (at most 4 lines today) is its own screen before the editor,
  and is the first thing in Help.
- Predict waves: the code to read sits above a smaller answer editor (the
  longest code is 6 lines, the longest answer 4).
- Boss: the timer counts down while you type.

## Editor keys

| Key | Does |
| --- | --- |
| arrows, Home, End, PgUp, PgDn | move the cursor |
| Enter | split the line (no automatic indent) |
| Backspace, Delete | delete; at the edge of a line, join lines |
| Tab | insert 4 spaces |
| Down on the last line, or Esc | focus the buttons |
| Left/Right, Enter on the buttons | pick, press |
| Up or Esc on the buttons | back to the editor |
| Ctrl-S, Ctrl-R, Ctrl-T | submit, run, hint |
| Ctrl-G, Ctrl-O | help, map |
| Ctrl-Z | undo (one step per line worked on) |
| Ctrl-E | type one command (see below) |
| Ctrl-C | save and quit, as now |

Any printable character is accepted, including æ, ø and å. Ctrl-H and Ctrl-I
cannot be shortcuts: terminals send them as Backspace and Tab.

**Command line.** Ctrl-E (`:` at the map) opens one line that takes any of
today's commands: the power-ups, `stats`, `where`, `wave 2`, and Python for
the quick console. Without it these would be lost, as they have no button.

**Fill-in waves.** The starter is shown and only the blanks can be edited. Tab
and Shift-Tab move between blanks. This keeps the UX pass rule.

**Hint** asks "Buy the outline hint for N coins?" before spending. Showing a
hint you already own is free and asks nothing.

**Restart level** asks first (default No). It puts the starter code back in
every wave and goes to wave 1. It keeps passed waves, best score, stars,
bought hints, coins and used guesses, so it cannot be used to get any of them
again. In a boss level it also restarts the fight.

## Other screens

| Screen | Keys |
| --- | --- |
| Title | Up/Down, Enter. "New game" over a save asks [No] [Yes] |
| Map | Left/Right move Snek (past the end: next world), Enter plays; buttons [Play] [Stats] [Help] [Quit] with Down |
| Story, tips, tutorial | Enter continues, Esc skips to the code |
| Results, help, hints, run output | Up/Down scroll, Enter on [Continue] |
| Run with `input()` | a small editor for the input lines, then [Run] |
| Window too small | checks again on resize; `p` plays in line mode |

A locked or unwritten level can be walked to; Enter says why it will not open.
After the last wave, results offer [Next level] [Map].

## Reading keys: `engine/keys.py`

Standard library only. It returns key names ("up", "enter", "ctrl-s") or one
character, and None after a short timeout (for the boss timer and resizing).

- **Linux, macOS:** `termios` and `os.read` on the file descriptor. Line
  buffering and echo are off. Flow control is off so Ctrl-S arrives. Ctrl-Z
  and Ctrl-\ do not stop the process. Signals stay on, so Ctrl-C still goes
  through `ShutdownGuard`. A lone Esc is told apart from an arrow by waiting
  50 ms for the rest of the sequence.
- **Windows:** `msvcrt.kbhit` and `getwch`, polled.
- The terminal settings are saved once and put back in a `finally`, in
  `atexit`, and on SIGTERM, SIGHUP and Ctrl-C through `ShutdownGuard`.
  **`kill -9` cannot be caught by any program**; the player then types `reset`.

## Autosave

Saved after every change to the code and after every action. Pasted text
arrives as many keys at once: all waiting keys are handled, then one save.

## How the code is laid out

| File | Holds |
| --- | --- |
| `engine/keys.py` | key reading and terminal settings |
| `engine/editor.py` | the text, cursor, scrolling, undo; no terminal |
| `engine/focus.py` | buttons and menus: which one is chosen |
| `engine/key_game.py` | which screen is on and what a key does there |
| `render/editor_view.py`, `render/buttons.py` | drawing, as text |

Submit, run, hint and the rest call the same functions as line mode. Their
texts name typed commands (`:submit`, "play 1-2"), so those sentences need a
second wording for key mode.

## Testing

- Editor, focus and drawing are pure and tested with plain values.
- `key_game` takes the key source as an argument; tests script key presses.
- A pseudo-terminal test (Linux, macOS) checks the settings are restored after
  quit, an error, SIGINT, SIGTERM and SIGHUP.
- Line-mode tests stay as they are. Today's full-screen tests type lines and
  will be rewritten to press keys.
- I can only try Linux here. **macOS and Windows need a try by hand** before
  they can be called working.

## Steps

Three pull requests, each with its own roadmap checkbox:

1. `ui/keys`: key reader, title, menus, map, continue screens. Waves still use
   the typing row.
2. `ui/editor`: editor, buttons, shortcuts, command line, autosave.
3. `ui/waves`: fill-in, predict, boss, run input, restart level, key wording;
   remove the typing row.

## Questions for you

Each has a recommendation, which is what the text above assumes.

1. **Tab.** "Tab inserts 4 spaces" and "Tab from the last line goes to the
   buttons" clash: new code is typed on the last line, so Tab could not indent
   there. *Recommend:* Tab always indents; Down on the last line or Esc goes to
   the buttons.
2. **Restart level.** *Recommend:* as above (code only; score and coins stay).
3. **Command line (Ctrl-E).** *Recommend:* yes, so power-ups and the console
   survive.
4. **Fill-in.** *Recommend:* only blanks editable. The other choice is the
   whole starter editable.
5. **Automatic indent** after Enter. *Recommend:* none, as you described it;
   typing the indent is practice, and pasted code is not indented twice.
6. **Hint confirmation.** *Recommend:* yes.
