# Phase 3 design: World 1, Boot Sector

Roadmap checkbox (docs/plan.md, Phase 3): "Write Levels 1-1 to 2-5". This
covers the World 1 part (1-2 to 1-5; 1-1 exists). Boss 1 follows on branch
`phase-3/boss-1`.

The player asked for the whole of World 1 to be completed without a separate
plan approval, so this document records the decisions for review in the PR.

## The levels

| Level | Fill-in | Build | Debug |
| --- | --- | --- | --- |
| 1-2 Memory Cells | store and print `battery` | store, rebind and print three values and a type | predict: rebinding a name |
| 1-3 Power Calculations | `//` and `%` | run time in hours and minutes | fix a precedence bug |
| 1-4 Floating Truth | `==` against `math.isclose()` | exact, absolute and relative comparison | predict: float round-off |
| 1-5 Corrupted Logs | slice a log line | clean a line and print an aligned report | fix a thrown-away `strip()` |

## Decisions

- **No keyword arguments in 1-4.** `rel_tol=` needs `keyword`, which is first
  taught in 3-3. Absolute and relative tolerance are written out with `abs()`,
  which also shows what `math.isclose()` does.
- **Data is in the starter code**, because `input()` is first taught in 2-1.
- **Output is given exactly in each brief.** Without `input()` or functions the
  tests can only compare output, so `require` tests ask for the construct of
  the level. A determined player can still print the answers as text.
- **Not part of this branch:** the power-up commands do not run yet (a level
  only names its power-up), and the Codex screen is Phase 5.
- **Tests:** predict answers are checked by running the code, and every
  fix-the-bug starter must fail as it stands.
