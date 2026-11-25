# Phase 2 design: the level-clear screen and the boss fight screen

Roadmap checkbox (docs/plan.md, Phase 2): "Level-clear screen and boss
fight screen with health bar and lives". Approved before coding, on branch
`phase-2/screens` (built on `phase-2/scoring`, which gives it the rewards
to show). It also holds the Phase 2 gate test.

## Art (8 × 8 icons and a 16 × 16 placeholder, from the art guide's palette)

- `art/star.txt` (Gold) and `art/star-empty.txt` (Slate outline, Navy
  inside)
- `art/coin.txt` (Gold, with an Orange shadow at the bottom right)
- `art/heart.txt` (Red, Maroon shadow) and `art/heart-empty.txt` (Slate
  outline, Navy inside)
- `art/boss-placeholder.txt`: a 16 × 16 red and maroon robot head. Real
  boss sprites come in Phase 3 with the bosses themselves.

Gold is only used for rewards and red only for danger and lives, as the art
guide says.

## The level-clear screen

`render/level_clear.py`:

- `level_clear_frames(level_id, title, score, stars, xp_gained,
  coins_gained, power_up, art)` returns the frames of a short animation:
  - a banner line `LEVEL 1-1 CLEARED · HELLO, TERMINAL`
  - a pixel picture: a 2-pixel bar across the top, the three stars and a
    coin
  - `SCORE 100 %`, `+1000 XP   +10 COINS`, and `POWER-UP: status`
- The stars fill in one per frame, and the bar flashes White and Green
  while they do; the last frame has a Green bar and all earned stars.
- Every frame has the same height, so the loop draws them over each other.
- `load_clear_art()` reads the palette and icons.

`engine/commands.py`: when a submit clears a level for the first time, or
earns more stars than before, `submit` returns the level-clear frames, and
the last frame has the wave results below it (the same way `play` puts the
intro below Snek's slither). Otherwise it returns the text as before.

## Boss levels in the loader

A boss is a level.toml with `boss = true` in `[level]`:

```toml
[level]
id = "boss-1"
title = "The Corrupted Bootloader"
world = 1
boss = true
time_limit = 600        # seconds; 600 if left out
sprite = "boss-placeholder"   # a file in art/; this one if left out
cutscene = '''
# >> The screen flickers red.
'''

[[wave]]
kind = "boss"
brief = "Repair the boot report."
reference = '''...'''
wrong = '''...'''

[[wave.test]]
...
```

- A boss teaches no new concepts, so `new_concepts`, `tips` and
  `power_up` can be left out. It has exactly one wave, of kind `boss`.
- `Level` gets `boss`, `time_limit` and `sprite`.
- `kind = "boss"` is allowed only in a boss level.

## The boss fight

- `engine/boss.py`: `BossFight(level, clock=time.monotonic)` keeps the
  fight's state: 3 lives, the health (one block per hidden test), and when
  the fight started. `submit_result(result)` returns what happened:
  - `"won"`: every hidden test passed
  - `"hit"`: some tests failed; one life is lost. Health only goes down:
    it is the number of tests still failing in the best attempt.
  - `"restart"`: the last life was lost; the fight starts again with 3
    lives, full health and a new timer
  - `time_left()`: seconds left. When the time is up, the next submit
    is not graded: the fight restarts (`"timeout"`).
- `engine/game_state.py`: `boss_fight` (the fight going on, or `None`).
  It is not saved: quitting in the middle of a fight starts it again next
  time, like the arcade.
- `render/boss_screen.py`:
  - `boss_screen(title, sprite, hp_left, hp_total, lives_left, seconds_left,
    art)` draws the plan's mock-up:
    ```
    BOSS 1 · THE CORRUPTED BOOTLOADER              LIVES ♥ ♥ ♡
    (pixel picture: the boss in the middle, a heart icon per life on the left)
    BOSS HP [██████████░░░░░░░░░░]  5 of 10 hidden tests still failing
    TIME 07:42
    ```
  - `hp_drain_frames(...)`: the bar drains one test at a time, as frames
  - the bar is 20 blocks wide, filled in proportion to the tests failing
- `engine/commands.py`:
  - `play boss-1` starts a new `BossFight` and shows the cutscene and
    the boss screen, plus where the file goes (`wave1.py`)
  - `submit` in a boss level grades the file and updates the fight. The
    answer is the health-bar animation, then one line: `HIT! 3 more tests
    to go. You lost a life: 2 left.`, `The boss knocked you out. The fight
    starts again.`, or `BOSS DEFEATED.` plus the score line. Hidden tests
    stay hidden: only a crash or a syntax error is explained, because those
    say nothing about the tests.
  - winning counts as clearing the boss level at 100 %, through the same
    `apply_submission` as levels, so XP, coins and unlocking work the same
- A test boss and a test sprite live in the tests only; Boss 1 itself is
  Phase 3 content.

## The Phase 2 gate test

`tests/test_phase_two_gate.py`, through `python -m engine`'s `main` with
the real levels, a temporary workspace and a temporary save:

- the player plays 1-1, writes each wave's reference solution, submits,
  and gets 100 %, 3 stars and the level-clear screen
- a second player writes each wrong solution, scores under 70 %, and the
  level stays not cleared, so nothing after it would open (checked with a
  copy of 1-1 as 1-2 in a temporary levels folder)

## Decisions

- **Flashing is short and only on clearing**; the accessible no-flash mode
  from the plan comes later, with the plain-ASCII mode.
- **The time limit is checked when the player submits**, not with a live
  ticking clock, because the game reads whole lines. The time left is shown
  on every boss screen.
- **The boss-door star rule comes in Phase 3** with Boss 1; for now a boss
  opens like a level, when the level before it is cleared.
