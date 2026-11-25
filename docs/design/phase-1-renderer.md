# Phase 1 design: half-block pixel renderer

Roadmap checkbox (docs/plan.md, Phase 1): "Half-block pixel renderer that
draws a sprite from a text file". Approved before coding, on branch
`phase-1/renderer` (taken from `main`; it does not depend on the command loop).

## Files

- `art/palette.txt`: one colour per line, `code red green blue name`, for
  example `2 29 43 83 dark-blue`. Lines starting with `#` are comments and
  blank lines are skipped. The palette lives in a file so the pixel artist can
  change it without touching code.
- `art/robot.txt`: the robot from the old `render/sprite_test.py`. One line
  per pixel row; `.` is a transparent pixel; `#` lines are comments.
- `render/palette.py`:
  - `load_palette(path)` returns a dict such as `{"2": (29, 43, 83)}`
  - `foreground(colour)` and `background(colour)` turn a `(red, green, blue)`
    colour into an ANSI escape code
- `render/sprite.py`:
  - `load_sprite(path, palette)` returns the sprite as a list of row strings
  - `render_sprite(sprite, palette)` returns the terminal lines (the
    half-block logic from the old demo)
  - `SpriteError` (a kind of `ValueError`) names the file and line number when
    a row uses a code not in the palette, rows have different widths, or the
    file has no rows
  - a sprite with an odd number of rows gets one transparent row added at the
    bottom, instead of an error
- `render/__main__.py`: `python -m render art/robot.txt` draws any sprite
  file, for testing by hand.
- `tests/test_palette.py`, `tests/test_sprite.py`: unittest, with small and
  broken files made with `tempfile`, plus the real `art/robot.txt`. The old
  sprite tests move here.

## Decisions

- **`render/sprite_test.py` and `tests/test_sprite_test.py` are removed.**
  Their logic and tests move to `render/sprite.py` and `tests/test_sprite.py`,
  so the same code does not exist twice.
- **Colours stay 24-bit** (`38;2;r;g;b` and `48;2;r;g;b`), as in the demo. The
  plain-ASCII fallback and accessible mode from the plan are later work.
- **Palette codes are one character** (`0`–`9`, `a`–`f`), so there is room for
  the plan's fixed 16-colour palette.
- **The palette holds only the robot's three colours for now.** Choosing all
  16 belongs to the art style guide (a Phase 0 checkbox not done yet).
- **Note:** the three current colours are exactly colours from the PICO-8
  palette. The plan asks for a palette "of our own", so they are placeholders
  to revisit with the art style guide.

## Later changes (branch `phase-1/review-fixes`)

- `art/robot.txt` was removed. It broke the art style guide (comment lines,
  no `-<state>` in its name, colours from the old placeholder palette), and
  `art/aria-offline.txt` now covers the same tests.
- Sprite files follow the art style guide strictly: comments, blank lines and
  spaces are errors, each with its own clear message.
- Palette codes must be `0`–`9` or `a`–`f`.
- `render_sprite` raises `SpriteError` for an odd number of rows instead of
  an `IndexError`.
