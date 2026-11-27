"""Start the game with: python play.py  (or python -m engine)"""

import argparse
import os
import sys
import time
from pathlib import Path

from engine.autosave import AutoSaver
from engine.game_state import GameState
from engine.level_pack import LevelError, load_levels
from engine.loop import run, start_text
from engine.save_file import DEFAULT_SAVE_PATH, load_progress, set_aside_broken_save
from engine.display import Display
from engine.shutdown import GameInterrupted, ShutdownGuard, install_windows_close_handler
from engine.terminal import (
    EnterWatcher,
    default_write,
    enable_virtual_terminal,
    supports_truecolor,
    terminal_size,
)
from engine.title import NEW, QUIT, ask_title, inspect_save, keep_old_save
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


def write_line(text):
    """Print a line and push it out at once, so a program reading our output sees it."""
    print(text, flush=True)


def make_real_display(state):
    """Return a Display for the real terminal, or None if it cannot do full screen.

    A Windows console that cannot be switched to colour codes, or input that
    is not a terminal, gets the plain mode.
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None
    if not enable_virtual_terminal():
        return None
    return Display(state, default_write, size=terminal_size, sleep=time.sleep,
                   skipped=EnterWatcher(sys.stdin).pressed, truecolor=supports_truecolor())


def choose_how_to_start(state, info, save_path, read_line, write, plain):
    """Show the title screen and set the game up as the player chose.

    Returns "play" to start the command loop, or "quit". A save that cannot
    be read is never deleted: it is set aside as .broken (or kept as .old
    for a new game over a good save).
    """
    choice = ask_title(info, read_line, write, plain)
    if choice == QUIT:
        return "quit"
    if choice == NEW:
        if info.status == "ok":
            keep_old_save(save_path)
        elif info.status == "damaged":
            write(f"The damaged save was moved to {set_aside_broken_save(save_path)}")
        return "play"
    load_progress(state, save_path)
    return "play"


def run_game(levels_folder=LEVELS_FOLDER, save_path=DEFAULT_SAVE_PATH,
             workspace_root=WORKSPACE_FOLDER, concepts_file=CONCEPTS_FILE,
             read_line=input, write=write_line, plain=False, install_signals=True,
             pause=time.sleep, color=None, display_factory=None):
    """Load the levels, show the title screen, run the game, and return an exit code.

    levels/concepts.toml (`concepts_file`) lists every level of the game, so
    the map can show levels that are not written yet. Pass None to show only
    the level packs. `workspace_root` is only used by the :where command.

    `plain` means no box characters. `color` colours the player's code; it is
    on unless the game is plain or the NO_COLOR variable is set (see
    no-color.org), and tests pass it explicitly.

    Unless `plain`, the game runs full screen on a real terminal (see
    engine/display.py). `display_factory(state)` makes the display (tests give
    one on a fake terminal). The terminal is always put back when the game ends, also after
    an error or a stop signal.

    The game saves after every typed line. When the system asks the game to
    stop (Ctrl-C, kill, a closed terminal) the game saves and leaves with the
    exit code 128 + the signal number.
    A broken level stops the game, because it is a mistake in the game
    itself. A broken save does not: it is set aside and the game starts
    fresh. A save that cannot be opened at all stops the game.
    """
    try:
        levels = load_levels(levels_folder)
    except (OSError, LevelError) as error:
        write(f"Cannot load the levels: {error}")
        return 1
    try:
        curriculum = load_game_curriculum(concepts_file, levels)
    except ValueError as error:
        write(f"Cannot load the levels: {error}")
        return 1
    state = GameState(levels, workspace_root, curriculum)
    state.plain = plain
    if color is None:
        color = not plain and "NO_COLOR" not in os.environ
    state.color = color
    display = None
    if display_factory is not None:
        display = display_factory(state)
    elif not plain:
        display = make_real_display(state)
    if display is not None:
        state.plain = False
        state.color = True
    guard = ShutdownGuard()
    autosaver = AutoSaver(state, save_path)
    close_handler = None
    if install_signals:
        guard.install()
        # Windows has no SIGHUP: this is how closing the window reaches us.
        # The variable keeps the handler alive until the game ends.
        close_handler = install_windows_close_handler(autosaver.save)
    try:
        return play_session(state, autosaver, guard, read_line, write, plain, pause, display)
    except GameInterrupted as stop:
        autosaver.save()
        return stop.code
    finally:
        if display is not None:
            display.stop()
        guard.restore()
        state.close()
        del close_handler


def play_session(state, autosaver, guard, read_line, write, plain, pause, display=None):
    """The part of run_game that happens after the levels are loaded.

    With a display, everything the game says is drawn as a screen, and the
    title starts with the logo animation.
    """
    save_path = autosaver.path
    info = inspect_save(save_path, state.levels, state.curriculum)
    say = write
    if display is not None:
        display.read_line = lambda prompt: guard.read_input(read_line, prompt)
        display.start()
        display.show_title()
        say = display.show
    try:
        guarded_read = guard.read_input
        how = choose_how_to_start(
            state, info, save_path, lambda prompt: reader_for(display, guarded_read, read_line, prompt),
            say, plain)
    except OSError as error:
        # The file is there but cannot be opened, for example because of its
        # permissions. Moving it would fail too, so the game stops.
        if display is not None:
            display.stop()
        write(f"Cannot open your save file: {error}")
        return 1
    if how == "quit":
        if display is not None:
            display.stop()
            write("Goodbye, technician.")
        return 0
    say(start_text(state))
    autosaver.save()
    run(state, read_line, write, pause=pause, guard=guard, autosaver=autosaver, display=display)
    autosaver.save()
    if display is not None:
        display.stop()
        write("Goodbye, technician.")
    return 0


def reader_for(display, guarded_read, read_line, prompt):
    """Read a line for the title screen: through the display when there is one."""
    if display is None:
        return guarded_read(read_line, prompt)
    return guarded_read(lambda text: display.read(read_line, text), prompt)


def parse_arguments(argv):
    """Read the command line: --plain and --save PATH."""
    parser = argparse.ArgumentParser(prog="python play.py", description="Python Bytes: learn Python by playing.")
    parser.add_argument("--plain", action="store_true",
                        help="plain text: no box characters (for screen readers and logs)")
    parser.add_argument("--save", default=str(DEFAULT_SAVE_PATH), metavar="PATH",
                        help="where the game is saved (default: %(default)s)")
    return parser.parse_args(argv)


def wants_plain(arguments, environment=os.environ, is_terminal=None):
    """Return True if the plain look is wanted: --plain, output that is not a terminal, or NO_COLOR.

    NO_COLOR (see no-color.org) asks programs not to use colour; the full-screen
    game is built on colour, so it then runs in the plain mode.
    """
    if is_terminal is None:
        is_terminal = sys.stdout.isatty() and sys.stdin.isatty()
    return arguments.plain or not is_terminal or "NO_COLOR" in environment


def main(argv=None):
    """Start the game from the command line (python play.py) and return the exit code."""
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    return run_game(save_path=Path(arguments.save), plain=wants_plain(arguments))


if __name__ == "__main__":
    sys.exit(main())
