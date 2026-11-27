"""The command loop: read a line, run the command, show the answer, repeat."""

import shutil
import time

from engine.autosave import AutoSaver
from engine.code_mode import prompt_for, show_wave
from engine.commands import do_map, handle_line
from engine.footer import footer_for
from engine.key_screens import MapScreen, is_map_answer
from engine.wave_screen import WaveScreen
from engine.screens import CONTINUE_PROMPT, SKIP_WORDS, split_screens, wrap_text

# How long each frame of an animation stays on screen, in seconds.
FRAME_SECONDS = 0.05

# Plain text is wrapped to the window, within these widths.
PLAIN_WIDTH = 80
MIN_WRAP_WIDTH = 40


def move_cursor_up(line_count):
    """Return the escape code that moves the cursor up `line_count` lines.

    The cursor also goes to the start of the line, so the next text is
    written over what was there.
    """
    return f"\x1b[{line_count}F"


def show_frames(frames, write, pause):
    """Show an animation: write each frame over the one before it.

    After a frame is written, the cursor is on the line below it. Moving
    up by the frame's number of lines puts it back on the frame's first
    line, so the next frame is drawn in the same place. pause(FRAME_SECONDS)
    is called between frames.
    """
    previous_height = 0
    for frame in frames:
        if previous_height == 0:
            write(frame)
        else:
            pause(FRAME_SECONDS)
            write(move_cursor_up(previous_height) + frame)
        previous_height = len(frame.split("\n"))


def start_text(state):
    """Return the screen to show when the game starts or resumes.

    A player who was typing a wave lands on that wave, with the code they
    had typed. Anyone else starts at the map.
    """
    level = state.find_level(state.current_level)
    if state.coding and level is not None:
        return show_wave(state)
    return do_map(state, [])


def save_and_report(autosaver, write, already_reported):
    """Save now. If it fails, tell the player once; return whether a failure was reported."""
    if autosaver is None:
        return already_reported
    if autosaver.save():
        return False
    if not already_reported:
        write(f"Could not save your progress: {autosaver.last_error}")
    return True


def show_screens(screens, write, read_line, width):
    """Write screens one at a time, waiting for Enter between them.

    Returns a line typed at a pause that still has to be handled, or None.
    """
    for screen in screens[:-1]:
        write(wrap_text(screen, width))
        typed = read_line(CONTINUE_PROMPT)
        if typed.strip() != "":
            write(wrap_text(screens[-1], width))
            if typed.strip().lower() in SKIP_WORDS:
                return None
            return typed
    write(wrap_text(screens[-1], width))
    return None


def show_answer(answer, write, pause, read_line=input, width=PLAIN_WIDTH):
    """Show what a command answered: a text, or a list of frames as an animation.

    Returns a line typed at a pause that still has to be handled, or None.
    """
    if isinstance(answer, list):
        screens = split_screens(answer[-1])
        screens[0] = wrap_text(screens[0], width)
        show_frames(answer[:-1] + [screens[0]], write, pause)
        if len(screens) == 1:
            return None
        typed = read_line(CONTINUE_PROMPT)
        if typed.strip().lower() not in [""] + SKIP_WORDS:
            write(wrap_text(screens[-1], width))
            return typed
        return show_screens(screens[1:], write, read_line, width)
    if answer:
        return show_screens(split_screens(answer), write, read_line, width)
    return None


def plain_width(get_size=shutil.get_terminal_size):
    """Return the width text is wrapped to: the window's, at most 80."""
    columns = get_size((PLAIN_WIDTH, 24))[0]
    return max(MIN_WRAP_WIDTH, min(PLAIN_WIDTH, columns))


def read_one_line(read_line, guard, display, prompt):
    """Read the player's next line: at the typing row of the full-screen display, and guarded against signals."""
    reader = read_line
    if display is not None:
        def reader(text):
            """Read through the display, which puts the cursor on the typing row."""
            return display.read(read_line, text)
    if guard is not None:
        return guard.read_input(reader, prompt)
    return reader(prompt)


