# Design: the main character is Snek

Not a roadmap checkbox: a story and art change, approved before coding, on
branch `phase-1/snek` (built on `phase-1/world-map`, because it changes
files from the Level 1-1 and world map branches). The plan's part of the
rename is in the solo-plan PR, which already changes `docs/plan.md`.

## Decisions

- **ARIA becomes Snek, a forest-green robot snake, everywhere.** The
  robotics-lab story, the technician and the short UPPER-CASE lines stay.
  In dialogue the speaker is written `Snek:`, for example
  `Snek: "HELLO... TECHNICIAN?"`.
- **Moss (code 9) becomes forest green, `#228b22`** (34, 139, 34), in
  both the art guide and `art/palette.txt`. It is used for Snek's body,
  plants and green shadows.
- **The sprite is `art/snek-offline.txt`** (16 × 16): a coiled snake with a
  forest-green body (9), a silver shine at the top left (4), dark eyes
  (1) and a pink forked tongue (f), with a Slate outline (2). When online,
  the eyes turn cyan (6). It replaces `art/aria-offline.txt`.

## Files

- `art/snek-offline.txt` (new) and `art/aria-offline.txt` (removed)
- `art/palette.txt` and `docs/art-style-guide.md`: Moss's colour, the
  colour uses, the sizes table and the reference sprite
- `docs/level-style-guide.md` and `levels/w1/1-1-hello-terminal/level.toml`:
  the tone rule and the Level 1-1 example (`print("SNEK ONLINE")`)
- `render/world_map.py`, `render/__main__.py`, `engine/commands.py`:
  `aria` names become `snek`, for example `SNEK_SIZE` and `art.snek`
- Tests: the same renames, and the sprite tests use `snek-offline.txt`
- Earlier design notes: ARIA becomes Snek where they describe current code
