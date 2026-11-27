"""The answer sheet of a quiz wave: reading it, writing it and grading it.

A sheet is text with one answer per line, "number: letter", for example
"2: b". The number is a question (choice waves) or a code line (review
waves). The key screens write the sheet; in plain mode the player types it.
"""

import re

from grader.checks import CheckResult

# The letters of the options, in order.
LETTERS = "abcde"

SHEET_LINE = re.compile(r"\s*(\d+)\s*:\s*([a-zA-Z]?)\s*")


def read_sheet(text):
    """Return ({number: letter}, "") for a sheet, or ({}, why it cannot be read).

    A later line for the same number replaces an earlier one, and a line
    with no letter takes the answer away.
    """
    answers = {}
    for line in text.splitlines():
        if line.strip() == "":
            continue
        match = SHEET_LINE.fullmatch(line)
        if match is None:
            return {}, f"Write each answer as  number: letter, for example 1: a. Not: {line.strip()}"
        number = int(match.group(1))
        if match.group(2):
            answers[number] = match.group(2).lower()
        else:
            answers.pop(number, None)
    return answers, ""


def write_sheet(answers):
    """Return {number: letter} as the text of a sheet, in number order."""
    lines = []
    for number in sorted(answers):
        lines.append(f"{number}: {answers[number]}\n")
    return "".join(lines)


def choices_for(wave, number):
    """Return (the allowed letters for `number`, why the number is not allowed)."""
    if wave.mode == "review":
        if not 1 <= number <= len(wave.code_lines()):
            return "", f"The code has no line {number}."
        return LETTERS[:len(wave.categories)], ""
    if not 1 <= number <= len(wave.questions):
        return "", f"There is no question {number}."
    return LETTERS[:len(wave.questions[number - 1]["options"])], ""


def sheet_problem(wave, text):
    """Return why `text` cannot be graded for `wave`, or "" if it can.

    A review sheet may not mark more lines than there are faults, so that
    marking every line cannot score.
    """
    answers, problem = read_sheet(text)
    if problem:
        return problem
    if not answers:
        return "You have not answered yet. Answer first, then submit."
    if wave.mode == "review" and len(answers) > len(wave.faults):
        return f"Mark at most as many lines as there are faults: {len(wave.faults)}."
    for number, letter in answers.items():
        letters, problem = choices_for(wave, number)
        if problem:
            return problem
        if letter not in letters:
            return f"The letters for {number} are {', '.join(letters)}."
    return ""


def key_sheet(questions):
    """Return the right sheet for a list of questions."""
    answers = {}
    for number, question in enumerate(questions, start=1):
        answers[number] = question["answer"]
    return write_sheet(answers)


def fault_sheet(faults):
    """Return the right sheet for a list of faults."""
    answers = {}
    for fault in faults:
        answers[fault["line"]] = fault["category"]
    return write_sheet(answers)


def check(passed, name, message):
    """Return a CheckResult that has `message` only if it failed."""
    if passed:
        return CheckResult(True, name)
    return CheckResult(False, name, message)


def grade_sheet(wave, text):
    """Return the CheckResults of the sheet `text`.

    A choice wave has one check per question. A review wave has two per
    fault: the line is marked, and it has the right category.
    """
    problem = sheet_problem(wave, text)
    if problem:
        return [CheckResult(False, "answers the questions", problem)]
    answers, _ = read_sheet(text)
    checks = []
    if wave.mode == "review":
        for number, fault in enumerate(wave.faults, start=1):
            marked = answers.get(fault["line"])
            checks.append(check(marked is not None, f"finds fault {number}",
                                f"Fault {number} is not marked yet."))
            checks.append(check(marked == fault["category"], f"names fault {number}",
                                f"Fault {number} does not have its right name yet."))
        return checks
    for number, question in enumerate(wave.questions, start=1):
        checks.append(check(answers.get(number) == question["answer"],
                            f"answers question {number}", f"Question {number} is not right yet."))
    return checks
