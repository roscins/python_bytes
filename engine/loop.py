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


def run(state, read_line=input, write=print, save_path=None, pause=time.sleep,
        guard=None, autosaver=None, display=None):
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
    """
    if autosaver is None and save_path is not None:
        autosaver = AutoSaver(state, save_path)
    failure_reported = False
    while state.running:
        prompt = prompt_for(state)
        try:
            line = read_one_line(read_line, guard, display, prompt)
        except (EOFError, KeyboardInterrupt):
            # Start on a fresh line, because the terminal is still on the prompt.
            write("")
            line = ":quit"
        combo_before = state.combo
        answer = handle_line(state, line)
        try:
            if display is not None:
                display.show(answer)
                display.after_command(combo_before)
            else:
                show_answer(answer, write, pause)
        except OSError:
            # The terminal is gone (the window was closed). Save and stop.
            state.running = False
        failure_reported = save_and_report(autosaver, write, failure_reported)
        if guard is not None and guard.requested:
            state.running = False
