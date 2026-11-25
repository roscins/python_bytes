"""Print a short brief for one level, to paste into a model's context.

Usage:
    python tools/level_brief.py <level-id>        for example: 3-2 or boss-4

The brief says what the level is about and which constructs its code may
use: everything added up to and including this level, with the ones this
level adds marked by a star. It reads levels/concepts.toml and prints at
most about 40 lines of plain text.
"""

import sys
import textwrap
from pathlib import Path

# Make the game's packages importable when this file is run as a script.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
if str(PROJECT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_FOLDER))

from grader.progression import load_curriculum  # noqa: E402
from render.world_map import WORLD_NAMES  # noqa: E402

WIDTH = 100
NEW_MARK = "*"

# Construct kinds that are written "kind:name". Everything else is a syntax
# node, such as While or Compare:Eq.
KINDS = ["call", "method", "import", "decorator", "dunder", "pattern"]
GROUPS = ["nodes"] + KINDS


def split_construct(construct):
    """Return (group, name) for a construct, for example ("call", "round")."""
    prefix, colon, rest = construct.partition(":")
    if colon and prefix in KINDS:
        return prefix, rest
    return "nodes", construct


def wrapped(label, text):
    """Return `label` and `text` as lines no wider than WIDTH, indenting the later lines."""
    return textwrap.wrap(
        label + text,
        width=WIDTH,
        subsequent_indent=" " * len(label),
        break_on_hyphens=False,
        break_long_words=False,
    )


def construct_lines(curriculum, item):
    """Return the lines that list the constructs `item` may use, grouped by kind."""
    new = curriculum.new_constructs(item.id)
    names = {}
    for group in GROUPS:
        names[group] = []
    for construct, _ in curriculum.allowed_constructs(item.id):
        group, name = split_construct(construct)
        if construct in new:
            name = name + NEW_MARK
        names[group].append(name)

    if item.boss:
        lines = ["Allowed constructs (everything so far; a boss adds none):"]
    else:
        lines = [f"Allowed constructs (everything so far; {NEW_MARK} = added by this level):"]
    for group in GROUPS:
        if names[group]:
            lines.extend(wrapped(f"  {group}: ", ", ".join(names[group])))
    return lines


def recycle_text(curriculum, item):
    """Return the recycled levels as "id Title; id Title", or "none"."""
    parts = []
    for other_id in item.recycles:
        other = curriculum.find(other_id)
        parts.append(f"{other.id} {other.title}")
    if not parts:
        return "none"
    return "; ".join(parts)


def brief_lines(curriculum, level_id):
    """Return the brief of one level as a list of lines. Raises KeyError for an unknown id."""
    item = curriculum.find(level_id)
    if item is None:
        raise KeyError(level_id)

    world_name = WORLD_NAMES.get(item.world, "")
    if item.boss:
        number = item.id.split("-")[1]
        lines = [f"BOSS {number} ({item.id}): {item.title}"]
        power_up = "none (a boss earns no power-up)"
    else:
        lines = [f"LEVEL {item.id}: {item.title}"]
        power_up = item.power_up
    lines.append(f"World {item.world} ({world_name}) | Difficulty: {item.difficulty} | Power-up: {power_up}")
    lines.extend(wrapped("Outcomes: ", ", ".join(item.outcomes)))

    if item.boss:
        lines.append("Concepts: none (a boss teaches nothing new)")
    else:
        lines.extend(wrapped("Concepts: ", "; ".join(item.concepts)))
    if item.technique:
        lines.append("Kind: technique level (teaches a method, not new syntax)")
    if item.story:
        lines.extend(wrapped("Story: ", item.story))
    lines.extend(wrapped("Mission: ", item.mission))
    lines.extend(wrapped("Recycles: ", recycle_text(curriculum, item)))
    lines.extend(construct_lines(curriculum, item))
    return lines


def main(argv=None, out=None):
    """Print the brief of the level named in `argv`. Returns the exit code (0 or 1)."""
    if argv is None:
        argv = sys.argv[1:]
    if out is None:
        out = sys.stdout
    if len(argv) != 1:
        print("Usage: python tools/level_brief.py <level-id>, for example 3-2 or boss-4", file=out)
        return 1
    curriculum = load_curriculum()
    try:
        lines = brief_lines(curriculum, argv[0])
    except KeyError:
        print(f"There is no level {argv[0]} in levels/concepts.toml.", file=out)
        return 1
    for line in lines:
        print(line, file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
