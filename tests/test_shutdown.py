"""Tests for engine/shutdown.py: what happens when the game is told to stop.

The rule: a signal never saves anything itself (the game state could be
half updated). While the game waits for the player, a signal stops it at
once; while a command runs, the loop stops after the command.
"""

import os
import signal
import unittest

from engine.shutdown import (
    CTRL_CLOSE_EVENT,
    CTRL_LOGOFF_EVENT,
    CTRL_SHUTDOWN_EVENT,
    GameInterrupted,
    ShutdownGuard,
    install_windows_close_handler,
    make_console_handler,
)


class TestGuardLogic(unittest.TestCase):
    """The decisions, without real signals."""

    def test_signal_while_waiting_stops_at_once(self):
        """The handler raises GameInterrupted, which is what ends a blocked input()."""
        guard = ShutdownGuard()
        with guard.waiting():
            with self.assertRaises(GameInterrupted) as context:
                guard.handle(signal.SIGTERM, None)
        self.assertEqual(context.exception.code, 128 + signal.SIGTERM)
        self.assertTrue(guard.requested)

    def test_signal_while_running_a_command_only_asks_to_stop(self):
        """No exception: the loop looks at `requested` after the command."""
        guard = ShutdownGuard()
        guard.handle(signal.SIGTERM, None)
        self.assertTrue(guard.requested)

    def test_a_second_signal_stops_at_once(self):
        """If the command does not finish, the player can still get out."""
        guard = ShutdownGuard()
        guard.handle(signal.SIGTERM, None)
        with self.assertRaises(GameInterrupted):
            guard.handle(signal.SIGINT, None)

    def test_waiting_flag_is_cleared_afterwards(self):
        """After the input is read, a signal no longer raises."""
        guard = ShutdownGuard()
        with guard.waiting():
            pass
        guard.handle(signal.SIGTERM, None)

    def test_waiting_flag_is_cleared_after_an_exception(self):
        """Even if reading fails, the flag goes back."""
        guard = ShutdownGuard()
        with self.assertRaises(EOFError):
            with guard.waiting():
                raise EOFError
        self.assertFalse(guard.is_waiting)

    def test_read_input_marks_the_wait(self):
        """read_input calls the reader while the guard says the game is waiting."""
        guard = ShutdownGuard()
        seen = []

        def reader(prompt):
            seen.append(guard.is_waiting)
            return "hello"

        self.assertEqual(guard.read_input(reader, "> "), "hello")
        self.assertEqual(seen, [True])
        self.assertFalse(guard.is_waiting)

    def test_game_interrupted_is_a_system_exit(self):
        """So nothing catches it by accident with `except Exception`."""
        self.assertTrue(issubclass(GameInterrupted, SystemExit))


class TestRealSignals(unittest.TestCase):
    """The handlers are really installed, and put back."""

    def setUp(self):
        """Install a guard; always restore the old handlers."""
        self.guard = ShutdownGuard()
        self.guard.install()
        self.addCleanup(self.guard.restore)

    def test_term_signal_during_input_raises(self):
        """A SIGTERM sent to ourselves while waiting raises GameInterrupted."""
        with self.assertRaises(GameInterrupted):
            with self.guard.waiting():
                signal.raise_signal(signal.SIGTERM)

    def test_interrupt_signal_during_input_raises(self):
        """Ctrl-C while waiting stops the game the same way."""
        with self.assertRaises(GameInterrupted):
            with self.guard.waiting():
                signal.raise_signal(signal.SIGINT)

    @unittest.skipUnless(hasattr(signal, "SIGHUP"), "no SIGHUP on this system")
    def test_hangup_signal_during_input_raises(self):
        """Closing the terminal window sends SIGHUP on Linux and macOS."""
        with self.assertRaises(GameInterrupted):
            with self.guard.waiting():
                signal.raise_signal(signal.SIGHUP)

    def test_restore_puts_the_old_handlers_back(self):
        """After restore, SIGTERM is as it was before."""
        before = signal.getsignal(signal.SIGTERM)
        guard = ShutdownGuard()
        guard.install()
        self.assertNotEqual(signal.getsignal(signal.SIGTERM), before)
        guard.restore()
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    @unittest.skipIf(os.name == "nt", "SIGBREAK only exists on Windows")
    def test_no_sigbreak_on_unix(self):
        """The guard only names signals the system has."""
        self.assertFalse(hasattr(signal, "SIGBREAK"))


class TestWindowsCloseHandler(unittest.TestCase):
    """Closing a Windows console window saves the game (the decision logic; Windows runs the rest)."""

    def test_closing_events_save_and_are_handled(self):
        """Window closed, logoff and shutdown."""
        for event in (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
            with self.subTest(event=event):
                saved = []
                handler = make_console_handler(lambda: saved.append(1))
                self.assertTrue(handler(event))
                self.assertEqual(saved, [1])

    def test_other_events_are_left_to_the_signal_handlers(self):
        """Ctrl-C (event 0) and Ctrl-Break (event 1) do not save here and are not handled."""
        saved = []
        handler = make_console_handler(lambda: saved.append(1))
        self.assertFalse(handler(0))
        self.assertFalse(handler(1))
        self.assertEqual(saved, [])

    @unittest.skipIf(os.name == "nt", "this checks the non-Windows answer")
    def test_installing_does_nothing_outside_windows(self):
        """No handler, and no error."""
        self.assertIsNone(install_windows_close_handler(lambda: None))


if __name__ == "__main__":
    unittest.main()
