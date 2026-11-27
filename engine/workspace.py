"""Files for a wave's code: names, the starting text, and the export of :where.

The player types their code in the game, and it lives in the game's save
(see engine/code_mode.py). The :where command writes the code of the wave
you are on to a file, for the few players who want to open it in an editor:

    workspace/1-1/wave1.py    a code wave (a fill-in or build wave)
    workspace/1-1/wave3.txt   the answer of a predict wave

The file is only a copy: the game never reads it back. The workspace/ folder
is in .gitignore, so a player's answers are never committed.
"""

from pathlib import Path

# The workspace lives in the game's folder, next to levels/ and engine/.
WORKSPACE_FOLDER = Path(__file__).parent.parent / "workspace"


def wave_file_name(wave, number):
    """Return the file name for wave number `number`, for example "wave1.py".

    A predict wave's answer is text, not code, so its file ends in .txt.
    """
    if wave.mode == "predict":
        return f"wave{number}.txt"
    return f"wave{number}.py"


def level_folder(level, root):
    """Return the workspace folder of `level` inside `root`."""
    return Path(root) / level.id


def starting_text(wave):
    """Return what the code of a new wave starts with.

    Fill-in waves and fix-the-bug waves start from their starter code; the
    others start empty. A build wave does not start with the brief as a
    comment, because then "add a comment" would pass for free.
    """
    if wave.starter is not None:
        return wave.starter.strip() + "\n"
    return ""


def export_wave(level, number, text, root):
    """Write `text` as the file of wave `number` of `level` in `root`; return the file's path."""
    folder = level_folder(level, root)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / wave_file_name(level.waves[number - 1], number)
    path.write_text(text, encoding="utf-8")
    return path
