"""Save the player's progress to a JSON file, and load it again.

A save file looks like this:

    {"version": 1, "current_level": "1-1", "cleared": []}

"version" lets later versions of the game change what is saved and still
read old saves.
"""

import json
import os
from pathlib import Path

SAVE_VERSION = 1

# The save lives in the player's home folder, not in the game's folder, so
# it survives updating the game and is never committed to Git by mistake.
DEFAULT_SAVE_PATH = Path.home() / ".python-bytes" / "save.json"


class SaveError(ValueError):
    """A save file that cannot be used, for example because it is not JSON."""


def save_progress(state, path):
    """Write the player's progress in `state` to the save file at `path`.

    The folder is made if it does not exist yet. The save is first written
    to a temporary file, which then replaces the old save in one step. So if
    the game crashes halfway through saving, the old save is still whole.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": SAVE_VERSION,
        "current_level": state.current_level,
        "cleared": state.cleared,
    }
    temporary_path = path.with_name(path.name + ".tmp")
    with open(temporary_path, "w", encoding="utf-8") as save_file:
        json.dump(data, save_file, indent=2)
    os.replace(temporary_path, path)


def load_progress(state, path):
    """Read the save file at `path` into `state`.

    Returns False if there is no save file yet (a new player), and True if
    progress was loaded. A level id that no longer exists in the game is
    dropped, so a removed level cannot break the save.

    Raises SaveError if the file is not a valid save.
    """
    path = Path(path)
    if not path.exists():
        return False
    try:
        with open(path, encoding="utf-8") as save_file:
            data = json.load(save_file)
    except json.JSONDecodeError as error:
        raise SaveError(f"{path}: not valid JSON: {error}") from error

    if not isinstance(data, dict):
        raise SaveError(f"{path}: a save must be a JSON object, like {{\"version\": 1}}")
    if data.get("version") != SAVE_VERSION:
        raise SaveError(f"{path}: expected version {SAVE_VERSION}, got {data.get('version')!r}")

    current_level = data.get("current_level")
    if current_level is not None and not isinstance(current_level, str):
        raise SaveError(f"{path}: current_level must be a level id or null")
    cleared = data.get("cleared", [])
    if not isinstance(cleared, list):
        raise SaveError(f"{path}: cleared must be a list of level ids")
    for level_id in cleared:
        if not isinstance(level_id, str):
            raise SaveError(f"{path}: cleared must be a list of level ids")

    if current_level is not None and state.find_level(current_level) is None:
        current_level = None
    state.current_level = current_level
    state.cleared = []
    for level_id in cleared:
        if state.find_level(level_id) is not None:
            state.cleared.append(level_id)
    return True


def set_aside_broken_save(path):
    """Rename a broken save to <name>.broken and return the new path.

    The game then starts fresh, but the broken file is kept, so the player
    (or a teacher) can look at it. An older .broken file is replaced.
    """
    path = Path(path)
    broken_path = path.with_name(path.name + ".broken")
    os.replace(path, broken_path)
    return broken_path
