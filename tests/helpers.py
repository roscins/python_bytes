"""Small helpers shared by several test files."""

import os
import tempfile


def write_temporary_file(test, text, suffix=".txt"):
    """Write `text` to a temporary file, delete it after `test`, return its path."""
    handle, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(handle, "w", encoding="utf-8") as temporary_file:
        temporary_file.write(text)
    test.addCleanup(os.remove, path)
    return path


def make_level(level_id, title=None):
    """Return a small Level for tests that only need an id and a title.

    The title is "Level <id>" unless one is given.
    """
    # Imported here so tests that do not use levels do not need the engine.
    from engine.level_pack import Level, Wave

    if title is None:
        title = f"Level {level_id}"
    wave = Wave("build", "Print OK.", reference='print("OK")', wrong="print(OK)")
    return Level(level_id, title, 1, ["print()", "strings"], "status",
                 'print("OK")', ["tip one", "tip two"], [wave])


def make_levels(*level_ids):
    """Return a list of small Levels, one for each id given."""
    levels = []
    for level_id in level_ids:
        levels.append(make_level(level_id))
    return levels


def make_temporary_folder(test):
    """Make an empty temporary folder, delete it after `test`, return its path."""
    from pathlib import Path

    folder = tempfile.TemporaryDirectory()
    test.addCleanup(folder.cleanup)
    return Path(folder.name)


# A small level.toml that follows the level style guide's structure. Tests
# change parts of it to make broken files.
VALID_LEVEL_TOML = '''
[level]
id = "1-1"
title = "Hello, Terminal"
world = 1
new_concepts = ["print()", "string literals"]
power_up = "status"
cutscene = """
print("SYSTEM CHECK")
"""
tips = ["print(...) shows text.", "Text in quotes is a string literal."]

[[wave]]
kind = "build"
brief = "Print OK."
reference = 'print("OK")'
wrong = "print(OK)"

[[wave.test]]
expected_stdout = "OK\\n"

[[wave]]
kind = "debug"
mode = "predict"
brief = "What does this print?"
code = 'print("ONE")'
answer = "ONE"
wrong = "TWO"
'''


def write_level_pack(levels_folder, world_folder, level_folder, text=VALID_LEVEL_TOML):
    """Write `text` to levels_folder/world_folder/level_folder/level.toml.

    Returns the path of the new level.toml file.
    """
    folder = levels_folder / world_folder / level_folder
    folder.mkdir(parents=True)
    path = folder / "level.toml"
    path.write_text(text, encoding="utf-8")
    return path
