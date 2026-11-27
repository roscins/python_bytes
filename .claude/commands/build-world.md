Build world $ARGUMENTS on branch world-$ARGUMENTS:
1. For each item of the world in levels/concepts.toml, run
   `python tools/level_brief.py <id>` and give the brief to level-writer.
2. Failed levels go to level-fixer; if still failing, fix them yourself.
3. Build the boss sprite in the art style guide's format.
4. When all pass, run world-reviewer and show its findings. Wait for OK.
5. Apply approved findings, run all tests, update docs/plan.md boxes,
   open a PR. Do not merge.
