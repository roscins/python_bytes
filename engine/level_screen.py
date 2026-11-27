"""The text the player sees when a level starts.

intro_text(level) builds the title card, the cutscene and the tips into one
piece of text; wave_screen_text shows one wave with the code typed so far. Like the commands, it returns text and never
prints, so it is easy to test.
"""

from engine.fill import all_blanks_filled, blank_marker, is_filling
from engine.screens import join_screens
from grader.answer_sheet import LETTERS
from render.highlight import highlight_lines
from render.panel import panel

# Story lines in a cutscene start with this; every other line is code.
STORY_MARKER = "# >>"

# Code is indented by this much, so it stands out from the story.
CODE_INDENT = "    "


def title_card(level):
    """Return the level's title line, for example "LEVEL 1-1 · HELLO, TERMINAL"."""
    return f"LEVEL {level.id} · {level.title.upper()}"


def cutscene_lines(cutscene):
    """Return the cutscene as a list of lines to show.

    Story lines ("# >> The lab is dark.") lose their marker and are shown
    as plain text. Code lines are indented. Blank lines are left out.
    """
    lines = []
    for line in cutscene.strip().splitlines():
        if line.strip() == "":
            continue
        if line.startswith(STORY_MARKER):
            story = line[len(STORY_MARKER):].strip()
            lines.append(story)
        else:
            lines.append(CODE_INDENT + line)
    return lines


def code_lines(code, color=False):
    """Return a piece of code as indented lines, without blank lines around it.

    With `color` the code is syntax highlighted.
    """
    lines = []
    for line in highlight_lines(code.strip(), color):
        lines.append(CODE_INDENT + line)
    return lines


def separator(plain):
    """Return the character between a line number and its code."""
    if plain:
        return "|"
    return "│"


def numbered_code(text, plain=False, color=False):
    """Return a code text as numbered lines, for example "  1 │ print(1)".

    With `color` the code is syntax highlighted.
    """
    lines = []
    number = 0
    for line in highlight_lines(text, color):
        number = number + 1
        lines.append(f"{number:>3} {separator(plain)} {line}")
    return lines


# The width of the GOAL box; it also fits inside a panel of the full screen.
GOAL_WIDTH = 66

def goal_box(goal, plain=False):
    """Return the GOAL box of a wave as lines."""
    return panel("GOAL", [goal], GOAL_WIDTH, ascii_only=plain)


def question_lines(wave, color=False):
    """Return a choice wave's questions and lettered options, for the typed mode."""
    lines = []
    for number, question in enumerate(wave.questions, start=1):
        lines.append("")
        lines.append(f"{number}. {question['ask']}")
        if "code" in question:
            lines.extend(code_lines(question["code"], color))
        for letter, option in zip(LETTERS, question["options"]):
            lines.append(f"   {letter}) {option}")
    return lines


def wave_screen_text(level, number, buffer_text, plain=False, color=False):
    """Return the screen of one wave: its goal, its task and the numbered code typed so far."""
    wave = level.waves[number - 1]
    label = f"WAVE {number} of {len(level.waves)} · {wave.kind.upper()}"
    if level.boss:
        label = "BOSS WAVE"
    lines = [label]
    if wave.goal is not None:
        lines.extend(goal_box(wave.goal, plain))
    for line in wave.brief.strip().splitlines():
        lines.append(line.strip())
    # A predict wave shows the code to read; the player types its output.
    if wave.mode == "predict" and wave.code is not None:
        lines.append("")
        lines.append("Read this code:")
        lines.extend(code_lines(wave.code, color))
        lines.append("")
        lines.append("YOUR ANSWER (what it prints):")
    elif wave.mode == "review":
        lines.append("")
        lines.extend(numbered_code("\n".join(wave.code_lines()), plain, color))
        lines.append("")
        for letter, category in zip(LETTERS, wave.categories):
            lines.append(f"   {letter}) {category}")
        lines.append("")
        lines.append(f"YOUR ANSWERS (line: letter, one for each of {len(wave.faults)} faults):")
    elif wave.is_quiz():
        lines.extend(question_lines(wave, color))
        lines.append("")
        lines.append("YOUR ANSWERS (number: letter, for example 1: a):")
    else:
        lines.append("")
        lines.append("YOUR CODE:")
    if buffer_text.strip() == "":
        lines.append("    (nothing yet: type your first line)")
    else:
        lines.extend(numbered_code(buffer_text, plain, color))
    if is_filling(wave, buffer_text):
        index, marker, question = blank_marker(buffer_text, wave, len("  1 | "))
        # The marker goes right under the line with the blank.
        position = len(lines) - len(buffer_text.splitlines()) + index + 1
        lines.insert(position, marker)
        lines.append(question)
    elif all_blanks_filled(wave, buffer_text):
        lines.append("All blanks are filled: :submit to check it.")
    return "\n".join(lines)


def intro_text(level, keys=False):
    """Return everything shown when the player starts `level`; `keys` for the key-driven mode."""
    story = [title_card(level), ""]
    story.extend(cutscene_lines(level.cutscene))
    tips = ["TIPS"]
    for tip in level.tips:
        tips.append(f"  • {tip}")
    tips.append("")
    count = len(level.waves)
    waves = f"{count} waves"
    if count == 1:
        waves = "1 wave"
    how = "Type your code one line at a time; commands start with a colon (:help)."
    if keys:
        how = "You type straight into the code; Ctrl-S hands it in."
    tips.append(f"{waves}. {how}")
    return join_screens(["\n".join(story), "\n".join(tips)])


def boss_intro_text(level, keys=False):
    """Return what is shown when a boss fight starts: the cutscene and the task."""
    lines = []
    lines.extend(cutscene_lines(level.cutscene))
    lines.append("")
    wave = level.waves[0]
    lines.append("BOSS WAVE")
    for line in wave.brief.strip().splitlines():
        lines.append(line.strip())
    minutes = level.time_limit // 60
    submit = ":submit"
    if keys:
        submit = "Submit (Run is free)"
    lines.append(f"{len(wave.tests)} hidden tests, 3 tries, {minutes} minutes. "
                 f"Each failed {submit} uses up a try.")
    return "\n".join(lines)