def keep_on_the_map(state, map_screen, answer):
    """Return True if `answer` needs no screen of its own: the map shows it.

    That is the map itself, or a short message, which goes under the map.
    Only used in the key-driven mode.
    """
    if map_screen is None or state.coding or not state.running or isinstance(answer, list):
        return False
    if answer == "" or is_map_answer(state, answer):
        return True
    lines = answer.split("\n")
    if len(lines) == 1 and len(answer) <= PLAIN_WIDTH - 2 and "\f" not in answer:
        map_screen.message = answer
        return True
    return False


def run(state, read_line=input, write=print, save_path=None, pause=time.sleep,
        guard=None, autosaver=None, display=None, first_answer=None):
    """Keep asking for lines until the player quits.

    read_line and write default to input and print. Tests pass in their own
    functions instead, so they can script the player's typing and collect
    what the game shows.

    The game is saved after EVERY line, so closing the window or killing the
    process loses at most the line being typed. Give an `autosaver`, or a
    `save_path` to make one. If saving fails the player is told once and the
    game goes on.

    A command can answer with a list of frames instead of a text; they are
    shown as an animation, with pause between frames.

    `guard` (a ShutdownGuard) makes the loop stop after the current command
    when the system asks the game to stop, and lets a stop signal end the
    waiting for the player's typing. Ctrl-D (end of input) and Ctrl-C quit
    the same way as :quit.

    With a `display` (the full-screen mode) every answer is drawn as a screen
    by the display instead of being written as text.

    `first_answer` is shown before the first line is read. In the plain mode a
    footer follows every answer.
    """
    if autosaver is None and save_path is not None:
        autosaver = AutoSaver(state, save_path)
    width = plain_width()
    # With a keyboard, the map and the waves are worked with keys instead of typed commands.
    map_screen = None
    wave_screen = None

    def save_now():
        """Save while a wave is being edited; say once if that does not work."""
        nonlocal failure_reported
        failure_reported = save_and_report(autosaver, wave_report, failure_reported)

    def wave_report(text):
        """Show a save problem in the panel of the wave."""
        wave_screen.say("SNEK", text)

    if getattr(display, "keys", None) is not None and state.slots():
        map_screen = MapScreen(display, state)
        wave_screen = WaveScreen(display, state, save_now)

    def read(prompt):
        """Read one line through the guard and the display."""
        return read_one_line(read_line, guard, display, prompt)

    def present(answer):
        """Show an answer; return a line typed at a pause, or None."""
        if keep_on_the_map(state, map_screen, answer):
            return None
        if display is not None:
            return display.show(answer)
        typed = show_answer(answer, write, pause, read, width)
        if answer and typed is None and state.running:
            write(footer_for(state))
        return typed

    failure_reported = False
    queued = None
    if first_answer is not None:
        try:
            queued = present(first_answer)
        except (EOFError, KeyboardInterrupt):
            write("")
            queued = ":quit"
    while state.running:
        try:
            if queued is not None:
                line, queued = queued, None
            elif map_screen is not None and not state.coding and state.pending is None:
                line = map_screen.next_line()
            elif wave_screen is not None and state.coding and state.pending is None:
                line = wave_screen.run()
            else:
                line = read(prompt_for(state))
        except (EOFError, KeyboardInterrupt):
            # Start on a fresh line, because the terminal is still on the prompt.
            write("")
            line = ":quit"
        except OSError:
            # The terminal is gone (the window was closed). Stop.
            state.running = False
            break
        combo_before = state.combo
        answer = handle_line(state, line)
        # Save before showing: a screen may wait at a pause for a long time.
        failure_reported = save_and_report(autosaver, write, failure_reported)
        try:
            queued = present(answer)
            if display is not None:
                display.after_command(combo_before)
        except (EOFError, KeyboardInterrupt):
            write("")
            queued = ":quit"
        except OSError:
            # The terminal is gone (the window was closed). Save and stop.
            state.running = False
        if guard is not None and guard.requested:
            state.running = False
