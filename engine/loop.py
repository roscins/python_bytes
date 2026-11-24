"""The command loop: read a line, run the command, show the answer, repeat."""

from engine.commands import handle_line
from engine.save_file import save_progress

PROMPT = "> "
WELCOME = "PYTHON BYTES. Type help to see the commands."


def welcome_text(state):
    """Return the text shown when the game starts.

    A player who saved while playing a level is told where they were.
    """
    if state.current_level is None:
        return WELCOME
    return f"{WELCOME}\nWelcome back. You were on level {state.current_level}."


def run(state, read_line=input, write=print, save_path=None):
    """Keep asking for commands until the player quits.

    read_line and write default to input and print. Tests pass in their own
    functions instead, so they can script the player's typing and collect
    what the game shows.

    If save_path is given, the progress is saved there after every command.
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
        if answer:
            write(answer)
        if save_path is not None:
            try:
                save_progress(state, save_path)
            except OSError as error:
                write(f"Could not save your progress: {error}")
