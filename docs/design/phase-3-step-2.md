# Phase 3 design: three decisions after the power-ups

## 1. A predict wave reveals its answer after 3 wrong guesses

- The third wrong answer shows the correct output and why.
- The wave then counts as passed, at **half** of its score
  (`REVEALED_SHARE` in `engine/scoring.py`). The level can be cleared, but
  not with 3 stars. No coins, and the combo is 0.
- Running code is unlocked from then on: there is nothing left to give away.
- Empty answers are not guesses. Guesses are counted in the save, so
  restarting does not reset them.
- A predict wave has an `explanation` in its level file. Every real level
  must have one.
- The save gets a `revealed` list per level. Older saves without it still load.

## 2. The `:submit` loophole is accepted

See "While a predict wave is unanswered" in phase-3-power-ups.md.

## 3. `stats`

One row per world: levels cleared (bosses count) and stars, then totals.
It works at the map and as `:stats` in a wave, and does not leave the wave.
`stats = 5` is still Python.
