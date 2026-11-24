"""The state of one running game: which levels exist and where the player is."""

# Until the level-pack loader exists, the game knows only the World 1 levels
# by their ids. Later this list will come from the level folders.
DEFAULT_LEVELS = ["1-1", "1-2", "1-3", "1-4"]


class GameState:
    """Everything the command loop needs to remember between commands.

    Attributes:
        levels: the level ids the player can choose from, in map order.
        current_level: the id of the level being played, or None if the
            player has not started a level yet.
        running: True while the game should keep asking for commands.
    """

    def __init__(self, levels=None):
        """Start a new game with the given level ids (or the default list)."""
        if levels is None:
            levels = DEFAULT_LEVELS
        self.levels = list(levels)
        self.current_level = None
        self.running = True
