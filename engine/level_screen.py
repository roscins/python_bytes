"""The text the player sees when a level starts.

intro_text(level) builds the title card, the cutscene and the tips into one
piece of text; wave_screen_text shows one wave with the code typed so far. Like the commands, it returns text and never
prints, so it is easy to test.
"""

from render.highlight import highlight_lines

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


HELP_LINE = ":submit  :show  :undo  :clear  :edit n text  :ins n text  :del n  :hint  :map  :help"


def wave_screen_text(level, number, buffer_text, plain=False, color=False):
    """Return the screen of one wave: its task and the numbered code typed so far."""
    wave = level.waves[number - 1]
    label = f"WAVE {number} of {len(level.waves)} · {wave.kind.upper()}"
    if level.boss:
        label = "BOSS WAVE"
    lines = [label]
    for line in wave.brief.strip().splitlines():
        lines.append(line.strip())
    # A predict wave shows the code to read; the player types its output.
    if wave.mode == "predict" and wave.code is not None:
        lines.append("")
        lines.append("Read this code:")
        lines.extend(code_lines(wave.code, color))
        lines.append("")
        lines.append("YOUR ANSWER (what it prints):")
    else:
        lines.append("")
        lines.append("YOUR CODE:")
    if buffer_text.strip() == "":
        lines.append("    (nothing yet: type your first line)")
    else:
        lines.extend(numbered_code(buffer_text, plain, color))
    lines.append("")
    lines.append(HELP_LINE)
    return "\n".join(lines)


def intro_text(level):
    """Return everything shown when the player starts `level`, as one text."""
    lines = [title_card(level), ""]
    lines.extend(cutscene_lines(level.cutscene))
    lines.append("")
    lines.append("TIPS")
    for tip in level.tips:
        lines.append(f"  • {tip}")
    lines.append("")
    count = len(level.waves)
    waves = f"{count} waves"
    if count == 1:
        waves = "1 wave"
    lines.append(f"{waves}. Type your code one line at a time; commands start with a colon (:help).")
    return "\n".join(lines)


def boss_intro_text(level):
    """Return what is shown when a boss fight starts: the cutscene and the task."""
    lines = []
    lines.extend(cutscene_lines(level.cutscene))
    lines.append("")
    wave = level.waves[0]
    lines.append("BOSS WAVE")
    for line in wave.brief.strip().splitlines():
        lines.append(line.strip())
    minutes = level.time_limit // 60
    lines.append(f"{len(wave.tests)} hidden tests, 3 lives, {minutes} minutes. "
                 "Each failed :submit costs a life.")
    return "\n".join(lines)
