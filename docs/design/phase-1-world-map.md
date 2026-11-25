# Phase 1 design: world map screen with ARIA walking

Roadmap checkbox (docs/plan.md, Phase 1): "World map screen with placeholder
sprites and ARIA walking between level nodes". Approved before coding, on
branch `phase-1/world-map` (built on `phase-1/level-1-1`).

## Files

- `render/canvas.py`:
  - `new_canvas(width, height)` returns a blank pixel grid: a list of row
    strings full of `.`, the same shape as a sprite
  - `paste(canvas, sprite, left, top)` copies a sprite onto it; `.` pixels
    in the sprite let the canvas show through, and pixels outside the
    canvas are cut off
  - `draw_line(canvas, code, left, right, top, thickness)` draws a
    horizontal line, for the path between nodes
  - because a canvas is just a list of row strings, the existing
    `render_sprite` draws it unchanged
- `art/node-open.txt`: an 8 × 8 placeholder tile for a level node
- `render/world_map.py`:
  - `WORLD_NAMES`: the eight world names from the plan
  - `node_centre(index, node_count)`: nodes are spread evenly across the
    80-cell screen
  - `map_frame(world, level_ids, aria_left, art)` returns one screen as
    text: the header `WORLD 1 · BOOT SECTOR`, a line of level ids above
    the nodes, then the pixel picture (nodes joined by a teal path, ARIA
    below them, 24 pixels = 12 lines)
  - `map_screen(world, level_ids, aria_index, art)`: the map with ARIA
    under level number `aria_index`, or with no ARIA if it is `None`
  - `walk_frames(world, level_ids, from_index, to_index, art)`: the frames
    of ARIA walking from one node to another, 4 pixels per frame
  - `load_map_art()` reads the palette, the node tile and ARIA from `art/`
  - this module knows nothing about `Level` objects: the engine passes
    level ids and numbers, so `render/` does not depend on `engine/`
- `engine/commands.py`:
  - `map` shows the map of the current level's world (World 1 before any
    level is played), then "You are at [1-1] Hello, Terminal." or "Type
    play <level> to start."
  - `play` walks ARIA to the new level when the player was already on a
    level in the same world: it returns the walk frames, and the last
    frame has the level's intro below the map. Otherwise it returns the
    intro alone, as now.
- `engine/loop.py`: `run(..., pause=time.sleep)`. A command may now return
  a list of frames instead of a text. The loop writes each frame over the
  one before (moving the cursor up by the previous frame's height) and
  pauses `FRAME_SECONDS` between frames. Tests pass a pause that does not
  wait.
- Tests: `tests/test_canvas.py`, `tests/test_world_map.py`, plus updates to
  the command and loop tests.

## Decisions

- **Frames are redrawn by moving the cursor up**, not by clearing the
  screen, so the player's earlier commands stay visible above the map.
- **Every frame has the same height and width**, so drawing over the last
  one leaves nothing behind.
- **No stars, XP or coins on the map yet**: scoring comes in Phase 2.
- **No locked levels yet**: the 70 % unlock rule comes in Phase 2.
- **Only Level 1-1 exists**, so in the real game ARIA has nowhere to walk
  until Level 1-2 (Phase 3). The walk is tested with made-up levels.
- **The plain-ASCII and accessible modes (no animation) are later work.**
