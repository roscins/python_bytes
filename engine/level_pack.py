"""Read level packs: one level.toml file per level, inside levels/w<world>/.

A level pack holds everything one level needs: its title, the story
cutscene, the tips, and the waves of tasks with their tests. See
docs/level-style-guide.md for what goes in a level.toml file.

This module only checks the structure of a level, so the game never crashes
on a broken file. The style guide's content rules (line limits, number of
tests, and so on) are checked by tests/test_levels.py.
"""

import ast
import tomllib
from pathlib import Path

from grader.checks import TEST_KINDS

# The three kinds of wave a level can have, in the order the guide lists them.
WAVE_KINDS = ["fill-in", "build", "debug"]

# A boss level has exactly one wave, of this kind.
BOSS_WAVE_KIND = "boss"

# What a boss level gets when it leaves these out.
DEFAULT_BOSS_TIME_LIMIT = 600           # seconds
DEFAULT_BOSS_SPRITE = "boss-placeholder"

# A wave with hints has exactly this many: a nudge, an outline and a partial solution.
HINT_COUNT = 3

# How many new concepts one level may teach.
MIN_NEW_CONCEPTS = 2
MAX_NEW_CONCEPTS = 4


class LevelError(ValueError):
    """A level.toml file that cannot be used, for example with a missing title."""


class Wave:
    """One wave of tasks in a level.

    Attributes:
        kind: "fill-in", "build" or "debug".
        brief: the task, as the player reads it.
        mode: for debug waves, "predict" or None.
        starter: code the player starts from (fill-in waves), or None.
        code: code the player reads (predict waves), or None.
        reference: a solution that must pass, or None for predict waves.
        wrong: a typical mistake that must fail.
        answer: the right output (predict waves), or None.
        tests: a list of dicts, one per [[wave.test]] in the file.
        hints: the wave's three hints (nudge, outline, partial solution),
            or an empty list if it has none.
        time_limit: how many seconds the player's program may run in this
            wave, or None for the runner's default.
        explanation: why a predict wave's answer is right, or None.
        goal: the wave's task in one short line, or None.
    """

    def __init__(self, kind, brief, mode=None, starter=None, code=None,
                 reference=None, wrong=None, answer=None, tests=None, hints=None,
                 time_limit=None, explanation=None, goal=None):
        """Remember every part of the wave. Parts a wave does not have are None."""
        self.kind = kind
        self.brief = brief
        self.mode = mode
        self.starter = starter
        self.code = code
        self.reference = reference
        self.wrong = wrong
        self.answer = answer
        if tests is None:
            tests = []
        self.tests = list(tests)
        if hints is None:
            hints = []
        self.hints = list(hints)
        self.time_limit = time_limit
        self.explanation = explanation
        self.goal = goal


class Level:
    """One level, as read from its level.toml file.

    Attributes:
        id: the level id, for example "1-1".
        title: the level's name, for example "Hello, Terminal".
        world: the world number, for example 1.
        new_concepts: the concepts this level teaches.
        power_up: the power-up the player earns.
        cutscene: the story scene, with working code in it.
        tips: one-line explanations, one per new concept.
        waves: a list of Wave objects.
        folder: the folder the level was read from, or None.
        boss: True for a boss fight.
        time_limit: a boss fight's time limit in seconds (None for levels).
        sprite: the name of a boss's sprite file in art/ (None for levels).
    """

    def __init__(self, level_id, title, world, new_concepts, power_up,
                 cutscene, tips, waves, folder=None, boss=False, time_limit=None,
                 sprite=None):
        """Remember every part of the level."""
        self.id = level_id
        self.title = title
        self.world = world
        self.new_concepts = list(new_concepts)
        self.power_up = power_up
        self.cutscene = cutscene
        self.tips = list(tips)
        self.waves = list(waves)
        self.folder = folder
        self.boss = boss
        self.time_limit = time_limit
        self.sprite = sprite


