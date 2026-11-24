"""The command loop: read a line, run the command, show the answer, repeat."""

from engine.commands import handle_line

PROMPT = "> "
WELCOME = "PYTHON BYTES. Type help to see the commands."


def run(state, read_line=input, write=print):
    """Keep asking for commands until the player quits.

    read_line and write default to input and print. Tests pass in their own
    functions instead, so they can script the player's typing and collect
    what the game shows.

    Pressing Ctrl-D (end of input) or Ctrl-C (interrupt) quits the game the
    same way as typing quit.
    """
    write(WELCOME)
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
