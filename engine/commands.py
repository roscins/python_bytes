"""The commands a player can type, and the code that runs them.

Every command is a function named do_<command>. It takes the game state and
a list of arguments, and returns the text to show the player, or a list of
frames for an animation (see show_frames in loop.py). The functions
never print anything themselves; that is the job of the loop in loop.py.
This keeps them easy to test.
"""

from engine.boss_turns import start_boss_fight, submit_to_boss
from engine.code_mode import (
    CODE_COMMANDS,
    NOT_PLAYING,
    add_code_line,
    current_context,
    show_wave,
    start_coding,
)
from engine.hints import ask_for_hint
from engine.hud import map_status
from engine.level_screen import HELP_LINE, boss_intro_text, intro_text
from engine.results_screen import results_text
from engine.rewards import apply_submission
from engine.scoring import PASS_MARK, is_unlocked
from engine.submission import grade_text
from engine.workspace import level_folder, wave_file_name
from render.level_clear import level_clear_frames, load_clear_art
from render.world_map import load_map_art, map_screen, slither_frames


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
    lines = ["Commands (while you are coding, type a colon first, for example :submit):"]
    # COMMANDS is defined further down in this file. That is fine: Python
    # only looks the name up when do_help runs, and by then the whole file
    # has been read.
    for name in COMMANDS:
        # Each entry is (function, description). help only needs the
        # description, so the function goes into _, the usual Python name
        # for "a value that is not used".
        _, description = COMMANDS[name]
        lines.append(f"  {name:<8} {description}")
    lines.append("While you code (always with a colon in front):")
    for name in CODE_COMMANDS:
        _, description = CODE_COMMANDS[name]
        lines.append(f"  :{name:<7} {description}")
    return "\n".join(lines)


def slot_index(slots, level_id):
    """Return the position of the slot with this id in a list of slots."""
    for index in range(len(slots)):
        if slots[index].id == level_id:
            return index
    return -1


def level_ids(levels):
    """Return the ids of a list of levels, for example ["1-1", "1-2"]."""
    ids = []
    for level in levels:
        ids.append(level.id)
    return ids


def do_map(state, arguments):
    """Return the map of the current world, with Snek at the current level."""
    if arguments:
        return extra_words_message("map")
    state.coding = False
    if not state.slots():
        return "No levels found. Level packs go in the levels/ folder."
    world = state.current_world()
    world_slots = state.slots_in_world(world)
    ids = level_ids(world_slots)
    status = map_status(state, world_slots)
    current = state.find_level(state.current_level)
    if current is None:
        picture = map_screen(world, ids, None, load_map_art(), status)
        return picture + "\n\nType play <level> to start, for example: play " + ids[0]
    picture = map_screen(world, ids, ids.index(current.id), load_map_art(), status)
    return picture + f"\n\nYou are at [{current.id}] {current.title}."


def do_play(state, arguments):
    """Start the level whose id is given, for example "play 1-1".

    A locked level cannot be played: the level before it must be cleared
    first. The answer is the level's intro: title, cutscene, tips and waves.
    The player is then in code mode on the first wave that is not done yet,
    and the intro ends with that wave and the code typed so far. A boss
    level starts a boss fight and shows the boss screen.
    If the player was already on another level in the same world, Snek
    slithers there first: the answer is then a list of map frames, and the
    last frame has the intro below the map.
    """
    if len(arguments) != 1:
        return "Usage: play <level>, for example: play 1-1"
    level_id = arguments[0]
    level = state.find_level(level_id)
    if level is None:
        if state.find_slot(level_id) is not None:
            return f"Level {level_id} is not written yet. Type map to see the levels."
        return f"There is no level {level_id}. Type map to see the levels."
    slots = state.slots()
    if not is_unlocked(slots, state.cleared, level):
        before = slots[slot_index(slots, level.id) - 1]
        return f"Level {level.id} is locked. Clear {before.id} with at least {PASS_MARK} % first."
    previous = state.find_level(state.current_level)
    start_coding(state, level)
    if level.boss:
        intro = boss_intro_text(level) + "\n\n" + start_boss_fight(state, level) + "\n\n" + HELP_LINE
    else:
        intro = intro_text(level) + "\n\n" + show_wave(state)
    if previous is None or previous.world != level.world or previous.id == level.id:
        return intro
    world_slots = state.slots_in_world(level.world)
    ids = level_ids(world_slots)
    frames = slither_frames(level.world, ids, ids.index(previous.id), ids.index(level.id),
                            load_map_art(), map_status(state, world_slots))
    frames[-1] = frames[-1] + "\n\n" + intro
    return frames