def load_level(path):
    """Read one level.toml file and return a Level.

    Raises LevelError, naming the file, if the file is not valid TOML or
    if a part of the level is missing or has the wrong type.
    """
    path = Path(path)
    try:
        with open(path, "rb") as level_file:
            data = tomllib.load(level_file)
    except tomllib.TOMLDecodeError as error:
        raise LevelError(f"{path}: not valid TOML: {error}") from error

    if "level" not in data or not isinstance(data["level"], dict):
        raise LevelError(f"{path}: the file needs a [level] table")
    table = data["level"]

    level_id = get_text(table, "id", path)
    title = get_text(table, "title", path)
    cutscene = get_text(table, "cutscene", path)
    world = get_whole_number(table, "world", path)
    boss = table.get("boss", False)
    if not isinstance(boss, bool):
        raise LevelError(f"{path}: boss must be true or false")

    if boss:
        # A boss teaches nothing new, so concepts, tips and a power-up are optional.
        power_up = ""
        new_concepts = []
        tips = []
        time_limit = DEFAULT_BOSS_TIME_LIMIT
        if "time_limit" in table:
            time_limit = get_whole_number(table, "time_limit", path)
        sprite = DEFAULT_BOSS_SPRITE
        if "sprite" in table:
            sprite = get_text(table, "sprite", path)
    else:
        power_up = get_text(table, "power_up", path)
        new_concepts = get_list_of_text(table, "new_concepts", path)
        tips = get_list_of_text(table, "tips", path)
        time_limit = None
        sprite = None
        if len(new_concepts) < MIN_NEW_CONCEPTS or len(new_concepts) > MAX_NEW_CONCEPTS:
            raise LevelError(
                f"{path}: a level has {MIN_NEW_CONCEPTS} to {MAX_NEW_CONCEPTS} new concepts, "
                f"this one has {len(new_concepts)}"
            )
        if len(tips) != len(new_concepts):
            raise LevelError(
                f"{path}: there must be one tip per new concept, "
                f"but there are {len(tips)} tips and {len(new_concepts)} concepts"
            )
    if not path.parent.name.startswith(level_id + "-"):
        raise LevelError(
            f"{path}: the folder name must start with the level id, "
            f"for example {level_id}-short-name"
        )

    if "wave" not in data or not isinstance(data["wave"], list) or not data["wave"]:
        raise LevelError(f"{path}: the level needs at least one [[wave]]")
    waves = []
    wave_number = 0
    allowed_kinds = WAVE_KINDS
    if boss:
        allowed_kinds = [BOSS_WAVE_KIND]
        if len(data["wave"]) != 1:
            raise LevelError(f"{path}: a boss level has exactly one [[wave]]")
    for wave_table in data["wave"]:
        wave_number = wave_number + 1
        waves.append(make_wave(wave_table, f"{path}, wave {wave_number}", allowed_kinds))

    return Level(level_id, title, world, new_concepts, power_up,
                 cutscene, tips, waves, folder=path.parent, boss=boss,
                 time_limit=time_limit, sprite=sprite)


def make_wave(table, place, allowed_kinds=WAVE_KINDS):
    """Turn one [[wave]] table into a Wave, checking the parts it needs.

    `place` says which file and wave this is, for error messages.
    `allowed_kinds` are the kinds this level may use: the normal three, or
    only "boss" in a boss level.
    """
    kind = get_text(table, "kind", place)
    if kind not in allowed_kinds:
        raise LevelError(f"{place}: kind must be one of {allowed_kinds}, got {kind!r}")
    brief = get_text(table, "brief", place)

    mode = None
    if "mode" in table:
        mode = get_text(table, "mode", place)

    # A predict wave shows code and asks for its output, so it has an
    # answer instead of a reference solution. Every other wave has a
    # reference solution. Both kinds have a wrong solution.
    if mode == "predict":
        needed = ["code", "answer", "wrong"]
    else:
        needed = ["reference", "wrong"]
    for key in needed:
        get_text(table, key, place)

    tests = table.get("test", [])
    if not isinstance(tests, list):
        raise LevelError(f"{place}: tests must be written as [[wave.test]] tables")
    test_number = 0
    for test in tests:
        test_number = test_number + 1
        check_test(test, f"{place}, test {test_number}")

    explanation = None
    if "explanation" in table:
        explanation = get_text(table, "explanation", place)

    goal = None
    if "goal" in table:
        goal = get_text(table, "goal", place)

    hints = []
    if "hints" in table:
        hints = get_list_of_text(table, "hints", place)
        if len(hints) != HINT_COUNT:
            raise LevelError(f"{place}: a wave has {HINT_COUNT} hints (nudge, outline, "
                             f"partial solution), this one has {len(hints)}")

    time_limit = None
    if "time_limit" in table:
        time_limit = get_whole_number(table, "time_limit", place)
        if time_limit < 1:
            raise LevelError(f"{place}: time_limit must be at least 1 second")

    return Wave(
        kind,
        brief,
        mode=mode,
        starter=table.get("starter"),
        code=table.get("code"),
        reference=table.get("reference"),
        wrong=table.get("wrong"),
        answer=table.get("answer"),
        tests=tests,
        hints=hints,
        time_limit=time_limit,
        explanation=explanation,
        goal=goal,
    )


