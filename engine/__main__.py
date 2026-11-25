"""Start the game with: python -m engine"""

import sys
from pathlib import Path

from engine.game_state import GameState
from engine.level_pack import LevelError, load_levels
from engine.loop import run
from engine.save_file import DEFAULT_SAVE_PATH, SaveError, load_progress, set_aside_broken_save
from engine.workspace import WORKSPACE_FOLDER

# The levels folder, found from this file's folder so it works from anywhere.
LEVELS_FOLDER = Path(__file__).parent.parent / "levels"


def main(levels_folder=LEVELS_FOLDER, save_path=DEFAULT_SAVE_PATH,
         workspace_root=WORKSPACE_FOLDER):
    """Load the levels and the save, run the command loop, return an exit code.

    The player's code goes in workspace_root, one folder per level.

    A broken level stops the game, because it is a mistake in the game
    itself. A broken save does not: it is set aside and the game starts
    fresh. A save that cannot be opened at all stops the game.
    """
    try:
        levels = load_levels(levels_folder)
    except (OSError, LevelError) as error:
        print(f"Cannot load the levels: {error}")
        return 1
    state = GameState(levels, workspace_root)
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
