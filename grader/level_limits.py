"""The limits of docs/level-style-guide.md, as a function a tool and the tests can call.

check_limits(level) returns a list of problems, one line each. An empty
list means the level keeps every limit. The limits that a machine cannot
count, such as the number of bugs in a debug wave, are not checked.
"""

import re

from grader.wave_grader import BLANK

# The waves every normal level has, in this order. A boss has one boss wave.
WAVE_ORDER = ["fill-in", "build", "debug"]
MAX_CUTSCENE_LINES = 25
MIN_BLANKS = 1
MAX_BLANKS = 3
MAX_BRIEF_SENTENCES = 5
MIN_TESTS_PER_WAVE = 2
MAX_GOAL_LENGTH = 60
STORY_MARK = "# >>"

# A debug wave holds at most this much code: 10 lines, and from World 3, 30.
MAX_DEBUG_LINES = 10
MAX_DEBUG_LINES_FROM_WORLD_THREE = 30
FIRST_BIG_DEBUG_WORLD = 3

# Words the guide says never to use, because a task may not feel easy.
FORBIDDEN_WORDS = ["easy", "simple"]


def count_lines(text):
    """Return how many lines `text` has, not counting blank lines at its ends."""
    return len(text.strip().splitlines())


def count_sentences(text):
    """Return roughly how many sentences `text` has.

    A sentence ends with ".", "!" or "?" followed by a space or the end of
    the text. Good enough for briefs, which are plain English.
    """
    return len(re.findall(r"[.!?](\s|$)", text.strip()))


def is_valid_python(code):
    """Return True if `code` is Python that compiles, False otherwise."""
    try:
        compile(code, "<level>", "exec")
    except SyntaxError:
        return False
    return True


def max_debug_lines(world):
    """Return how many lines of code a debug wave in `world` may have."""
    if world >= FIRST_BIG_DEBUG_WORLD:
        return MAX_DEBUG_LINES_FROM_WORLD_THREE
    return MAX_DEBUG_LINES


def wave_place(number, wave):
    """Return how problems name a wave, for example "wave 2 (build)"."""
    return f"wave {number} ({wave.kind})"


def player_texts(level):
    """Return every piece of text in `level` that the player reads, with its place."""
    texts = [("title", level.title), ("cutscene", level.cutscene)]
    for index in range(len(level.tips)):
        texts.append((f"tip {index + 1}", level.tips[index]))
    number = 0
    for wave in level.waves:
        number = number + 1
        place = wave_place(number, wave)
        texts.append((place + " brief", wave.brief))
        if wave.goal is not None:
            texts.append((place + " goal", wave.goal))
        for hint in wave.hints:
            texts.append((place + " hint", hint))
    return texts


def plural(count, word):
    """Return "1 test" or "2 tests"."""
    if count == 1:
        return f"{count} {word}"
    return f"{count} {word}s"


def check_cutscene(level):
    """Return the problems of the cutscene: length, story line and Python."""
    problems = []
    lines = count_lines(level.cutscene)
    if lines > MAX_CUTSCENE_LINES:
        problems.append(f"cutscene has {lines} lines (at most {MAX_CUTSCENE_LINES})")
    if STORY_MARK not in level.cutscene:
        problems.append(f"cutscene has no {STORY_MARK} story line")
    if not is_valid_python(level.cutscene):
        problems.append("cutscene is not valid Python")
    return problems


def check_wave(world, number, wave):
    """Return the problems of one wave, whatever its kind."""
    place = wave_place(number, wave)
    problems = []
    if wave.mode == "predict":
        if wave.answer.strip() == wave.wrong.strip():
            problems.append(f"{place} answer and wrong are the same")
        if not is_valid_python(wave.code):
            problems.append(f"{place} code is not valid Python")
    else:
        if wave.reference.strip() == wave.wrong.strip():
            problems.append(f"{place} wrong solution is the same as the reference")
        if not is_valid_python(wave.reference):
            problems.append(f"{place} reference is not valid Python")
        test_count = len(wave.tests)
        if test_count < MIN_TESTS_PER_WAVE:
            problems.append(f"{place} has {plural(test_count, 'test')} "
                            f"(at least {MIN_TESTS_PER_WAVE})")

    if wave.goal is None or wave.goal.strip() == "":
        problems.append(f"{place} has no goal")
    elif len(wave.goal) > MAX_GOAL_LENGTH or "\n" in wave.goal:
        problems.append(f"{place} goal must be one line of at most {MAX_GOAL_LENGTH} characters")
    if wave.kind == "fill-in":
        problems.extend(check_fill_in(place, wave))
    if wave.kind == "build":
        sentences = count_sentences(wave.brief)
        if sentences > MAX_BRIEF_SENTENCES:
            problems.append(f"{place} brief has {sentences} sentences (at most {MAX_BRIEF_SENTENCES})")
    if wave.kind == "debug":
        problems.extend(check_debug_size(world, place, wave))
    return problems


def check_fill_in(place, wave):
    """Return the problems of a fill-in wave's blanks."""
    problems = []
    if wave.starter is None:
        return [f"{place} has no starter"]
    blanks = wave.starter.count(BLANK)
    if blanks < MIN_BLANKS or blanks > MAX_BLANKS:
        problems.append(f"{place} starter has {plural(blanks, 'blank')} "
                        f"({MIN_BLANKS} to {MAX_BLANKS} needed)")
    if wave.reference is not None and BLANK in wave.reference:
        problems.append(f"{place} reference still has a {BLANK} blank")
    return problems


def check_debug_size(world, place, wave):
    """Return a problem if a debug wave's code is longer than the world allows."""
    if wave.mode == "predict":
        code = wave.code
    else:
        code = wave.starter
    if code is None:
        return [f"{place} has no code"]
    lines = count_lines(code)
    limit = max_debug_lines(world)
    if lines > limit:
        return [f"{place} code has {lines} lines (at most {limit} in world {world})"]
    return []


def check_words(level):
    """Return a problem for every forbidden word the player would read."""
    problems = []
    for place, text in player_texts(level):
        for word in FORBIDDEN_WORDS:
            if re.search(rf"\b{word}\b", text, re.IGNORECASE):
                problems.append(f'{place} uses the word "{word}"')
    return problems


def check_limits(level):
    """Return the style guide problems of `level`, one line each (empty if none)."""
    problems = []
    if level.folder is not None and level.folder.parent.name != f"w{level.world}":
        problems.append(f"a level of world {level.world} belongs in a folder w{level.world}/")
    problems.extend(check_cutscene(level))

    kinds = []
    for wave in level.waves:
        kinds.append(wave.kind)
    if not level.boss and kinds != WAVE_ORDER:
        problems.append("waves must be fill-in, build, debug, in that order")

    number = 0
    for wave in level.waves:
        number = number + 1
        problems.extend(check_wave(level.world, number, wave))
    problems.extend(check_words(level))
    return problems
