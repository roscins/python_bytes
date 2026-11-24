"""Start the game with: python -m engine"""

from engine.game_state import GameState
from engine.loop import run


def main():
    """Create a new game and run the command loop."""
    state = GameState()
    run(state)


if __name__ == "__main__":
    main()
