"""The commands a player can type, and the code that runs them.

Every command is a function named do_<command>. It takes the game state and
a list of arguments, and returns the text to show the player. The functions
never print anything themselves; that is the job of the loop in loop.py.
This keeps them easy to test.
"""


def parse_command(line):
    """Split a typed line into a command name and a list of arguments.

    The command name is made lower-case so "HELP" and "help" mean the same.
    An empty or blank line gives an empty name and no arguments.

    Example: parse_command("play 1-2") returns ("play", ["1-2"]).
    """
    words = line.split()
    if not words:
        return "", []
    name = words[0].lower()
    arguments = words[1:]
    return name, arguments


def do_help(state, arguments):
    """Return a list of all commands with a short description of each."""
    lines = ["Commands:"]
    for name, (function, description) in COMMANDS.items():
        lines.append(f"  {name:<8} {description}")
    return "\n".join(lines)


def do_map(state, arguments):
    """Return the list of levels, marking the one being played."""
    lines = ["Levels:"]
    for level_id in state.levels:
        if level_id == state.current_level:
            lines.append(f"  [{level_id}]  <- you are here")
        else:
            lines.append(f"  [{level_id}]")
    return "\n".join(lines)


def do_play(state, arguments):
    """Start the level whose id is given, for example "play 1-1"."""
    if len(arguments) != 1:
        return "Usage: play <level>, for example: play 1-1"
    level_id = arguments[0]
    if level_id not in state.levels:
        return f"There is no level {level_id}. Type map to see the levels."
    state.current_level = level_id
    return f"Starting level {level_id}."


def do_submit(state, arguments):
    """Hand in the player's code for the current level.

    Grading arrives in Phase 2; for now this only checks that a level has
    been started.
    """
    if state.current_level is None:
        return "You are not playing a level. Type play <level> first."
    return f"Grading is not ready yet, so level {state.current_level} cannot be checked."


def do_quit(state, arguments):
    """Stop the game."""
    state.running = False
    return "Goodbye, technician."


# Every command the player can type. Each name maps to the function that
# runs it and a short description used by the help command.
COMMANDS = {
    "help": (do_help, "show this list of commands"),
    "map": (do_map, "show the levels"),
    "play": (do_play, "start a level, for example: play 1-1"),
    "submit": (do_submit, "hand in your code for the current level"),
    "quit": (do_quit, "leave the game"),
}


def handle_line(state, line):
    """Run the command typed on one line and return the text to show.

    A blank line returns an empty string. An unknown command returns a hint
    to type help.
    """
    name, arguments = parse_command(line)
    if name == "":
        return ""
    if name not in COMMANDS:
        return f"Unknown command: {name}. Type help to see the commands."
    function, description = COMMANDS[name]
    return function(state, arguments)
