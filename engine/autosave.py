"""AutoSaver: save the game whenever something changes, and never crash doing it.

The game saves after every typed line (see engine/loop.py), so a killed
process loses at most the line being typed. A save that fails (a full disk,
a folder that cannot be written) is reported by the caller and the game goes
on.
"""

import threading

from engine.save_file import save_progress


class AutoSaver:
    """Saves a GameState to a file.

    Attributes:
        state: the GameState to save.
        path: the save file.
        save_count: how many saves worked so far (tests use it).
        last_error: the OSError of the last failed save, or None.
    """

    def __init__(self, state, path):
        """Remember what to save and where."""
        self.state = state
        self.path = path
        self.save_count = 0
        self.last_error = None
        # On Windows the "console closed" handler runs in another thread. The
        # lock keeps it from saving at the same moment as the game does.
        self.lock = threading.RLock()

    def save(self):
        """Save now. Return True if it worked, False if it failed (see last_error)."""
        with self.lock:
            try:
                save_progress(self.state, self.path)
            except OSError as error:
                self.last_error = error
                return False
            self.save_count = self.save_count + 1
            self.last_error = None
            return True
