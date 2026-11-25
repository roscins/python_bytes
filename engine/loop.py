"""The command loop: read a line, run the command, show the answer, repeat."""

import time

from engine.autosave import AutoSaver
from engine.code_mode import prompt_for, show_wave
from engine.commands import do_map, handle_line

# How long each frame of an animation stays on screen, in seconds.
FRAME_SECONDS = 0.05


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


def show_answer(answer, write, pause):
    """Show what a command answered: a text, or a list of frames as an animation."""
    if isinstance(answer, list):
        show_frames(answer, write, pause)
    elif answer:
        write(answer)


def run(state, read_line=input, write=print, save_path=None, pause=time.sleep,
        guard=None, autosaver=None):
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
    """
    if autosaver is None and save_path is not None:
        autosaver = AutoSaver(state, save_path)
    failure_reported = False
    while state.running:
        prompt = prompt_for(state)
        try:
            if guard is not None:
                line = guard.read_input(read_line, prompt)
            else:
                line = read_line(prompt)
        except (EOFError, KeyboardInterrupt):
            # Start on a fresh line, because the terminal is still on the prompt.
            write("")
            line = ":quit"
        answer = handle_line(state, line)
        try:
            show_answer(answer, write, pause)
        except OSError:
            # The terminal is gone (the window was closed). Save and stop.
            state.running = False
        failure_reported = save_and_report(autosaver, write, failure_reported)
        if guard is not None and guard.requested:
            state.running = False
