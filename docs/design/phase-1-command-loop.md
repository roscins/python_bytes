# Phase 1 design: command loop

Roadmap checkbox (docs/plan.md, Phase 1): "Command loop with help, map, play,
submit, quit". Approved before coding, on branch `phase-1/command-loop`.

## Files

- `engine/game_state.py`: a plain `GameState` class with
  - `levels`: level ids in map order (for now the constant `DEFAULT_LEVELS`,
    World 1 only; the level-pack loader will replace it)
  - `current_level`: the level being played, or `None`
  - `running`: `True` until the player quits
- `engine/commands.py`:
  - `parse_command(line)` splits a line into a lower-case command name and a
    list of arguments
  - one `do_<name>(state, arguments)` function per command: help, map, play,
    submit, quit. They **return text and never print**, so they are easy to test.
  - `COMMANDS` maps each name to `(function, description)`; `help` builds its
    list from it, so a new command is added in one place
  - `handle_line(state, line)` dispatches a line; a blank line gives `""`, an
    unknown command gives a hint to type help
- `engine/loop.py`: `run(state, read_line=input, write=print)`. Ctrl-D
  (`EOFError`) and Ctrl-C (`KeyboardInterrupt`) are treated as `quit`.
- `engine/__main__.py`: `python -m engine` starts the game.
- `tests/test_commands.py`, `tests/test_loop.py`: plain unittest. The loop
  tests use a scripted player passed in as `read_line`, with no mocking.

## Decisions

- **Plain class, not a dataclass.** The plan lists `dataclasses` for the
  engine, but a plain class with `__init__` is easier for first-year students
  to read, and dataclasses are only taught in Level 7-2. World 7 uses this code
  as teaching material.
- **`submit` is a placeholder.** It checks that a level has been started and
  says grading is not ready. Real grading comes in Phase 2.
- **No level locking yet.** Any level in the list can be played. The 70 %
  unlock rule comes in Phase 2.
- `hint`, `codex` and `stats` from the plan's full command list are left for
  later checkboxes.
