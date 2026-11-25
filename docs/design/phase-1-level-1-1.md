# Phase 1 design: Level 1-1 as the test level

Roadmap checkbox (docs/plan.md, Phase 1): "Write Level 1-1 as the test
level". Approved before coding, on branch `phase-1/level-1-1` (built on
`phase-1/level-loader`, which it needs).

## Files

- `levels/w1/1-1-hello-terminal/level.toml`: the complete example from the
  level style guide. Three new concepts: `print()`, string literals and
  comments ("running a script" is not syntax, so it is not a concept).
- `engine/level_screen.py`: `intro_text(level)` returns what `play` shows:
  - the title card: `LEVEL 1-1 · HELLO, TERMINAL`
  - the cutscene: story lines (`# >> …`) as plain text, code lines
    indented, so the player can tell them apart
  - the tips, under `TIPS` (the Codex that keeps them comes later)
  - each wave: number, kind and brief, with its starter code (fill-in) or
    the code to read (predict)
  - how to go on: `submit` is still a placeholder until Phase 2
- `engine/commands.py`: `play` returns `intro_text(level)`.
- `docs/level-style-guide.md`:
  - predict-mode debug waves: `answer` and `wrong` count as their tests
  - "the same style we grade" becomes "the style the game grades"
  - the note "field names are a proposal" becomes: the loader reads exactly
    this format; `tests/test_levels.py` checks the limits
- `tests/test_levels.py`: checks every real level in `levels/` against the
  guide (bosses are left out of the three-wave rule, since their format
  comes later):
  - it sits in `levels/w<world>/`
  - three waves, in the order fill-in, build, debug
  - cutscene at most 25 lines, with at least one `# >>` story line
  - cutscene, reference solutions and predict code are valid Python
  - fill-in: 1–3 `___` blanks in the starter, none in the reference
  - build brief at most 5 sentences; debug code at most 10 lines
  - at least 2 tests per wave, except predict waves, which have an
    `answer` and a `wrong` answer that differ
  - the reference and wrong solutions differ
  - no "easy" or "simple" anywhere the player reads
- `tests/test_level_screen.py`, and a gate test in
  `tests/test_engine_main.py`: with the real levels, a player opens the map,
  plays 1-1, quits, starts again and is welcomed back to 1-1.

## Decisions

- **The cutscene is shown, not run.** Running code belongs to the Phase 2
  runner; then the cutscene can show its output too.
- **Checking the predict answer by running the code is Phase 2 work** (the
  gate "each wave's reference solution passes").
