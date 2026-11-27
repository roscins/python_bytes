"""Read level packs: one level.toml file per level, inside levels/w<world>/.

A level pack holds everything one level needs: its title, the story
cutscene, the tips, and the waves of tasks with their tests. See
docs/level-style-guide.md for what goes in a level.toml file.

This module only checks the structure of a level, so the game never crashes
on a broken file. The style guide's content rules (line limits, number of
tests, and so on) are checked by tests/test_levels.py.
"""

import ast
import re
import tomllib
from pathlib import Path

from grader.answer_sheet import LETTERS, fault_sheet, key_sheet
from grader.checks import TEST_KINDS

# The three kinds of wave a level can have, in the order the guide lists them.
WAVE_KINDS = ["fill-in", "build", "debug"]

# The ways a wave can be answered without writing code. A quiz wave is
# answered with an answer sheet (see grader/answer_sheet.py).
MODES = ["predict", "choice", "review"]
QUIZ_MODES = ["choice", "review"]

# Quiz modes are only for these kinds of wave: a build wave scores code
# quality, and a boss is graded by tests.
QUIZ_KINDS = ["fill-in", "debug"]

MIN_QUESTIONS, MAX_QUESTIONS = 1, 6
MIN_OPTIONS, MAX_OPTIONS = 2, len(LETTERS)
MIN_FAULTS, MAX_FAULTS = 1, 4

# A data file has a plain name: no folders, and not a name the runner uses.
DATA_FILE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
RESERVED_FILE_NAMES = ["call.json", "catch.json"]
MAX_DATA_FILE_BYTES = 100_000
# The folder of a level that holds its data files.
DATA_FOLDER = "files"

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
        mode: "predict", "choice", "review" or None (the player writes code).
        starter: code the player starts from (fill-in waves), or None.
        code: code the player reads (predict and review waves), or None.
        reference: a solution that must pass, or None for predict waves.
        wrong: a typical mistake that must fail.
        answer: the right output (predict waves) or the right answer sheet
            (quiz waves), or None.
        questions: a choice wave's questions, dicts with "ask", "options",
            "answer", "explanation" and optionally "code".
        faults: a review wave's faults, dicts with "line", "category" and
            "explanation".
        categories: what a review wave's faults can be called.
        files: {name: text} of the data files the wave's code can open.
        lock: True if the console is locked while this wave is open.
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
                 time_limit=None, explanation=None, goal=None, questions=None,
                 lock=False, faults=None, categories=None, files=None):
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
        self.questions = list(questions or [])
        self.lock = lock
        self.faults = list(faults or [])
        self.categories = list(categories or [])
        self.files = dict(files or {})

    def code_lines(self):
        """Return the lines of the code the player reads, numbered from 1 in a review."""
        return (self.code or "").strip().splitlines()

    def takes_comments(self):
        """Return True if the player may comment on the lines of this review wave."""
        return any("model_comment" in fault for fault in self.faults)

    def is_quiz(self):
        """Return True if the wave is answered with an answer sheet."""
        return self.mode in QUIZ_MODES

    def locks_console(self):
        """Return True if running code would give this wave's answer away."""
        if self.mode == "predict" or self.lock:
            return True
        for question in self.questions:
            if "code" in question:
                return True
        return False


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
        waves.append(make_wave(wave_table, f"{path}, wave {wave_number}", allowed_kinds,
                               path.parent))

    return Level(level_id, title, world, new_concepts, power_up,
                 cutscene, tips, waves, folder=path.parent, boss=boss,
                 time_limit=time_limit, sprite=sprite)


def make_wave(table, place, allowed_kinds=WAVE_KINDS, folder=None):
    """Turn one [[wave]] table into a Wave, checking the parts it needs.

    `place` says which file and wave this is, for error messages.
    `allowed_kinds` are the kinds this level may use: the normal three, or
    only "boss" in a boss level. `folder` is the level's folder, where its
    data files are.
    """
    kind = get_text(table, "kind", place)
    if kind not in allowed_kinds:
        raise LevelError(f"{place}: kind must be one of {allowed_kinds}, got {kind!r}")
    brief = get_text(table, "brief", place)
    mode = get_mode(table, kind, place)
    check_needed_parts(table, mode, place)
    tests = get_tests(table, place, folder)

    answer = table.get("answer")
    questions = []
    faults = []
    categories = []
    if mode == "choice":
        questions = get_questions(table, place)
        answer = key_sheet(questions)
    if mode == "review":
        faults, categories = get_faults(table, place)
        answer = fault_sheet(faults)
    lock = table.get("lock", False)
    if not isinstance(lock, bool) or (lock and mode != "choice"):
        raise LevelError(f"{place}: lock must be true or false, and only a choice wave can set it")

    return Wave(
        kind,
        brief,
        mode=mode,
        starter=table.get("starter"),
        code=table.get("code"),
        reference=table.get("reference"),
        wrong=table.get("wrong"),
        answer=answer,
        tests=tests,
        hints=get_hints(table, place),
        time_limit=get_time_limit(table, place),
        explanation=get_optional_text(table, "explanation", place),
        goal=get_optional_text(table, "goal", place),
        questions=questions,
        lock=lock,
        faults=faults,
        categories=categories,
        files=get_data_files(table, place, folder),
    )


