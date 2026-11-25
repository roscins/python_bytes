"""The command loop: read a line, run the command, show the answer, repeat."""

import time

from engine.commands import handle_line
from engine.save_file import save_progress

PROMPT = "> "
WELCOME = "PYTHON BYTES. Type help to see the commands."

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


def welcome_text(state):
    """Return the text shown when the game starts.

    A player who saved while playing a level is told where they were.
    """
    if state.current_level is None:
        return WELCOME
    return f"{WELCOME}\nWelcome back. You were on level {state.current_level}."


def run(state, read_line=input, write=print, save_path=None, pause=time.sleep):
    """Keep asking for commands until the player quits.

    read_line and write default to input and print. Tests pass in their own
    functions instead, so they can script the player's typing and collect
    what the game shows.

    If save_path is given, the progress is saved there after every command.

    A command can answer with a list of frames instead of a text; they are
    shown as an animation, with pause (time.sleep unless a test passes its
    own) between frames.
    If saving fails, the player is told and the game goes on.

    Pressing Ctrl-D (end of input) or Ctrl-C (interrupt) quits the game the
    same way as typing quit.
    """
    write(welcome_text(state))
    while state.running:
        try:
            line = read_line(PROMPT)
        except (EOFError, KeyboardInterrupt):
            # Start on a fresh line, because the terminal is still on the prompt.
            write("")
            line = "quit"
        answer = handle_line(state, line)
        if isinstance(answer, list):
            show_frames(answer, write, pause)
        elif answer:
            write(answer)
        if save_path is not None:
            try:
                save_progress(state, save_path)
            except OSError as error:
                write(f"Could not save your progress: {error}")
