"""The title screen: CONTINUE, NEW GAME or QUIT.

This is the first thing the player sees. It says nothing about commands:
it asks one question and the game starts. Like the other screens, the
functions here return text; ask_title is the only one that talks to the
player, through the read_line and write functions it is given.
"""

import os
from pathlib import Path

from engine.game_state import GameState
from engine.save_file import SaveError, load_progress

CONTINUE = "continue"
NEW = "new"
QUIT = "quit"

TITLE = "PYTHON BYTES"


class SaveInfo:
    """What the title screen knows about the save file.

    Attributes:
        status: "none" (no save), "ok" (a save that loads) or "damaged".
        level_id: the level the player was on, or None for the map.
        wave: the wave the player was on.
        message: for a damaged save, why it cannot be used.
    """

    def __init__(self, status, level_id=None, wave=1, message=""):
        """Remember the facts about the save."""
        self.status = status
        self.level_id = level_id
        self.wave = wave
        self.message = message


def inspect_save(path, levels, curriculum):
    """Look at the save file at `path` without changing anything; return a SaveInfo."""
    path = Path(path)
    if not path.exists():
        return SaveInfo("none")
    scratch = GameState(levels, curriculum=curriculum)
    try:
        load_progress(scratch, path)
    except (SaveError, OSError) as error:
        return SaveInfo("damaged", message=str(error))
    return SaveInfo("ok", scratch.current_level, scratch.current_wave)


def options_for(info):
    """Return the menu as a list of (choice, label), first option first."""
    options = []
    if info.status == "ok":
        if info.level_id is None:
            where = "at the map"
        else:
            where = f"level {info.level_id}, wave {info.wave}"
        options.append((CONTINUE, f"CONTINUE ({where})"))
    options.append((NEW, "NEW GAME"))
    options.append((QUIT, "QUIT"))
    return options


def title_text(info, plain=False):
    """Return the title screen as text."""
    lines = [TITLE, "=" * len(TITLE), ""]
    if info.status == "damaged":
        lines.append("Your save file is damaged. NEW GAME keeps it as a .broken file.")
        lines.append("")
    number = 0
    for _, label in options_for(info):
        number = number + 1
        lines.append(f"  {number}  {label}")
    return "\n".join(lines)


def choice_from(text, options):
    """Return the choice the typed `text` stands for, or None if it is not a choice."""
    text = text.strip().lower()
    if text == "":
        return options[0][0]
    if text.isdigit():
        number = int(text)
        if 1 <= number <= len(options):
            return options[number - 1][0]
        return None
    for choice, label in options:
        if label.lower().startswith(text[0]) and len(text) == 1:
            return choice
    return None


def ask_title(info, read_line, write, plain=False):
    """Show the title screen and return CONTINUE, NEW or QUIT.

    Enter alone picks the first option. Starting a new game over a good save
    asks for a yes first; the old save is kept (see keep_old_save).
    End of input (Ctrl-D) quits.
    """
    options = options_for(info)
    write(title_text(info, plain))
    while True:
        try:
            typed = read_line("> ")
        except EOFError:
            return QUIT
        choice = choice_from(typed, options)
        if choice is None:
            write("Type a number from the list, or c, n or q.")
            continue
        if choice == NEW and info.status == "ok":
            write("This starts again from the beginning. Your old game is kept as save.json.old.")
            try:
                answer = read_line("Type yes to start a new game: ")
            except EOFError:
                return QUIT
            if answer.strip().lower() != "yes":
                write(title_text(info, plain))
                continue
        return choice


def keep_old_save(path):
    """Move the save to <name>.old (replacing an older .old), so a new game never deletes a save."""
    path = Path(path)
    os.replace(path, path.with_name(path.name + ".old"))
