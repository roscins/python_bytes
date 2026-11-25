"""Save the player's progress to a JSON file, and load it again.

A save file looks like this:

    {"version": 3, "current_level": "1-1", "current_wave": 2, "coding": true,
     "cleared": ["1-1"], "xp": 1000, "coins": 20, "combo": 3,
     "levels": {"1-1": {"wave_best": [1.0, 1.0, 1.0], ...}},
     "buffers": {"1-1": {"2": "print(\"SYSTEM CHECK\")"}}}

"version" lets later versions of the game change what is saved and still
read old saves. Version 1 saves (from before scoring) had only
current_level and cleared; they still load, with no XP and the starting
coins. Version 2 saves have no "coding", "current_wave" or "buffers"; they
load with the player at the map and no unfinished code.

"buffers" holds the code the player has typed for each wave, so a game that
is killed at any moment comes back with the unfinished answer.
"""

import json
import os
import time
from pathlib import Path

from engine.progress import is_number, progress_from_dict
from engine.scoring import STARTING_COINS

SAVE_VERSION = 3

# The versions this game can still read.
READABLE_VERSIONS = [1, 2, 3]

# On Windows another program (a virus scanner, the indexer) can hold the save
# file for a moment. Replacing it is tried this many times, this long apart.
REPLACE_TRIES = 5
REPLACE_WAIT_SECONDS = 0.02

# The save lives in the player's home folder, not in the game's folder, so
# it survives updating the game and is never committed to Git by mistake.
DEFAULT_SAVE_PATH = Path.home() / ".python-bytes" / "save.json"


class SaveError(ValueError):
    """A save file that cannot be used, for example because it is not JSON."""


def replace_with_retry(source, target, replace, sleep):
    """Replace `target` by `source`, trying again if the target is locked for a moment."""
    for attempt in range(REPLACE_TRIES):
        try:
            replace(source, target)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES - 1:
                raise
            sleep(REPLACE_WAIT_SECONDS)


def sync_folder(folder):
    """Ask the system to write the folder's entries to disk (not possible on Windows)."""
    if os.name == "nt":
        return
    try:
        descriptor = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        pass


def write_atomically(path, text, replace=os.replace, fsync=os.fsync, sleep=time.sleep):
    """Write `text` to `path` so that a crash at any moment leaves a whole file.

    The text goes to a temporary file in the same folder and is forced to
    disk (fsync). Only then does the temporary file replace the real one, in
    one step. So `path` always holds either the old text or the new text,
    never half of it. The temporary name has the process id, so two running
    games do not share one. `replace`, `fsync` and `sleep` are parameters so
    that tests can break the write halfway.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(temporary_path, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(text)
            temporary_file.flush()
            fsync(temporary_file.fileno())
        replace_with_retry(temporary_path, path, replace, sleep)
    except BaseException:
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    sync_folder(path.parent)


def buffers_to_dict(buffers):
    """Return the code buffers in the form the save file stores: wave numbers as text keys."""
    data = {}
    for level_id in buffers:
        data[level_id] = {}
        for number in buffers[level_id]:
            data[level_id][str(number)] = buffers[level_id][number]
    return data


def save_progress(state, path):
    """Write the player's progress in `state` to the save file at `path`.

    The folder is made if it does not exist yet. The write is atomic (see
    write_atomically), so the save is whole even if the game is killed in
    the middle of saving.
    """
    levels = {}
    for level_id in state.progress:
        levels[level_id] = state.progress[level_id].to_dict()
    data = {
        "version": SAVE_VERSION,
        "current_level": state.current_level,
        "current_wave": state.current_wave,
        "coding": state.coding,
        "cleared": state.cleared,
        "xp": state.xp,
        "coins": state.coins,
        "combo": state.combo,
        "levels": levels,
        "buffers": buffers_to_dict(state.buffers),
    }
    write_atomically(path, json.dumps(data, indent=2))


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

    current_wave = 1
    coding = False
    buffers = {}
    if version >= 3:
        current_wave = data.get("current_wave", 1)
        if isinstance(current_wave, bool) or not isinstance(current_wave, int):
            raise SaveError(f"{path}: current_wave must be a whole number")
        coding = data.get("coding", False)
        if not isinstance(coding, bool):
            raise SaveError(f"{path}: coding must be true or false")
        buffers = read_buffers(state, data.get("buffers", {}), path)

    if current_level is not None and state.find_level(current_level) is None:
        current_level = None
    if current_level is None:
        coding = False
    else:
        wave_count = len(state.find_level(current_level).waves)
        if current_wave < 1 or current_wave > wave_count:
            current_wave = 1
    state.current_level = current_level
    state.current_wave = current_wave
    state.coding = coding
    state.buffers = buffers
    state.cleared = []
    for level_id in cleared:
        if state.find_level(level_id) is not None:
            state.cleared.append(level_id)
    state.xp = xp
    state.coins = coins
    state.combo = combo
    state.progress = progress
    return True


def read_buffers(state, buffers, path):
    """Return the code buffers of a save: {level id: {wave number: text}}.

    Buffers of levels that no longer exist, or of waves a level no longer
    has, are dropped. Raises SaveError if a buffer is not text.
    """
    if not isinstance(buffers, dict):
        raise SaveError(f"{path}: buffers must be a JSON object")
    result = {}
    for level_id in buffers:
        level = state.find_level(level_id)
        if level is None:
            continue
        waves = buffers[level_id]
        if not isinstance(waves, dict):
            raise SaveError(f"{path}: buffers of level {level_id} must be a JSON object")
        result[level_id] = {}
        for key in waves:
            text = waves[key]
            if not key.isdigit() or not isinstance(text, str):
                raise SaveError(f"{path}: level {level_id}: a wave's code must be text")
            number = int(key)
            if 1 <= number <= len(level.waves):
                result[level_id][number] = text
    return result


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
