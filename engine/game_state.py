"""The state of one running game: which levels exist and where the player is."""


class GameState:
    """Everything the command loop needs to remember between commands.

    Attributes:
        levels: the Level objects the player can choose from, in map order.
        current_level: the id of the level being played, for example "1-1",
            or None if the player has not started a level yet.
        cleared: the ids of the levels the player has cleared. Grading
            arrives in Phase 2, so for now this stays empty.
        running: True while the game should keep asking for commands.
    """

    def __init__(self, levels=None):
        """Start a new game with the given levels (or none)."""
        if levels is None:
            levels = []
        self.levels = list(levels)
        self.current_level = None
        self.cleared = []
        self.running = True

    def find_level(self, level_id):
        """Return the level with this id, or None if there is no such level."""
        for level in self.levels:
            if level.id == level_id:
                return level
        return None
