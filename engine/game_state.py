"""The state of one running game: which levels exist and where the player is."""

from engine.progress import LevelProgress
from engine.roadmap import build_slots
from engine.scoring import STARTING_COINS
from engine.workspace import starting_text

# How many earlier versions of a wave's code :undo can go back to.
UNDO_LIMIT = 20


class GameState:
    """Everything the command loop needs to remember between commands.

    Attributes:
        levels: the Level objects the player can choose from, in map order.
        curriculum: the Curriculum (levels/concepts.toml) that says which
            levels exist on the map, or None to show only the levels above.
        current_level: the id of the level being played, for example "1-1",
            or None if the player has not started a level yet.
        current_wave: the wave the player is on in the current level (from 1).
        coding: True while the player is typing the code of a wave. Then
            every line that does not start with ":" is code.
        buffers: the code typed so far, {level id: {wave number: text}}.
            It is saved with the progress, so unfinished code is never lost.
        undo_stack: earlier versions of a wave's code, newest last, as
            (level id, wave number, text). Not saved.
        pending: what the game is waiting for after an answer that needs more
            typing (a dict with a "kind"), or None. Not saved.
        just_filled: the wave and code right after its last blank was filled
            (see engine/code_mode.py), or None. Not saved.
        repl: the quick console (runner/repl.py), started when first needed.
        repl_timeout: seconds one line of the quick console may run.
        plain: True for the ASCII look (no box characters).
        color: True to colour code with ANSI colours (off for tests, pipes and NO_COLOR).
        cleared: the ids of the levels the player has cleared (every wave passed).
        xp: the player's experience points.
        coins: the coins the player can spend on hints.
        combo: how many waves in a row were passed on the first try.
        progress: a dict from level id to that level's LevelProgress.
        boss_fight: the BossFight going on, or None. It is not saved, so
            quitting in the middle of a fight starts it again next time.
        running: True while the game should keep asking for commands.
        workspace_root: the folder where :where saves a copy of the code of a
            wave (see engine/workspace.py), or None for no folder. Tests leave
            it as None, so they never write files.
    """

    def __init__(self, levels=None, workspace_root=None, curriculum=None):
        """Start a new game with the given levels (or none), workspace folder and curriculum."""
        if levels is None:
            levels = []
        self.levels = list(levels)
        self.curriculum = curriculum
        self.workspace_root = workspace_root
        self.current_level = None
        self.current_wave = 1
        self.coding = False
        self.buffers = {}
        self.undo_stack = []
        self.pending = None
        # (level id, wave number, code) right after the last blank was filled.
        self.just_filled = None
        self.repl = None
        self.repl_timeout = 2.0
        self.plain = False
        self.color = False
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

    def slots(self):
        """Return what the map shows, in map order: the levels, plus the ones not written yet.

        See engine/roadmap.py. Without a curriculum these are the levels.
        """
        return build_slots(self.levels, self.curriculum)

    def find_slot(self, level_id):
        """Return the slot with this id (a Level or a MissingLevel), or None."""
        for slot in self.slots():
            if slot.id == level_id:
                return slot
        return None

    def slots_in_world(self, world):
        """Return the slots of one world, in map order."""
        slots = []
        for slot in self.slots():
            if slot.world == world:
                slots.append(slot)
        return slots

    def current_world(self):
        """Return the world of the current level, or of the first slot on the map.

        Before any level is started, the player is in the first world.
        Returns None if there is nothing on the map at all.
        """
        level = self.find_level(self.current_level)
        if level is not None:
            return level.world
        slots = self.slots()
        if slots:
            return slots[0].world
        return None

    def levels_in_world(self, world):
        """Return the levels of one world, in map order."""
        levels = []
        for level in self.levels:
            if level.world == world:
                levels.append(level)
        return levels

    def wave_text(self, level, number):
        """Return the code typed so far for wave `number` of `level`.

        The first time, the buffer is made from the wave's starter code
        (fill-in and fix-the-bug waves) or is empty. A buffer that exists is
        never replaced, so going back to a wave never loses the player's work.
        """
        waves = self.buffers.setdefault(level.id, {})
        if number not in waves:
            waves[number] = starting_text(level.waves[number - 1])
        return waves[number]

    def set_wave_text(self, level, number, text):
        """Replace the code of wave `number` of `level`, remembering the old code for :undo."""
        old_text = self.wave_text(level, number)
        self.undo_stack.append((level.id, number, old_text))
        del self.undo_stack[:-UNDO_LIMIT]
        self.buffers[level.id][number] = text

    def undo_wave_text(self, level, number):
        """Go back to the code before the last change; return False if there is nothing to undo."""
        for index in range(len(self.undo_stack) - 1, -1, -1):
            level_id, wave_number, text = self.undo_stack[index]
            if level_id == level.id and wave_number == number:
                del self.undo_stack[index]
                self.buffers[level.id][number] = text
                return True
        return False

    def close(self):
        """End what the game started: the quick console's worker process."""
        if self.repl is not None:
            self.repl.close()
            self.repl = None
