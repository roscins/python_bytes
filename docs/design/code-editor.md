# Design: the code editor (step 2 of the key-driven interface)

**Status: approved** (see Decisions at the end). It follows a playtest of step 1:
menus and map work well, the wave screen is the main blocker.

It replaces the wave parts of docs/design/editor.md and takes in its step 3
too (fill-in, predict, boss, run input, key wording), because Level 1-1 and
Boss 1 cannot be played with keys alone without them.

## The wave screen (80 x 24)

```
rows 1-3    HUD and rule
row  4      GOAL: Make Snek print SNEK ONLINE.
rows 5-14   editor: "WAVE 1 of 3 · FILL-IN", 8 numbered lines
rows 15-22  panel: TASK, RESULTS, RUN or HINT, 6 lines
row  23     [Submit] [Run] [Hint] [Restart wave] [Map] [Help]
row  24     ^S submit  ^R run  ^T hint  ^G help  ^O map  ^Z undo
```

- With the panel closed the editor has 16 lines. A taller window gives the
  extra rows to the panel.
- The GOAL box becomes one line, to make room.
- The editor stays on screen and editable while the panel is open. A longer
  panel text turns with PgUp and PgDn. Esc closes the panel.
- Long lines scroll sideways. Longer code scrolls up and down.

## Opening a wave

The editor has the cursor at once. The panel shows the task, so there is no
separate task screen.

| Wave | Cursor starts |
| --- | --- |
| fill-in | on the first blank |
| debug, boss | line 1 |
| build | on a new line after the starter code |
| predict | in the answer box, under the code to read (one frame, a divider) |

## Editing

Arrows, Home and End move. Typing edits in place. Enter splits a line,
Backspace and Delete join lines. Tab inserts 4 spaces. No automatic indent.
Ctrl-Z undoes, one step per line worked on. Any printable letter works.

**Blanks.** `___` is highlighted. Typing with the cursor on it replaces the
whole blank, and Backspace or Delete there removes it whole. The rest of a
fill-in wave is **freely editable** (this changes the earlier decision that
only blanks could be edited). Restart wave puts the starter back.

## Buttons

Down from the last line, or Esc with the panel closed, moves to the buttons.
Left and Right pick, Enter presses, Up or Esc goes back.

| Button | Key | Does |
| --- | --- | --- |
| Submit | ^S | grade; results in the panel |
| Run | ^R | run without grading; output in the panel. With `input()`, the panel first asks for the input lines |
| Hint | ^T | asks before spending coins; hint in the panel |
| Restart wave | none | asks (default No); starter code back in this wave only. Passed waves, score, stars, coins, hints and guesses stay. In a boss it also restarts the fight |
| Map | ^O | to the map; the code is kept |
| Help | ^G | the task and the keys, full screen |

On a passed wave **[Next wave]** is added first in the row (chosen when it has
just passed);
after the last wave, **[Next level]**. The code and results stay until you
press it. The level-clear animation plays first, as now.

## The failing line

After Submit or Run, if Python reports an error, that line is highlighted in
the editor and a row with `^` is drawn under the column. The cursor stays
where you left it; the editor scrolls so the line is visible. The mark goes
when you edit that line, or at the next Submit or Run.

- The column of a syntax error comes from `compile()`. For a runtime error it
  comes from the `^` line of the traceback, so the grader must keep the line
  and column, not only its message.
- Python does not always give a column. Then only the line is highlighted.
- A **wrong output** has no failing line: the panel shows expected and yours,
  as now. In a predict wave the first wrong answer line is highlighted.
- A boss shows the mark for crashes and syntax errors only, so hidden tests
  stay hidden.

## Friendly errors for missing quotes

The suggestion reuses the player's own words, so it gives no answers away.

| Typed | Snek says |
| --- | --- |
| `print(SNEK ONLINE)` | Text needs quotes: try print("SNEK ONLINE") |
| `print(HELLO, TECHNICIAN)` | Text needs quotes: try print("HELLO, TECHNICIAN") |
| `print(SNEK)` | Text needs quotes: try print("SNEK") |
| `print(SNEK'S ONLINE)` | Text needs quotes: try print("SNEK'S ONLINE") |
| `print SNEK` | Text needs quotes and brackets: try print("SNEK") |
| `print(unti)` after `unit = 1` | I do not know the name unti. Did you mean unit? |

The rule applies to a SyntaxError or NameError on a `print` line whose content
is only words and punctuation: no quotes around it, no `=`, brackets or
operators. A name close to one the code creates counts as a typo instead.
Anything else keeps today's message.

The real Python message stays below in grey. A terminal has one text size, so
it cannot be small.

## Colon commands

They stay in `--plain` and line mode. Key mode never needs or mentions one:
messages and the tutorial name keys and buttons instead. The typing row in
waves is removed.

## Autosave

After every change to the code (once for a pasted block) and every action.

## Code layout

| File | Holds |
| --- | --- |
| `engine/editor.py` | text, cursor, blanks, scrolling, undo; no terminal |
| `engine/wave_screen.py` | the keys of a wave: editor, buttons, panel |
| `render/editor_view.py` | draws the editor with the mark |
| `engine/friendly.py` | the quote and typo rules |

Submit, Run and Hint call the same functions as line mode.

## Testing

- Editor, drawing and error rules are tested with plain values.
- Scripted key presses play **all of Level 1-1 and Boss 1**, including a
  wrong answer fixed with arrows and Ctrl-S.
- I also play both in a pseudo-terminal of 80 x 24 and look at the screens.
- Plain-mode tests stay as they are.
- Linux only; macOS and Windows still need a try by hand.

One branch, `ui/editor`, one pull request, a commit per part. The roadmap
boxes 2 and 3 become one.

## Changes while building

- After a hit on the boss the health bar drains and you are straight back in
  the code. Waiting for Enter swallowed what was typed. A win still waits.
- Restart level and Hint ask with [No] [Yes] in the button row.
- The old full screen with a typing row was removed after the merge.
- Open: Snek's face beside the results is no longer seen in a wave, because
  the panel under the editor does not draw it.

## Decisions

1. The button is **Restart level**, not "Restart wave".
2. Tab indents in the editor; Down from the last line or Esc reaches the
   buttons, and there Tab moves to the next button.
3. Ctrl-E opens a one-line prompt for typed words, without a colon.

## After the first playtest of the editor

1. The button is **Restart wave** (this replaces decision 1). `restart level`
   typed after Ctrl-E still restarts every wave and goes to wave 1.
2. Results and run output whose code has changed are dimmed and headed
   "edited since last check". Undoing the change makes them current again.
3. Typing in the code shrinks the panel to at most 3 lines of text. Esc hides
   it. F1, or the [Panel] button that then appears, shows it in full. Some
   terminals keep F1 for their own help; the button always works.
