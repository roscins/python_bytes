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


def make_full_level(**build_changes):
    """Return a small Level with the three waves of the style guide, breaking no limit.

    It is Level 1-1 in short: fill-in, build and predict-mode debug. Keyword
    arguments replace parts of the build wave (reference, wrong, starter).
    """
    from engine.level_pack import Level, Wave

    tests = [{"expected_stdout": "a\n"}, {"require": ["Call"]}]
    fill_in = Wave("fill-in", "Fill.", starter="print(___)", reference='print("a")',
                   wrong="print(a b)", tests=tests)
    build_parts = {"reference": 'print("a")', "wrong": 'print("b")', "starter": None}
    build_parts.update(build_changes)
    build = Wave("build", "Build.", tests=tests, **build_parts)
    debug = Wave("debug", "Predict.", mode="predict", code='print("a")', answer="a", wrong="b")
    return Level("1-1", "Hello, Terminal", 1, ["print()", "string literals", "comments"],
                 "status", '# >> Hi.\nprint("a")', ["t1", "t2", "t3"], [fill_in, build, debug])


def world_of(level_id):
    """Return the world number of an id like "2-3" or "boss-2"."""
    if level_id.startswith("boss-"):
        return int(level_id.split("-")[1])
    return int(level_id[0])


def concepts_toml_text(*level_ids):
    """Return the text of a small concepts.toml with one item for each id.

    Every item adds one made-up construct, so it is a valid file for the
    loader. An id like "boss-1" becomes a boss.
    """
    lines = ['[meta]', 'version = 2', 'levels_per_world = 5', 'outcome_codes = ["B1"]', ""]
    for level_id in level_ids:
        lines.append("[[level]]")
        lines.append(f'id = "{level_id}"')
        lines.append(f"world = {world_of(level_id)}")
        lines.append(f'title = "Title {level_id}"')
        if level_id.startswith("boss-"):
            lines.append("boss = true")
            lines.append("constructs = []")
        else:
            lines.append('concepts = ["one", "two"]')
            lines.append(f'constructs = ["construct:{level_id}"]')
            lines.append(f'power_up = "up-{level_id}"')
        lines.append("recycles = []")
        lines.append("difficulty = 1")
        lines.append('outcomes = ["B1"]')
        lines.append('mission = "Do something."')
        lines.append("")
    return "\n".join(lines)


def make_curriculum_of(*level_ids):
    """Return a Curriculum with one item for each id, in the order given."""
    import tomllib

    from grader.progression import parse_curriculum

    return parse_curriculum(tomllib.loads(concepts_toml_text(*level_ids)))


def type_code(state, code):
    """Replace the code of the current wave by `code`, typed line by line as a player would."""
    from engine.commands import handle_line

    handle_line(state, ":clear")
    for line in code.splitlines():
        handle_line(state, line)


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


def make_boss_level(level_id="boss-1", time_limit=600):
    """Return a small boss Level whose one wave has three hidden tests.

    The task: write add(a, b) that returns a + b. The reference passes all
    three tests; the wrong solution (a - b) passes only add(2, 0).
    """
    from engine.level_pack import Level, Wave

    tests = [
        {"call": "add", "args": [2, 0], "expected": 2},
        {"call": "add", "args": [2, 3], "expected": 5},
        {"call": "add", "args": [1, 1], "expected": 2},
    ]
    reference = 'def add(a, b):\n    """Add."""\n    return a + b\n'
    wrong = 'def add(a, b):\n    """Add."""\n    return a - b\n'
    wave = Wave("boss", "Write add(a, b).", reference=reference, wrong=wrong, tests=tests)
    return Level(level_id, "The Test Boss", 1, [], "", "# >> The boss wakes.", [], [wave],
                 boss=True, time_limit=time_limit, sprite="boss-placeholder")


class FakeClock:
    """A clock for tests: it says the time is `now`, which a test moves by hand."""

    def __init__(self):
        """Start the clock at 0 seconds."""
        self.now = 0.0

    def __call__(self):
        """Return the current pretend time, like time.monotonic() would."""
        return self.now


# A small boss level.toml, as the loader reads it.
VALID_BOSS_TOML = '''
[level]
id = "boss-1"
title = "The Test Boss"
world = 1
boss = true
time_limit = 300
cutscene = """
# >> The screen flickers red.
"""

[[wave]]
kind = "boss"
brief = "Print OK."
reference = 'print("OK")'
wrong = "print(OK)"

[[wave.test]]
expected_stdout = "OK\\n"
'''
