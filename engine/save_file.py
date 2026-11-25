"""Save the player's progress to a JSON file, and load it again.

A save file looks like this:

    {"version": 2, "current_level": "1-1", "cleared": ["1-1"],
     "xp": 1000, "coins": 20, "combo": 3,
     "levels": {"1-1": {"wave_best": [1.0, 1.0, 1.0], ...}}}

"version" lets later versions of the game change what is saved and still
read old saves. Version 1 saves (from before scoring) had only
current_level and cleared; they still load, with no XP and the starting
coins.
"""

import json
import os
from pathlib import Path

from engine.progress import is_number, progress_from_dict
from engine.scoring import STARTING_COINS

SAVE_VERSION = 2

# The versions this game can still read.
READABLE_VERSIONS = [1, 2]

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
    levels = {}
    for level_id in state.progress:
        levels[level_id] = state.progress[level_id].to_dict()
    data = {
        "version": SAVE_VERSION,
        "current_level": state.current_level,
        "cleared": state.cleared,
        "xp": state.xp,
        "coins": state.coins,
        "combo": state.combo,
        "levels": levels,
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
    version = data.get("version")
    if version not in READABLE_VERSIONS:
        raise SaveError(f"{path}: expected version {SAVE_VERSION}, got {version!r}")

    current_level = data.get("current_level")
    if current_level is not None and not isinstance(current_level, str):
        raise SaveError(f"{path}: current_level must be a level id or null")
    cleared = data.get("cleared", [])
    if not isinstance(cleared, list):
        raise SaveError(f"{path}: cleared must be a list of level ids")
    for level_id in cleared:
        if not isinstance(level_id, str):
            raise SaveError(f"{path}: cleared must be a list of level ids")

    xp = 0
    coins = STARTING_COINS
    combo = 0
    progress = {}
    if version >= 2:
        xp = whole_number(data, "xp", path)
        coins = whole_number(data, "coins", path)
        combo = whole_number(data, "combo", path)
        progress = read_level_progress(state, data.get("levels"), path)

    if current_level is not None and state.find_level(current_level) is None:
        current_level = None
    state.current_level = current_level
    state.cleared = []
    for level_id in cleared:
        if state.find_level(level_id) is not None:
            state.cleared.append(level_id)
    state.xp = xp
    state.coins = coins
    state.combo = combo
    state.progress = progress
    return True


def whole_number(data, key, path):
    """Return data[key] if it is a whole number of 0 or more; otherwise raise SaveError."""
    value = data.get(key)
    if not is_number(value) or isinstance(value, float) or value < 0:
        raise SaveError(f"{path}: {key} must be a whole number of 0 or more")
    return value


def read_level_progress(state, levels, path):
    """Return a dict from level id to LevelProgress, read from the save's "levels".

    Levels that no longer exist in the game are dropped. Raises SaveError
    if the progress of a level is not valid.
    """
    if not isinstance(levels, dict):
        raise SaveError(f"{path}: levels must be a JSON object")
    progress = {}
    for level_id in levels:
        level = state.find_level(level_id)
        if level is None:
            continue
        try:
            progress[level_id] = progress_from_dict(levels[level_id], len(level.waves))
        except ValueError as error:
            raise SaveError(f"{path}: level {level_id}: {error}") from error
    return progress


def set_aside_broken_save(path):
    """Rename a broken save to <name>.broken and return the new path.

    The game then starts fresh, but the broken file is kept, so the player
    (or a teacher) can look at it. An older .broken file is replaced.
    """
    path = Path(path)
    broken_path = path.with_name(path.name + ".broken")
    os.replace(path, broken_path)
    return broken_path
