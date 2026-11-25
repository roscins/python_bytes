# Phase 3 design: the map from concepts.toml, wave time limits, `boss-8`

Branch `curriculum/map-and-loader`, **stacked on `curriculum/progression-checker`
(PR #18)**: the game now reads `levels/concepts.toml` with
`grader.progression.load_curriculum`, which PR #18 adds. This is the code
follow-up that PR #17 listed as "not done here". Merge #18 first; then this
PR's diff against `main` is only its own change.

## 1. The map shows the whole world (ids from `concepts.toml`)

`docs/curriculum.md` has 5 levels and a boss in every world, but only the
levels that exist as packs in `levels/` are on the map today (just 1-1).
Decided: World 1 shows 6 nodes, ids and titles come from `concepts.toml`,
and a level without a pack is drawn locked.

- `engine/roadmap.py` (new): `MissingLevel` is a small stand-in for a level
  that has no pack yet (`id`, `title`, `world`, `boss`). `build_slots(levels,
  curriculum)` returns one entry per item of the curriculum, in curriculum
  order: the real `Level` if there is a pack, a `MissingLevel` if not.
  `is_written(slot)` tells them apart.
- `GameState` gets an optional `curriculum`. `slots()`, `slots_in_world(w)`
  and `find_slot(id)` give the map's view. **Without a curriculum the slots
  are just the levels**, so every existing test and caller behaves as before.
- Unlocking works on slots: a level opens when the slot before it is cleared,
  and a slot with no pack is never open. So a pack written for 1-3 stays
  locked until 1-2 exists and is cleared. `scoring.is_unlocked` is unchanged:
  it only needs objects with an `id`.
- `map` draws the slots of the current world (6 nodes in World 1, 13 pixels
  each on the 80-pixel map; `[boss-1]` is 8 characters, so labels still fit).
  The stars line in the HUD counts all slots (`★ 0/18`).
- `play 1-2` for a level that has no pack says it is not written yet, not
  "there is no level". `play 9-9` still says there is no level.
- Clearing a level never reports that a `MissingLevel` opened.
- `python -m engine` loads `levels/concepts.toml`. A level pack whose id is
  not in the file stops the game with a message: the curriculum is the
  source of truth (`CLAUDE.md`).
- With no packs at all, `map` still draws the first world, all locked, and
  `play` says the level is not written yet. "No levels found" remains for a
  game started with neither packs nor a curriculum.

The renderer (`render/world_map.py`) needs no change: it already takes any
list of ids and a lock flag for each.

## 2. Optional `time_limit` for a wave

For missions that time code (Level 8-2) a wave may say how many seconds the
player's program may run: `time_limit = 10` in the `[[wave]]` table.

- The loader accepts a whole number of seconds, at least 1, and keeps it as
  `Wave.time_limit` (`None` if left out, meaning the runner's default of
  2 seconds). Anything else is a `LevelError`. A boss level's own
  `time_limit` (the length of the fight) is a different field and does not
  change.
- `grade_wave` passes the limit to every check that runs the program. The
  "ran for more than N seconds" message names the limit that applied.
- `tools/check_level.py` (PR #18) already runs waves through `grade_wave`,
  so it honours the limit with no change.

## 3. `boss-8`

The last boss is `boss-8` (`final-boss` is gone from the curriculum). The
loader, the boss screen (`BOSS 8`) and the map already work for any
`boss-<n>`; this change adds a test that a `boss-8` pack in `w8/` loads,
is named `BOSS 8` and is a boss, so that stays true.

## Tests (written first)

`tests/test_roadmap.py` (slots, missing levels, unlocking, HUD stars, `map` and
`play` with a curriculum), `tests/test_world_map.py` (six nodes),
`tests/test_level_pack.py` (wave `time_limit`, `boss-8`), `tests/test_checks.py`
and `tests/test_wave_grader.py` (the limit is used), `tests/test_engine_main.py`
(curriculum loaded; unknown pack and missing file stop the game).
`tests/test_phase_two_gate.py` now expects `★ 3/18` on the map: World 1 has six
nodes, three stars each.
