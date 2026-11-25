# Phase 3 design: curriculum v1 (PR 1 of 2)

Branch `curriculum/v1`. The proposal in `docs/curriculum.md` and
`levels/concepts.toml` was reviewed, and the decisions below were approved.
This PR fixes the proposal and brings the other documents in line. The
progression checker itself is PR 2 (its own branch); no engine code changes
here.

## What this PR contains

- `docs/curriculum.md` and `levels/concepts.toml`: corrected, as one pair.
- `docs/plan.md`: 5 levels per world, 40 levels + 8 bosses, new level ids,
  new tables, roadmap changes.
- `docs/level-style-guide.md`: bigger debug waves from World 3, a `starter`
  field for build waves, optional wave `time_limit`, the `concepts` field,
  why `global` is never taught.
- `CLAUDE.md`: the rule that the curriculum decides what a level teaches.
- `tests/test_curriculum_data.py`: checks that the two files agree and that
  the data has the shape the checker will rely on.

Not in this PR (code, listed in the PR description): the map reading its ids
from `concepts.toml`, the loader accepting a wave `time_limit` and the
`boss-8` id, and `tests/test_levels.py` using the new debug limits.

## The construct grammar (what the checker will enforce in PR 2)

Decided, and written into section 6 of `docs/curriculum.md`:

- Always allowed: `Module`, `Load`, `Store`, `Expr`, and the name of a
  function that is being called (the call itself is still gated).
- `import:x` allows `import x`, `from x import ...` and everything `x.*`.
- `method:x` governs only built-in str, list, dict, set and file methods.
  Methods of user-defined classes and of library classes are free once the
  class or module is allowed.
- A bare node (`Compare`, `Match`) allows all its sub-forms. A level that
  wants to hold some back lists the sub-forms it allows instead
  (`Compare:Eq`, `Compare:Lt`, ...). `Compare:In` covers `not in`,
  `Compare:Is` covers `is not`.
- Rule 1 applies to cutscene code, fill-in starters, references and debug
  code. A wrong solution must comply only if it parses. Output text
  (`answer`, `wrong` of a predict wave, expected output) is never checked.
- A provided file in a level may set `exempt = true` (Boss 7 reviews the
  game's own code, which uses modules the player has not met).
- "Earlier" means file order in `concepts.toml`.

## Decisions on the errors found in the review

| Level | Fix | Why |
| --- | --- | --- |
| 1-4 | Adds the comparison operators (`Compare:Eq` ... `Compare:GtE`) | the level is about `==` on floats; `if` stays in 2-2 |
| 2-4 | `enumerate` moves to 3-5 | it needs tuple unpacking, which arrives in World 3 |
| World 3 | 3-1 lists, 3-2 functions I (+ `pass`), 3-3 functions II, 3-4 aliasing (+ `id`), 3-5 tuples, sets, `zip`, `enumerate` | `sorted`, `min`, `max` need lists first |
| 3-3 | Newton–Raphson moves here from 2-5 | 2-5 was four algorithms; here it is a function the player writes |
| Boss 4 | One file | multi-module work starts in 5-1 |
| World 4 | Recursion moves to 4-5 (last) | it was the hardest Basic level and sat in the middle |
| 4-5 | No nested-list flattening; call counts through return values or a mutable counter | flattening needs `isinstance` (6-1); counting calls with a counter needs `global`, which is never taught |
| 5-4 | Exact `__eq__` with `__hash__`, a separate `is_close()`, `__radd__`, `repr`, `hash` | a tolerance-based `__eq__` cannot have a consistent hash |
| 6-3 | Class-based context managers only | `@contextmanager` needs `yield` (7-2) |
| 7-2 | `*args`/`**kwargs`, `wraps`, `lru_cache`, `functools` | decorators cannot be written without them |
| builtins | `bool` 2-2, `join`/`startswith`/`isdigit` 1-5, exception constructors 4-2, `next` 4-3, `iter` 5-5, `breakpoint` 7-4, `del` 3-1, `IfExp` 7-1, `^` 3-5, `Pass` 3-2, `id` 3-4 | added where first needed |

`global` is never taught. The level style guide says why.

## Rules (curriculum.md section 6, as approved)

1. A level's code uses only constructs listed for that level or an earlier one.
2. Bosses add no constructs.
3. Every non-boss level adds at least one construct, unless `technique = true`.
4. Every outcome code appears in at least one non-boss level.
5. Inside a world difficulty never decreases; the boss is at least the
   world's maximum; a new world starts at or below the previous boss minus 1.
6. `recycles` names only items that come earlier in the file.

B12 is in 4-4 and R9 is in 5-1, so rule 4 holds.

## The `concepts` field

Each non-boss level has `concepts`: 2–4 headline concepts, the same limit
the loader already puts on `new_concepts`. Constructs stay fine-grained, so
one concept ("string methods") can be many constructs. `docs/curriculum.md`
shows the `concepts` text, so the two files cannot drift apart: the test
compares them.

## Where I used my own judgement (listed in the PR description)

- **World 4 order**: Catalogue, Fault Tolerance, Archive, Test Bench,
  Echo Chamber. This keeps the Test Bench at 4-4, where B12 was decided, and
  puts recursion last.
- **3-5 split**: `import:time`, timing and Big-O vocabulary move to 4-1,
  where "choosing a data structure" needs them.
- **5-4 split**: `__len__` and `__iter__` move to 5-5, where the Stack and
  Queue classes need them.
- **7-1/7-2/7-3 split**: `GeneratorExp` to 7-2; `contextlib` and `itertools`
  to 7-3 (the same context manager as a class and as a generator is the
  "two roads" example).
- **4-4 (B12)**: written answers stay in Worlds 7–8, so the review is graded
  by choosing the right feedback and the line holding the fault.
- **Boss 4** loses R9 (now 5-1) and keeps B11, B12, R5.
- **Power-ups** for every level, in `concepts.toml`.
- **Phase 6 gate** says "Level 5-1" (the first multi-file level), not 5-2.

## Checks

`tests/test_curriculum_data.py`: `concepts.toml` loads; 5 levels and a boss
in each of 8 worlds; ids unique and in order; 2–4 concepts per non-boss
level; power-ups unique; every row of the tables in `curriculum.md` matches
the file. The six rules themselves are PR 2.