def get_mode(table, kind, place):
    """Return the wave's mode, or None for a wave the player answers with code."""
    if "mode" not in table:
        return None
    mode = get_text(table, "mode", place)
    if mode not in MODES:
        raise LevelError(f"{place}: mode must be one of {MODES}, got {mode!r}")
    if mode in QUIZ_MODES and kind not in QUIZ_KINDS:
        raise LevelError(f"{place}: a {mode} wave must be one of {QUIZ_KINDS}")
    return mode


def check_needed_parts(table, mode, place):
    """Raise LevelError if the wave lacks a part its mode needs.

    A predict wave shows code and asks for its output, so it has an answer
    instead of a reference solution. A quiz wave makes its answer from its
    questions or faults. Every other wave has a reference solution. All of
    them have a wrong solution.
    """
    if mode == "predict":
        needed = ["code", "answer", "wrong"]
    elif mode in QUIZ_MODES:
        needed = ["wrong"]
    else:
        needed = ["reference", "wrong"]
    for key in needed:
        get_text(table, key, place)


def get_tests(table, place, folder):
    """Return the wave's checked [[wave.test]] tables, each with the data files it runs with."""
    tests = table.get("test", [])
    if not isinstance(tests, list):
        raise LevelError(f"{place}: tests must be written as [[wave.test]] tables")
    test_number = 0
    for test in tests:
        test_number = test_number + 1
        check_test(test, f"{place}, test {test_number}")
    files = get_data_files(table, place, folder)
    for test in tests:
        add_data(test, files, place, folder)
    return tests


def get_optional_text(table, key, place):
    """Return table[key] if it is there (it must be text), or None."""
    if key not in table:
        return None
    return get_text(table, key, place)


def get_hints(table, place):
    """Return the wave's three hints, or an empty list if it has none."""
    if "hints" not in table:
        return []
    hints = get_list_of_text(table, "hints", place)
    if len(hints) != HINT_COUNT:
        raise LevelError(f"{place}: a wave has {HINT_COUNT} hints (nudge, outline, "
                         f"partial solution), this one has {len(hints)}")
    return hints


def get_time_limit(table, place):
    """Return the wave's time limit in seconds, or None for the runner's default."""
    if "time_limit" not in table:
        return None
    time_limit = get_whole_number(table, "time_limit", place)
    if time_limit < 1:
        raise LevelError(f"{place}: time_limit must be at least 1 second")
    return time_limit


def read_data_file(name, place, folder):
    """Return the text of the data file `name` of the level in `folder`, checked."""
    if (not isinstance(name, str) or not DATA_FILE_NAME.fullmatch(name)
            or name.lower().endswith(".py") or name.lower() in RESERVED_FILE_NAMES):
        raise LevelError(f"{place}: {name!r} is not a plain data file name")
    if folder is None:
        raise LevelError(f"{place}: data files need a level folder")
    path = folder / DATA_FOLDER / name
    if not path.is_file():
        raise LevelError(f"{place}: there is no file {DATA_FOLDER}/{name}")
    if path.stat().st_size > MAX_DATA_FILE_BYTES:
        raise LevelError(f"{place}: {name} is larger than {MAX_DATA_FILE_BYTES} bytes")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise LevelError(f"{place}: {name} is not UTF-8 text") from error


def get_data_files(table, place, folder):
    """Return {name: text} for the wave's `files` list."""
    if "files" not in table:
        return {}
    files = {}
    for name in get_list_of_text(table, "files", place):
        files[name] = read_data_file(name, place, folder)
    return files


def add_data(test, files, place, folder):
    """Put the data files this test runs with in test["data"].

    A test's own `files` table puts another file under a wave file's name.
    """
    replaced = test.get("files", {})
    if not isinstance(replaced, dict):
        raise LevelError(f"{place}: a test's files must be a table")
    data = dict(files)
    for name, other in replaced.items():
        if name not in files:
            raise LevelError(f"{place}: a test replaces {name!r}, which the wave does not list")
        data[name] = read_data_file(other, place, folder)
    if data:
        test["data"] = data


