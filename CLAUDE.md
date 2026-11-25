# Python Bytes – instructions for Claude

Arcade-style, pixel-art terminal game that teaches Python. Full plan: docs/plan.md.

## Hard rules
- Python 3.12+, standard library ONLY. Never add dependencies.
- Follow the folder layout: engine/, render/, levels/, runner/, grader/, art/, tests/,
  tools/ (developer scripts: level_brief.py, check_level.py).
- Code must be readable by first-year students: clear names, docstrings on every
  function and class, no clever one-liners. World 7 uses this code as teaching material.
- Every change comes with tests in tests/ (unittest), and they must pass.
- Work on a branch, never on main. One roadmap checkbox per branch.
- docs/curriculum.md and levels/concepts.toml decide what each level teaches;
  never add a construct to a level that isn't listed there.

## How to work with me
- Plan first, and wait for my OK before writing code.
- After each change, explain what you did and why in a few sentences.
- If something in docs/plan.md is unclear or seems wrong, ask instead of guessing.