def advance_after_submit(state, level, number, result):
    """Move to the next wave if wave `number` passed; return what to show under the results."""
    if not result.all_passed():
        return "Not yet. Change your code and :submit again, or buy a :hint."
    if number < len(level.waves):
        state.current_wave = number + 1
        return f"Wave {number} passed! Next:\n\n" + show_wave(state)
    state.coding = False
    return f"Wave {number} passed, and that was the last wave. Type map to see where to go next."


def do_submit(state, arguments):
    """Grade the code of the current wave and show the results and score.

    A wave with full marks is not graded again. When every test of a wave
    passes, the player moves on to the next wave. Clearing a level, or
    earning more stars, shows the level-clear animation above the results.
    In a boss level, submit is a hit on the boss instead.
    """
    if arguments:
        return extra_words_message("submit")
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    if level.boss:
        return submit_to_boss(state, level)
    wave = level.waves[number - 1]
    progress = state.progress_for(level)
    if progress.wave_is_perfect(number, wave):
        return f"Wave {number} already passed \u2713. Type :wave <n> to go to another wave."
    submission = grade_text(wave, number, state.wave_text(level, number))
    if submission.result is None:
        return "Your code is empty. Type your first line, then :submit."
    reward = apply_submission(state, level, [submission])
    results = results_text(level, [submission], [], reward)
    results = results + "\n\n" + advance_after_submit(state, level, number, submission.result)
    if not reward.cleared_now and reward.stars <= reward.old_stars:
        return results
    frames = level_clear_frames(level.id, level.title, reward.best_score, reward.stars,
                                reward.xp_gained, reward.coins_gained, level.power_up,
                                load_clear_art())
    frames[-1] = frames[-1] + "\n\n" + results
    return frames


def do_hint(state, arguments):
    """Show the hints bought for a wave, and buy the next one, for example "hint 2"."""
    usage = "Usage: hint <wave>, for example: hint 2 (or just :hint for the wave you are on)"
    if len(arguments) > 1:
        return usage
    level = state.find_level(state.current_level)
    if level is None:
        return NOT_PLAYING
    if not arguments:
        return ask_for_hint(state, level, state.current_wave)
    if not arguments[0].isdigit():
        return usage
    number = int(arguments[0])
    if number < 1 or number > len(level.waves):
        return f"Level {level.id} has waves 1 to {len(level.waves)}."
    return ask_for_hint(state, level, number)


def do_where(state, arguments):
    """Save the code of the current wave to a file you can open in an editor; return its path."""
    if arguments:
        return extra_words_message("where")
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    if state.workspace_root is None:
        return "There is no workspace folder."
    folder = level_folder(level, state.workspace_root)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / wave_file_name(level.waves[number - 1], number)
    path.write_text(state.wave_text(level, number), encoding="utf-8")
    return f"Saved the code of wave {number} to {path.resolve()}"


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
    "submit": (do_submit, "hand in the code of the wave you are on"),
    "hint": (do_hint, "buy a hint with coins, for example: hint 2 (or :hint)"),
    "where": (do_where, "save this wave's code in a file to open in an editor"),
    "quit": (do_quit, "leave the game"),
}


def run_command(state, text, colon):
    """Run the command at the start of `text`. `colon` is True if it was typed with a colon.

    The commands of code mode (:edit, :undo ...) only exist with a colon.
    """
    name, arguments = parse_command(text)
    if name == "":
        return ""
    if colon and name in CODE_COMMANDS:
        function, _ = CODE_COMMANDS[name]
        # They want the text after the command name exactly as typed, because
        # the spaces in ":edit 2     print(x)" are the code's indentation.
        return function(state, text.lstrip()[len(name):])
    if name not in COMMANDS:
        if colon:
            return f"Unknown command: :{name}. Type :help to see the commands."
        return f"Unknown command: {name}. Type help to see the commands."
    # Each entry is (function, description); only the function is needed here.
    function, _ = COMMANDS[name]
    return function(state, arguments)


def handle_line(state, line):
    """Run the line the player typed and return the text to show.

    A line that starts with ":" is a command. Any other line is a line of
    code while the player is in code mode, and a command otherwise. A blank
    line outside code mode returns an empty string.
    """
    if line.startswith(":"):
        return run_command(state, line[1:], colon=True)
    if state.coding:
        return add_code_line(state, line)
    return run_command(state, line, colon=False)