def get_faults(table, place):
    """Return (faults, categories) of a review wave, checked."""
    line_count = len(get_text(table, "code", place).strip().splitlines())
    categories = get_list_of_text(table, "categories", place)
    if not MIN_OPTIONS <= len(categories) <= MAX_OPTIONS:
        raise LevelError(f"{place}: needs {MIN_OPTIONS} to {MAX_OPTIONS} categories")
    faults = table.get("fault", [])
    if not isinstance(faults, list) or not MIN_FAULTS <= len(faults) <= MAX_FAULTS:
        raise LevelError(f"{place}: a review wave has {MIN_FAULTS} to {MAX_FAULTS} "
                         "[[wave.fault]] tables")
    lines = []
    for number, fault in enumerate(faults, start=1):
        where = f"{place}, fault {number}"
        line = get_whole_number(fault, "line", where)
        if not 1 <= line <= line_count or line in lines:
            raise LevelError(f"{where}: line must be a line of the code, one fault per line")
        lines.append(line)
        get_text(fault, "explanation", where)
        get_optional_text(fault, "model_comment", where)
        if get_text(fault, "category", where) not in list(LETTERS[:len(categories)]):
            raise LevelError(f"{where}: category must be the letter of one of the categories")
    return faults, categories


def get_questions(table, place):
    """Return the checked [[wave.question]] tables of a choice wave."""
    questions = table.get("question", [])
    if not isinstance(questions, list) or not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        raise LevelError(f"{place}: a choice wave has {MIN_QUESTIONS} to {MAX_QUESTIONS} "
                         "[[wave.question]] tables")
    for number, question in enumerate(questions, start=1):
        where = f"{place}, question {number}"
        get_text(question, "ask", where)
        get_text(question, "explanation", where)
        if "code" in question:
            get_text(question, "code", where)
        options = get_list_of_text(question, "options", where)
        if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
            raise LevelError(f"{where}: needs {MIN_OPTIONS} to {MAX_OPTIONS} options")
        answer = get_text(question, "answer", where)
        if answer not in list(LETTERS[:len(options)]):
            raise LevelError(f"{where}: answer must be the letter of one of the options")
    return questions


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
    if kind == "require_call":
        get_list_of_text(test, "require_call", place)
    if kind == "require_plan" and get_whole_number(test, "require_plan", place) < 1:
        raise LevelError(f"{place}: require_plan must be at least 1")
    if kind == "catches":
        check_catches_table(test["catches"], place)
    if kind == "expected_file":
        wanted = test["expected_file"]
        if not isinstance(wanted, dict):
            raise LevelError(f"{place}: expected_file needs a name and contents")
        get_text(wanted, "contents", place)
        if not DATA_FILE_NAME.fullmatch(get_text(wanted, "name", place)):
            raise LevelError(f"{place}: expected_file needs a plain file name")
    if kind == "expected_stdout":
        get_text(test, "expected_stdout", place)
    if kind == "expected_stdout_contains":
        get_list_of_text(test, "expected_stdout_contains", place)
    if "stdin" in test:
        get_text(test, "stdin", place)
    if "values" in test:
        if kind not in ("expected_stdout", "expected_stdout_contains", "expected_file"):
            raise LevelError(f"{place}: values only goes with an output test")
        if not isinstance(test["values"], dict) or not test["values"]:
            raise LevelError(f"{place}: values must be a table, like {{ capacity = 400 }}")
        for value in test["values"].values():
            if not is_test_value(value):
                raise LevelError(
                    f"{place}: a value must be text, a number, true, false or a list of these")


def check_catches_table(wanted, place):
    """Raise LevelError unless a catches test names two usable versions of a function."""
    if not isinstance(wanted, dict):
        raise LevelError(f"{place}: catches needs test, function, correct and broken")
    for key in ["test", "function", "correct", "broken"]:
        get_text(wanted, key, place)
    for key in ["correct", "broken"]:
        try:
            tree = ast.parse(wanted[key])
        except SyntaxError as error:
            raise LevelError(f"{place}: {key} is not valid Python") from error
        names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        if wanted["function"] not in names:
            raise LevelError(f"{place}: {key} must define {wanted['function']}")


def is_test_value(value):
    """Return True if a test may give a variable this value."""
    items = value if isinstance(value, list) else [value]
    for item in items:
        if not isinstance(item, (str, int, float, bool)):
            return False
    return True


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
