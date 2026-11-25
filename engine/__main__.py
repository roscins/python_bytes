"""Start the game with: python -m engine"""

import sys
from pathlib import Path

from engine.game_state import GameState
from engine.level_pack import LevelError, load_levels
from engine.loop import run
from engine.save_file import DEFAULT_SAVE_PATH, SaveError, load_progress, set_aside_broken_save
from engine.workspace import WORKSPACE_FOLDER
from grader.progression import CONCEPTS_FILE, load_curriculum

# The levels folder, found from this file's folder so it works from anywhere.
LEVELS_FOLDER = Path(__file__).parent.parent / "levels"


def load_game_curriculum(concepts_file, levels):
    """Read levels/concepts.toml and check that every level pack is listed in it.

    Returns the Curriculum, or None if `concepts_file` is None (the map is
    then made of the level packs alone). Raises ValueError, with a message
    for the player, if the file cannot be read or a pack is not in it.
    """
    if concepts_file is None:
        return None
    try:
        curriculum = load_curriculum(concepts_file)
    except (OSError, ValueError, KeyError) as error:
        raise ValueError(f"cannot read {concepts_file}: {error}") from error
    for level in levels:
        if curriculum.find(level.id) is None:
            raise ValueError(f"level {level.id} is not listed in {concepts_file}")
    return curriculum


def main(levels_folder=LEVELS_FOLDER, save_path=DEFAULT_SAVE_PATH,
         workspace_root=WORKSPACE_FOLDER, concepts_file=CONCEPTS_FILE):
    """Load the levels and the save, run the command loop, return an exit code.

    The player's code goes in workspace_root, one folder per level.
    levels/concepts.toml (`concepts_file`) lists every level of the game, so
    the map can show levels that are not written yet. Pass None to show
    only the level packs.

    A broken level stops the game, because it is a mistake in the game
    itself. A broken save does not: it is set aside and the game starts
    fresh. A save that cannot be opened at all stops the game.
    """
    try:
        levels = load_levels(levels_folder)
    except (OSError, LevelError) as error:
        print(f"Cannot load the levels: {error}")
        return 1
    try:
        curriculum = load_game_curriculum(concepts_file, levels)
    except ValueError as error:
        print(f"Cannot load the levels: {error}")
        return 1
    state = GameState(levels, workspace_root, curriculum)
    try:
        load_progress(state, save_path)
    except SaveError as error:
        print(f"Your save file is broken: {error}")
        broken_path = set_aside_broken_save(save_path)
        print(f"It was moved to {broken_path}. Starting a new game.")
    except OSError as error:
        # The file is there but cannot be opened, for example because of
        # its permissions. Moving it would fail too, so the game stops.
        print(f"Cannot open your save file: {error}")
        return 1
    run(state, save_path=save_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
