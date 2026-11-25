# Phase 3 design: the progression checker and two level tools (PR 2 of 2)

Branch `curriculum/progression-checker`, built on `main` after PR #17.
Roadmap checkbox (docs/plan.md, Phase 3): "Build the progression checker".
The grammar and the six rules are decided in `docs/curriculum.md`, section 6,
and `docs/design/phase-3-curriculum-v1.md`. This note says how they are built.

## Files

| File | Job |
| --- | --- |
| `grader/constructs.py` | Reads Python code with `ast` and lists every construct it uses (rule 1's raw material). |
| `grader/progression.py` | Loads `levels/concepts.toml`, answers "what is allowed in level X", enforces rules 1-6. |
| `grader/level_limits.py` | The limits of `docs/level-style-guide.md` (cutscene length, blanks, tests, ...), moved out of `tests/test_levels.py` so a tool can use them too. |
| `tools/level_brief.py` | Prints a short brief for one level, to paste into a model's context. |
| `tools/check_level.py` | Checks level files: loader, progression, limits, reference and wrong solutions. |
| `tools/__init__.py` | Lets the tests import the two scripts. |

`tools/` is new, so `CLAUDE.md`'s folder layout gets a `tools/` entry. The
scripts add the project folder to `sys.path`, so `python tools/check_level.py`
works from any folder.

## Rule 1: how a construct is found

`grader/constructs.py` walks the code once and returns a list of `Need`s.
A `Need` has a label (what to print, like `call:round`), a list of options
(any one of them in the allowed set is enough, like `["BinOp:Add", "BinOp"]`)
and a line number.

| Code | Needs |
| --- | --- |
| `Module`, `Load`, `Store`, `Del`, `Expr`, operators, `comprehension`, `alias`, `withitem`, `match_case` | nothing. They belong to a parent that is gated, or are always allowed. |
| the name of a function being called | nothing for the name; the call is gated as below |
| any other `Name` | `Name` |
| `Constant` | `Constant:<type>` (`Constant:str`, `Constant:int`, ...) or bare `Constant` |
| `BinOp`, `UnaryOp`, `BoolOp` | `BinOp:Add` etc., or the bare node |
| `Compare` | one need per operator, `Compare:Eq` etc.; `not in` counts as `Compare:In`, `is not` as `Compare:Is` |
| `Call` of a name | `call:<name>`, unless the name is defined in the same code (`def`, `class`, parameter, import, assigned name) |
| `Call` of `x.method()` | `method:<name>` only when `<name>` is a built-in str/list/dict/set/tuple/int/float/file method and `x` is not an imported module or name. A method the code defines itself is free. |
| `Import`, `ImportFrom` | `import:<module>`; any prefix is enough (`import:unittest` allows `unittest.mock`). A module outside the standard library needs `import:local`. |
| decorators | `decorator:<name>`; a decorator defined in the same code needs `pattern:custom_decorator`; one imported from an allowed module is free |
| `def __x__` inside a class | `dunder:__x__` |
| other statements and expressions | their `ast` class name (`While`, `ListComp`, `Lambda`, `Global`, ...). A name listed nowhere is never allowed. |
| `Match` and all `Match*` patterns | `Match` |
| `pattern:...` | `docstring` (first statement of a function or class is a string), `default_args`, `recursion` (a function calls itself by name, or `self.name`), `main_guard` (`if __name__ == "__main__"`), `class_bases`, `annotations` (parameter or return annotation), `varargs` (`*args`, `**kwargs`, `*x` and `**x` in a call) |

Attributes that are not calls (`self.battery`, `path.name`) need nothing:
the checker gates calls, not data. `Attribute` is therefore not listed in
any level.

**Which code is checked** (as decided): cutscene, fill-in starters, references,
debug code (predict `code` and fix starters). A wrong solution and a
fill-in starter are checked only if they parse; output text (`answer`, the
predict `wrong`) never is. A blank `___` is an ordinary name and is ignored.
Code that does not parse where it must is reported by the limits check
("not valid Python"), not twice.

**Error messages** say where the construct is first taught:
`line 3 uses call:round (taught in 1-3)` or `... (not listed in concepts.toml)`.

Not built, because nothing needs it yet: the per-file `exempt = true` for
provided files (the loader has no provided files until Phase 6). The checker
functions take plain code strings, so adding it later changes the callers only.

## Rules 2-6 (the data)

`grader/progression.py` reads `concepts.toml` into a `Curriculum`.
`check_curriculum` runs every rule over all items; `check_item` runs the
rules that concern one item:

| Rule | Per item | Whole curriculum |
| --- | --- | --- |
| 2 | a boss has no constructs | |
| 3 | a level that is not `technique` adds a construct | |
| 4 | its outcome codes exist | every code appears in a non-boss level |
| 5 | not easier than the item before it; a boss is at least the world's maximum; a world starts at most (previous boss - 1) | |
| 6 | every `recycles` id exists and is earlier | |
| extra | 2-4 concepts; ids unique | |

## `tools/check_level.py <level.toml> [...]`

For each file: load (loader errors become one line), compare with
`concepts.toml` (id exists, same title, world, boss flag, `new_concepts`,
power-up), run the per-item rules, rule 1 on every code field, the style
limits, then run each wave's reference through `grade_wave` (must pass, and a
build wave must have full code quality) and each wrong solution (must fail).
A predict wave uses `answer` and `wrong`. Output is `PASS <id>` or
`FAIL <id>` and then one short line per problem, with no tracebacks.
Exit code 0 only if every file passes. A folder is accepted for a file. With
no arguments it checks every `levels/w*/*/level.toml`.

## `tools/level_brief.py <level-id>`

Prints at most 40 lines of plain text: id, title, world, difficulty,
concepts, story, mission, power-up, outcomes, recycled levels (id and
title) and the cumulative allowed constructs. Constructs are grouped by kind
(`nodes`, `call`, `method`, ...) and wrapped, and the ones this level adds
are marked with `*`. An unknown id prints one line and exits with 1.

## Changes to existing code and tests

- `tests/test_levels.py` imports its limits and helpers from
  `grader/level_limits.py` instead of defining them, and uses the World 3
  debug limit (30 lines from World 3) that the style guide now says. It still
  does not check the number of bugs: a machine cannot count them.
- `CLAUDE.md`: `tools/` joins the folder layout.
- `docs/level-style-guide.md`: a short "Checking a level" section.

## Tests (written first)

`tests/test_constructs.py`, `tests/test_progression.py`,
`tests/test_level_limits.py`, `tests/test_check_level.py`,
`tests/test_level_brief.py`. They include: every real level in `levels/`
passes `check_level`; the real `concepts.toml` passes every rule; a level
that uses a later construct, an unlisted one, a wrong solution that passes,
and a reference that fails are each reported.
