"""The workspace: the folder where the player writes the code for each level.

The player writes code in their own editor. Each level gets its own folder,
workspace/<level-id>/, with one file per wave:

    workspace/1-1/wave1.py    the fill-in wave, starting from the starter code
    workspace/1-1/wave2.py    the build wave, starting empty
    workspace/1-1/wave3.txt   the predicted output of a predict wave

submit reads these files and grades them. The workspace/ folder is in
.gitignore, so a player's answers are never committed.
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
    """Return what a new wave file starts with.

    Fill-in waves and fix-the-bug waves start from their starter code; the
    others start empty. A build file does not start with the brief as a
    comment, because then "add a comment" would pass for free.
    """
    if wave.starter is not None:
        return wave.starter.strip() + "\n"
    return ""


def prepare_workspace(level, root):
    """Make the level's workspace folder and its wave files; return the folder.

    A file that already exists is never overwritten, so playing a level
    again never loses the player's work.
    """
    folder = level_folder(level, root)
    folder.mkdir(parents=True, exist_ok=True)
    number = 0
    for wave in level.waves:
        number = number + 1
        path = folder / wave_file_name(wave, number)
        if not path.exists():
            path.write_text(starting_text(wave), encoding="utf-8")
    return folder


def read_wave_file(level, number, root):
    """Return the text of wave number `number`'s file, or None if it does not exist."""
    wave = level.waves[number - 1]
    path = level_folder(level, root) / wave_file_name(wave, number)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
