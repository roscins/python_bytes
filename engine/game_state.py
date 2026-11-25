"""The state of one running game: which levels exist and where the player is."""

from engine.progress import LevelProgress
from engine.scoring import STARTING_COINS


class GameState:
    """Everything the command loop needs to remember between commands.

    Attributes:
        levels: the Level objects the player can choose from, in map order.
        current_level: the id of the level being played, for example "1-1",
            or None if the player has not started a level yet.
        cleared: the ids of the levels the player has cleared (70 % or more).
        xp: the player's experience points.
        coins: the coins the player can spend on hints.
        combo: how many waves in a row were passed on the first try.
        progress: a dict from level id to that level's LevelProgress.
        boss_fight: the BossFight going on, or None. It is not saved, so
            quitting in the middle of a fight starts it again next time.
        running: True while the game should keep asking for commands.
        workspace_root: the folder that holds the players' code, one
            folder per level (see engine/workspace.py), or None for no
            workspace. Tests leave it as None, so they never write files.
    """

    def __init__(self, levels=None, workspace_root=None):
        """Start a new game with the given levels (or none) and workspace folder."""
        if levels is None:
            levels = []
        self.levels = list(levels)
        self.workspace_root = workspace_root
        self.current_level = None
        self.cleared = []
        self.xp = 0
        self.coins = STARTING_COINS
        self.combo = 0
        self.progress = {}
        self.boss_fight = None
        self.running = True

    def progress_for(self, level):
        """Return the LevelProgress of `level`, making a new one the first time."""
        if level.id not in self.progress:
            self.progress[level.id] = LevelProgress(len(level.waves))
        return self.progress[level.id]

    def find_level(self, level_id):
        """Return the level with this id, or None if there is no such level."""
        for level in self.levels:
            if level.id == level_id:
                return level
        return None

    def current_world(self):
        """Return the world of the current level, or of the first level.

        Before any level is started, the player is in the first world.
        Returns None if there are no levels at all.
        """
        level = self.find_level(self.current_level)
        if level is not None:
            return level.world
        if self.levels:
            return self.levels[0].world
        return None

    def levels_in_world(self, world):
        """Return the levels of one world, in map order."""
        levels = []
        for level in self.levels:
            if level.world == world:
                levels.append(level)
        return levels
