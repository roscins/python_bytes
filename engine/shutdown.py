"""Stopping the game cleanly when the system asks it to (Ctrl-C, kill, closed window).

The rule that keeps the save safe: **a signal never saves anything itself.**
A signal can arrive in the middle of a command, when the game state is only
half updated. So:

- If the game is waiting for the player to type, nothing is half done. The
  handler raises GameInterrupted, which ends the waiting input() call. (A
  handler that simply returns would not: Python goes back to waiting.)
- If a command is running, the handler only sets `requested`. The command
  loop looks at it after the command, when the state is whole, saves, and
  stops.
- A second signal always stops at once, so the player can never get stuck.

Killing the process with kill -9 cannot be caught at all. That is why the
game also saves after every typed line (see engine/loop.py).
"""

import os
import signal
from contextlib import contextmanager


class GameInterrupted(SystemExit):
    """Raised to leave the game after a signal. Its code is the exit code (128 + signal)."""


class ShutdownGuard:
    """Catches the stop signals and tells the game when to stop.

    Attributes:
        requested: True after the first stop signal.
        exit_code: 128 + the number of that signal, or 0.
        is_waiting: True while the game waits for the player to type.
    """

    def __init__(self):
        """Start with no stop requested and the old handlers not yet saved."""
        self.requested = False
        self.exit_code = 0
        self.is_waiting = False
        self.old_handlers = {}

    def stop_signals(self):
        """Return the signals that mean "stop", for this operating system."""
        names = ["SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGBREAK"]
        signals = []
        for name in names:
            if hasattr(signal, name):
                signals.append(getattr(signal, name))
        return signals

    def install(self):
        """Start catching the stop signals. Does nothing outside the main thread."""
        for number in self.stop_signals():
            try:
                self.old_handlers[number] = signal.signal(number, self.handle)
            except ValueError:
                # signal.signal only works in the main thread.
                return

    def restore(self):
        """Put the handlers back that were there before install()."""
        for number in self.old_handlers:
            signal.signal(number, self.old_handlers[number])
        self.old_handlers = {}

    def handle(self, number, frame):
        """Run when a stop signal arrives (see the module text for the rules)."""
        second_signal = self.requested
        self.requested = True
        self.exit_code = 128 + number
        if self.is_waiting or second_signal:
            raise GameInterrupted(128 + number)

    @contextmanager
    def waiting(self):
        """Mark the code inside `with` as waiting for the player."""
        self.is_waiting = True
        try:
            yield
        finally:
            self.is_waiting = False

    def stop_if_requested(self):
        """Leave now if a stop signal arrived earlier, before waiting for a key."""
        if self.requested:
            raise GameInterrupted(self.exit_code)

    def read_input(self, read_line, prompt):
        """Call read_line(prompt) while marked as waiting, and return what it returns."""
        with self.waiting():
            return read_line(prompt)


# What Windows tells a program when its console window is closed, or the
# user logs off or shuts down. (There is no SIGHUP on Windows.)
CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6
CLOSING_EVENTS = (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT)


def make_console_handler(save_now):
    """Return the function Windows calls when the console is closing.

    It saves and says "handled". Windows ends the program a moment after
    this function returns. It runs in another thread, which is why the
    AutoSaver has a lock. Other events (like Ctrl-C) are left to the normal
    signal handling: the function answers False.
    """
    def handler(event):
        """Save if the console is closing; return True if the event was handled."""
        if event in CLOSING_EVENTS:
            save_now()
            return True
        return False

    return handler


def install_windows_close_handler(save_now):
    """Ask Windows to call `save_now` when the console window is closed.

    Returns an object the caller must keep alive for as long as the game
    runs (Python would otherwise throw the handler away), or None when this
    is not Windows or the handler could not be installed. Not being able to
    install it is not an error: the game also saves after every line.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        handler_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        c_handler = handler_type(make_console_handler(save_now))
        if not ctypes.windll.kernel32.SetConsoleCtrlHandler(c_handler, True):
            return None
        return c_handler
    except (ImportError, AttributeError, OSError):
        return None
