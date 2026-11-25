"""The text the player sees when a level starts.

intro_text(level) builds the title card, the cutscene, the tips and the
waves into one piece of text. Like the commands, it returns text and never
prints, so it is easy to test.
"""

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


def code_lines(code):
    """Return a piece of code as indented lines, without blank lines around it."""
    lines = []
    for line in code.strip().splitlines():
        lines.append(CODE_INDENT + line)
    return lines


def wave_lines(wave, number):
    """Return the lines that introduce one wave: its number, kind, brief and code."""
    lines = [f"WAVE {number} · {wave.kind.upper()}"]
    for line in wave.brief.strip().splitlines():
        lines.append(line.strip())
    # A fill-in wave shows the code with blanks; a predict wave shows the
    # code to read. A build wave has no code: the player writes it all.
    if wave.starter is not None:
        lines.extend(code_lines(wave.starter))
    elif wave.code is not None:
        lines.extend(code_lines(wave.code))
    return lines


def intro_text(level):
    """Return everything shown when the player starts `level`, as one text."""
    lines = [title_card(level), ""]
    lines.extend(cutscene_lines(level.cutscene))
    lines.append("")
    lines.append("TIPS")
    for tip in level.tips:
        lines.append(f"  • {tip}")
    number = 0
    for wave in level.waves:
        number = number + 1
        lines.append("")
        lines.extend(wave_lines(wave, number))
    lines.append("")
    lines.append("Grading arrives in a later version. Type map to see the levels.")
    return "\n".join(lines)
