"""The commands a player can type, and the code that runs them.

Every command is a function named do_<command>. It takes the game state and
a list of arguments, and returns the text to show the player, or a list of
frames for an animation (see show_frames in loop.py). The functions
never print anything themselves; that is the job of the loop in loop.py.
This keeps them easy to test.
"""

from engine.level_screen import intro_text
from render.world_map import load_map_art, map_screen, walk_frames


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


def extra_words_message(name):
    """Return the answer for a command that was typed with words after it.

    Commands like help and quit take nothing after their name, so
    "quit now" gets this answer instead of quietly ignoring "now".
    """
    return f"{name} does not take anything after it. Type just: {name}"


def do_help(state, arguments):
    """Return a list of all commands with a short description of each."""
    if arguments:
        return extra_words_message("help")
    lines = ["Commands:"]
    # COMMANDS is defined further down in this file. That is fine: Python
    # only looks the name up when do_help runs, and by then the whole file
    # has been read.
    for name in COMMANDS:
        # Each entry is (function, description). help only needs the
        # description, so the function goes into _, the usual Python name
        # for "a value that is not used".
        _, description = COMMANDS[name]
        lines.append(f"  {name:<8} {description}")
    return "\n".join(lines)


def level_ids(levels):
    """Return the ids of a list of levels, for example ["1-1", "1-2"]."""
    ids = []
    for level in levels:
        ids.append(level.id)
    return ids


def do_map(state, arguments):
    """Return the map of the current world, with ARIA at the current level."""
    if arguments:
        return extra_words_message("map")
    if not state.levels:
        return "No levels found. Level packs go in the levels/ folder."
    world = state.current_world()
    ids = level_ids(state.levels_in_world(world))
    current = state.find_level(state.current_level)
    if current is None:
        picture = map_screen(world, ids, None, load_map_art())
        return picture + "\n\nType play <level> to start, for example: play " + ids[0]
    picture = map_screen(world, ids, ids.index(current.id), load_map_art())
    return picture + f"\n\nYou are at [{current.id}] {current.title}."


def do_play(state, arguments):
    """Start the level whose id is given, for example "play 1-1".

    The answer is the level's intro: title, cutscene, tips and waves.
    If the player was already on another level in the same world, ARIA
    walks there first: the answer is then a list of map frames, and the
    last frame has the intro below the map.
    """
    if len(arguments) != 1:
        return "Usage: play <level>, for example: play 1-1"
    level_id = arguments[0]
    level = state.find_level(level_id)
    if level is None:
        return f"There is no level {level_id}. Type map to see the levels."
    previous = state.find_level(state.current_level)
    state.current_level = level.id
    intro = intro_text(level)
    if previous is None or previous.world != level.world or previous.id == level.id:
        return intro
    ids = level_ids(state.levels_in_world(level.world))
    frames = walk_frames(level.world, ids, ids.index(previous.id), ids.index(level.id),
                         load_map_art())
    frames[-1] = frames[-1] + "\n\n" + intro
    return frames


def do_submit(state, arguments):
    """Hand in the player's code for the current level.

    Grading arrives in Phase 2; for now this only checks that a level has
    been started.
    """
    if arguments:
        return extra_words_message("submit")
    if state.current_level is None:
        return "You are not playing a level. Type play <level> first."
    return f"Grading is not ready yet, so level {state.current_level} cannot be checked."


def do_quit(state, arguments):
    """Stop the game."""
    if arguments:
        return extra_words_message("quit")
    state.running = False
    return "Goodbye, technician."


# Every command the player can type. Each name maps to the function that
# runs it and a short description used by the help command.
COMMANDS = {
    "help": (do_help, "show this list of commands"),
    "map": (do_map, "show the world map"),
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
    # Each entry is (function, description); only the function is needed here.
    function, _ = COMMANDS[name]
    return function(state, arguments)
