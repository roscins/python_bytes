# Phase 1 design: level-pack loader and save file

Roadmap checkbox (docs/plan.md, Phase 1): "Level-pack loader (TOML) and
save/load of progress (JSON)". Approved before coding, on branch
`phase-1/level-loader` (built on `phase-1/review-fixes`, because both change
`engine/commands.py`).

## Files

- `engine/level_pack.py`:
  - `Level`: a plain class with `id`, `title`, `world`, `new_concepts`,
    `power_up`, `cutscene`, `tips`, `waves` and `folder`
  - `Wave`: a plain class with `kind`, `brief`, `mode`, `starter`, `code`,
    `reference`, `wrong`, `answer` and `tests` (missing fields are `None`;
    `tests` is a list of dicts, which the Phase 2 grader will read)
  - `LevelError` (a kind of `ValueError`) names the file and what is wrong
  - `load_level(path)` reads one `level.toml` with `tomllib` and checks its
    structure (see "What the loader checks")
  - `load_levels(folder)` finds `<folder>/w*/*/level.toml` in folder-name
    order, so `1-1-…` comes before `1-2-…` and `boss-1-…`. Two levels with
    the same id are an error. A missing folder gives an empty list.
- `engine/save_file.py`:
  - `DEFAULT_SAVE_PATH` is `~/.python-bytes/save.json`
  - `save_progress(state, path)` writes
    `{"version": 1, "current_level": "1-1", "cleared": []}`. It writes to a
    temporary file first and then replaces the old save, so a crash halfway
    never leaves a broken save.
  - `load_progress(state, path)` returns `False` if there is no save yet,
    otherwise fills in the state and returns `True`. A level id that no
    longer exists is dropped.
  - `SaveError` (a kind of `ValueError`) for a save that is not valid JSON,
    has the wrong version, or has fields of the wrong type
  - `set_aside_broken_save(path)` renames a broken save to
    `save.json.broken`, so it is never overwritten silently
- `engine/game_state.py`: `GameState(levels)` holds `Level` objects instead
  of `DEFAULT_LEVELS` (removed), plus `cleared` (level ids, filled in by
  Phase 2) and `find_level(level_id)`. `current_level` stays an id string, so
  it can be saved as it is.
- `engine/commands.py`: `map` and `play` use `Level` objects. `play` says the
  level's title. With no levels, `map` says so.
- `engine/loop.py`: `run(state, read_line, write, save_path=None)` saves after
  every command when `save_path` is given. If saving fails, the player is
  told and the game goes on. `welcome_text(state)` adds "Welcome back. You
  were on level 1-1." when a level was saved.
- `engine/__main__.py`: `main(levels_folder, save_path)` loads the levels and
  the save, then runs the loop. A broken level stops the game with a message
  (exit code 1); a broken save is set aside and the game starts fresh.
- Tests: `tests/test_level_pack.py`, `tests/test_save_file.py`, plus updates
  to the command, loop and main tests. All of them use temporary folders and
  never touch the real `levels/` folder or `~/.python-bytes`.

## What the loader checks

Only the structure, so the game never crashes on a broken file:

- a `[level]` table with `id`, `title`, `power_up` and `cutscene` (strings),
  `world` (a whole number), `new_concepts` and `tips` (lists of strings)
- 2–4 new concepts, and one tip per new concept
- the folder name starts with the level id, for example `1-1-hello-terminal`
- at least one `[[wave]]`; each has a `kind` of `fill-in`, `build` or
  `debug` and a `brief`
- `predict` debug waves have `code`, `answer` and `wrong`; every other wave
  has `reference` and `wrong`

The guide's content limits (25-line cutscene, 1–3 blanks, at least 2 tests
per wave, …) are checked by `tests/test_levels.py` on the real levels, which
comes with Level 1-1.

## Decisions

- **Save file in `~/.python-bytes/save.json`**, so it survives `git pull`
  and is never committed.
- **Plain classes, not dataclasses**, as in `GameState`.
- **`tomllib` and `json` from the standard library only.**
- **The save keeps only `current_level` and `cleared` for now.** XP, stars
  and coins come with scoring in Phase 2; `version` lets later saves change.
