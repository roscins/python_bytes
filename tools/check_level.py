"""Check level files: does each level keep the rules of the curriculum and the style guide?

Usage:
    python tools/check_level.py [level.toml-or-folder ...]

For every level file the tool
  1. loads it with the level loader,
  2. compares it with its entry in levels/concepts.toml,
  3. checks the curriculum rules that concern one level (docs/curriculum.md),
     including rule 1 on all of the level's code,
  4. checks the limits of docs/level-style-guide.md,
  5. runs every reference solution (it must pass) and every wrong solution
     (it must fail) through the game's runner and grader.

It prints "PASS <id>", or "FAIL <id>" with one short line per problem.
The exit code is 0 if every level passes, 1 otherwise. With no arguments it
checks every level pack under levels/.
"""

import sys
from pathlib import Path

# Make the game's packages importable when this file is run as a script.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
if str(PROJECT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_FOLDER))

from engine.level_pack import LevelError, load_level  # noqa: E402
from grader.level_limits import check_limits  # noqa: E402
from grader.progression import (  # noqa: E402
    check_item,
    check_level_code,
    check_level_matches,
    load_curriculum,
)
from grader.wave_grader import grade_wave  # noqa: E402

LEVELS_FOLDER = PROJECT_FOLDER / "levels"
LEVEL_FILE_NAME = "level.toml"
MAX_LINE_LENGTH = 110


def shorten(text):
    """Return `text` on one line, cut to MAX_LINE_LENGTH characters."""
    text = " ".join(text.split())
    if len(text) > MAX_LINE_LENGTH:
        text = text[:MAX_LINE_LENGTH - 3] + "..."
    return text


def level_file_for(argument):
    """Return the path of the level file for a command-line argument.

    The argument may be the file itself or the folder that holds it.
    """
    path = Path(argument)
    if path.is_dir():
        return path / LEVEL_FILE_NAME
    return path


def load_problem(error, path):
    """Return a loader error as one short text, without the file's path."""
    message = str(error).replace(str(path), "", 1)
    return "load: " + message.lstrip(": ,")


def failed_checks_summary(result):
    """Describe a graded wave that failed: how many checks failed, and the first one."""
    failed = []
    for check in result.checks:
        if not check.passed:
            failed.append(check)
    if not failed:
        return "no check passed"
    first = failed[0]
    return f"{len(failed)} of {result.test_count()} checks fail, first: {first.name}: {first.message}"


def failed_quality_rules(result):
    """Return the names of the code-quality rules a graded wave broke."""
    names = []
    for rule in result.quality:
        if not rule.passed:
            names.append(rule.name)
    return ", ".join(names)


def check_wave_solutions(number, wave):
    """Run one wave's right and wrong solution; return the problems found."""
    place = f"wave {number} ({wave.kind})"
    if wave.mode == "predict":
        right_text, right_name = wave.answer, "answer"
        wrong_text, wrong_name = wave.wrong, "wrong answer"
    else:
        right_text, right_name = wave.reference, "reference"
        wrong_text, wrong_name = wave.wrong, "wrong solution"

    problems = []
    right = grade_wave(wave, right_text)
    if not right.all_passed():
        problems.append(f"{place} {right_name} fails: {failed_checks_summary(right)}")
    elif right.quality is not None and right.quality_share() < 1.0:
        problems.append(f"{place} {right_name} has less than full code quality: "
                        f"{failed_quality_rules(right)}")
    wrong = grade_wave(wave, wrong_text)
    if wrong.all_passed():
        problems.append(f"{place} {wrong_name} passes every test but must fail")
    return problems


def check_solutions(level):
    """Run the reference and wrong solution of every wave of `level`."""
    problems = []
    number = 0
    for wave in level.waves:
        number = number + 1
        problems.extend(check_wave_solutions(number, wave))
    return problems


def check_file(path, curriculum=None):
    """Check one level file; return (name, problems).

    The name is the level's id, or the path as given if the file cannot be
    loaded. No problems means the level passes.
    """
    path = Path(path)
    if not path.is_file():
        return str(path), ["file not found"]
    try:
        level = load_level(path)
    except LevelError as error:
        return str(path), [load_problem(error, path)]
    if curriculum is None:
        curriculum = load_curriculum()

    problems = []
    for problem in check_level_matches(curriculum, level):
        problems.append("concepts.toml: " + problem)
    if curriculum.find(level.id) is not None:
        for problem in check_item(curriculum, level.id):
            problems.append("concepts.toml: " + problem)
        problems.extend(check_level_code(curriculum, level))
    problems.extend(check_limits(level))
    problems.extend(check_solutions(level))
    return level.id, problems


def find_level_files(levels_folder):
    """Return the paths of every level file under `levels_folder`, in map order."""
    paths = []
    for path in sorted(Path(levels_folder).glob("w*/*/" + LEVEL_FILE_NAME)):
        paths.append(str(path))
    return paths


def main(argv=None, out=None, levels_folder=LEVELS_FOLDER):
    """Check the levels named in `argv` (or all of them) and print the result.

    Returns the exit code: 0 if every level passes, 1 otherwise.
    """
    if argv is None:
        argv = sys.argv[1:]
    if out is None:
        out = sys.stdout
    arguments = list(argv)
    if not arguments:
        arguments = find_level_files(levels_folder)
        if not arguments:
            print(f"No level packs found in {levels_folder}", file=out)
            return 1

    curriculum = load_curriculum()
    exit_code = 0
    for argument in arguments:
        name, problems = check_file(level_file_for(argument), curriculum)
        if problems:
            exit_code = 1
            print(f"FAIL {name}", file=out)
            for problem in problems:
                print("  " + shorten(problem), file=out)
        else:
            print(f"PASS {name}", file=out)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
