# Phase 2 design: XP, stars, coins, hints and the 70 % unlock rule

Roadmap checkbox (docs/plan.md, Phase 2): "XP, stars, coins, hints and the
70 % unlock rule". Approved before coding, on branch `phase-2/scoring`
(built on `phase-2/grader`, which gives it the wave results to score).

## The numbers

All of them are constants in `engine/scoring.py`, so Phase 8 can tune them
in one place.

| What | Value | From |
| --- | --- | --- |
| Wave weights | fill-in 20, build 50, debug 15, code quality (build wave) 15 | plan |
| Pass mark (clears the level, opens the next) | 70 % | plan |
| Stars | 1 ≥ 70 %, 2 ≥ 85 %, 3 = 100 % with no hints | plan |
| XP | 10 per score point gained over your best | approved proposal |
| Combo | XP × 1.5 after 3 first-try waves in a row, × 2 after 5 | plan |
| Coins | 5 per wave passed on the first try; 5 the first time a build wave gets full code quality | approved proposal |
| Hint prices | nudge 5, outline 15, partial solution 30 coins | approved proposal |
| Starting coins | 10, so a new player can buy a first nudge | my choice, flagged in the PR |

- **Level score**: each wave scores the share of its tests passed, and the
  build wave's code quality is the share of style rules passed. The score
  is the weighted sum, rounded to a whole percent. A level with other waves
  (bosses, test levels) uses the same weights, divided by their total.
- **The best attempt counts**, wave by wave: a wave's best share never goes
  down, and the level score is made from the best shares.
- **Replays are short**: `submit` grades only the waves that are not yet
  perfect (all tests passed, and full quality for the build wave). The
  others show `already passed ✓`.
- **XP only for improving**, so replaying a cleared level gives nothing:
  `XP = 10 × (new best score − old best score) × combo multiplier`.
- **Combo**: a wave passed on its first graded attempt adds 1. A wave that
  fails, or passes only after earlier attempts, sets it back to 0. The
  combo carries over from level to level and is saved. The multiplier uses
  the combo after the submit.
- **Hints use the best stars rule**: buying any hint caps the level at 2
  stars, because 3 stars needs "no hints". The partial solution's own
  "caps at 2 stars" rule gives the same result for now. Stars never go down
  once earned.

## Files

- `engine/scoring.py`: the constants and small pure functions:
  `level_score`, `stars_for`, `combo_multiplier`, `xp_for`,
  `is_unlocked(levels, cleared, level)`.
- `engine/progress.py`: `LevelProgress` holds one level's progress:
  `wave_best`, `wave_attempts`, `hints_bought` (one number per wave),
  `best_quality`, `quality_rewarded`, `best_score`, `stars`, plus
  `to_dict()` / `from_dict()` for the save file and `wave_is_perfect(n)`.
- `engine/rewards.py`: `apply_submission(state, level, submissions)` updates
  the progress, XP, coins, combo and cleared list after a submit, and
  returns a `Reward` (score, best score, stars, XP and coins gained, combo,
  multiplier, whether the level was cleared just now, and which level
  opened).
- `engine/game_state.py`: `xp`, `coins` (10 to start), `combo` and
  `progress` (level id → `LevelProgress`), and
  `progress_for(level)`.
- `engine/commands.py`:
  - `submit` grades the waves that are not perfect, then shows the
    results and a score line: `LEVEL SCORE 85 % ★★☆`, the XP and coins
    gained, the combo, and either `LEVEL 1-1 CLEARED. Level 1-2 is open.`
    or `You need 70 % to clear this level.`
  - `play` refuses a locked level: `Level 1-2 is locked. Clear 1-1 with at
    least 70 % first.`
  - new `hint <wave>`: shows the hints already bought for that wave and
    buys the next one if the player has the coins. A wave without hints,
    or with all three bought, says so.
- `engine/level_pack.py`: an optional `hints = [nudge, outline, partial]`
  per wave; if it is there it must be exactly three strings.
- `levels/w1/1-1-hello-terminal/level.toml` and `docs/level-style-guide.md`:
  hints for Level 1-1's three waves (the file and the guide example stay
  the same).
- `engine/save_file.py`: save version 2 adds `xp`, `coins`, `combo` and
  `levels` (each level's progress). A version 1 save still loads, with no
  XP and the starting coins. A level whose number of waves changed keeps
  its progress, cut or padded to the new number of waves.
- `render/world_map.py`: a `MapStatus` with the HUD text, which nodes are
  locked and how many stars each level has. Locked levels use a new
  `art/node-locked.txt` tile (Steel and Navy, a padlock shape), stars show
  as `★★☆` under each label, and the header shows the plan's HUD:
  `XP 1240   ★ 7/12   COINS 35`. `render/` still knows nothing about the
  engine; the engine builds the `MapStatus`.
- Tests: `tests/test_scoring.py`, `tests/test_progress.py`,
  `tests/test_rewards.py`, plus updates to the command, save, map and
  level tests.

## Decisions

- **Unlocking follows map order**: a level opens when the level before it
  in `levels/` order is cleared; the first level is always open. The
  boss-door star rule ("2 of 3 stars on average") comes with Boss 1 in
  Phase 3.
- **Not-started waves score 0**, so a player can clear a level only by
  doing enough of it.
- **The level-clear screen is the next branch**; here a cleared level gets
  the text line above.