def check_test(test, place):
    """Raise LevelError if one [[wave.test]] table cannot be graded.

    A test has exactly one key from TEST_KINDS, which says what kind of test
    it is. require and forbid must name real Python AST node types, such as
    "While", and a call test needs an expected value.
    """
    kinds = []
    for kind in TEST_KINDS:
        if kind in test:
            kinds.append(kind)
    if len(kinds) != 1:
        raise LevelError(f"{place}: a test needs exactly one of {TEST_KINDS}, found {kinds}")
    kind = kinds[0]

    if kind in ("require", "forbid"):
        node_types = get_list_of_text(test, kind, place)
        for node_type in node_types:
            if not isinstance(getattr(ast, node_type, None), type):
                raise LevelError(f"{place}: {node_type!r} is not a Python AST node type")
    if kind == "call":
        get_text(test, "call", place)
        if "expected" not in test:
            raise LevelError(f"{place}: a call test needs an expected value")
        if "args" in test and not isinstance(test["args"], list):
            raise LevelError(f"{place}: args must be a list, like [1, 2]")
    if kind == "expected_stdout":
        get_text(test, "expected_stdout", place)
    if kind == "expected_stdout_contains":
        get_list_of_text(test, "expected_stdout_contains", place)
    if "stdin" in test:
        get_text(test, "stdin", place)
    if "values" in test:
        if kind not in ("expected_stdout", "expected_stdout_contains"):
            raise LevelError(f"{place}: values only goes with an output test")
        if not isinstance(test["values"], dict) or not test["values"]:
            raise LevelError(f"{place}: values must be a table, like {{ capacity = 400 }}")
        for value in test["values"].values():
            if not isinstance(value, (str, int, float, bool)):
                raise LevelError(f"{place}: a value must be text, a number, true or false")


def get_text(table, key, place):
    """Return table[key] if it is a string; otherwise raise LevelError."""
    if key not in table:
        raise LevelError(f"{place}: {key} is missing")
    value = table[key]
    if not isinstance(value, str):
        raise LevelError(f"{place}: {key} must be text in quotes")
    return value


def get_whole_number(table, key, place):
    """Return table[key] if it is a whole number; otherwise raise LevelError."""
    if key not in table:
        raise LevelError(f"{place}: {key} is missing")
    value = table[key]
    # True and False count as numbers in Python, so they are ruled out first.
    if isinstance(value, bool) or not isinstance(value, int):
        raise LevelError(f"{place}: {key} must be a whole number")
    return value


def get_list_of_text(table, key, place):
    """Return table[key] if it is a list of strings; otherwise raise LevelError."""
    if key not in table:
        raise LevelError(f"{place}: {key} is missing")
    value = table[key]
    if not isinstance(value, list):
        raise LevelError(f"{place}: {key} must be a list, like [\"a\", \"b\"]")
    for item in value:
        if not isinstance(item, str):
            raise LevelError(f"{place}: every item in {key} must be text in quotes")
    return value


def load_levels(folder):
    """Read every level in `folder` and return them as a list, in map order.

    Levels live in folder/w<world>/<level-id>-<short-name>/level.toml. They
    are read in folder-name order, so 1-1-... comes before 1-2-... and
    boss-1-.... A folder that does not exist gives an empty list.

    Raises LevelError if a level is broken or two levels have the same id.
    """
    folder = Path(folder)
    levels = []
    seen_ids = []
    for path in sorted(folder.glob("w*/*/level.toml")):
        level = load_level(path)
        if level.id in seen_ids:
            raise LevelError(f"{path}: level id {level.id} is used twice")
        seen_ids.append(level.id)
        levels.append(level)
    return levels
