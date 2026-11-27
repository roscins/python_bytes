"""The answer sheet of a quiz wave: reading it, writing it and grading it.

A sheet is text with one answer per line, "number: letter", for example
"2: b". The key screens write the sheet; in plain mode the player types it.
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


def sheet_problem(wave, text):
    """Return why `text` cannot be graded for `wave`, or "" if it can."""
    answers, problem = read_sheet(text)
    if problem:
        return problem
    if not answers:
        return "You have not answered yet. Answer first, then submit."
    for number, letter in answers.items():
        if not 1 <= number <= len(wave.questions):
            return f"There is no question {number}."
        letters = LETTERS[:len(wave.questions[number - 1]["options"])]
        if letter not in letters:
            return f"Question {number} has the letters {', '.join(letters)}."
    return ""


def key_sheet(questions):
    """Return the right sheet for a list of questions."""
    answers = {}
    for number, question in enumerate(questions, start=1):
        answers[number] = question["answer"]
    return write_sheet(answers)


def grade_sheet(wave, text):
    """Return one CheckResult per question of `wave` for the sheet `text`."""
    problem = sheet_problem(wave, text)
    if problem:
        return [CheckResult(False, "answers the questions", problem)]
    answers, _ = read_sheet(text)
    checks = []
    for number, question in enumerate(wave.questions, start=1):
        name = f"answers question {number}"
        if answers.get(number) == question["answer"]:
            checks.append(CheckResult(True, name))
        else:
            checks.append(CheckResult(False, name, f"Question {number} is not right yet."))
    return checks
