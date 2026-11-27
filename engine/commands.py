"""The commands a player can type, and the code that runs them.

Every command is a function named do_<command>. It takes the game state and
a list of arguments, and returns the text to show the player, or a list of
frames for an animation (see show_frames in loop.py). The functions
never print anything themselves; that is the job of the loop in loop.py.
This keeps them easy to test.
"""

import ast
import re

from engine.boss_turns import start_boss_fight, submit_to_boss
from engine.code_mode import (
    CODE_COMMANDS,
    NOT_PLAYING,
    add_code_line,
    current_context,
    show_wave,
    start_coding,
)
from engine.console import continue_pending, do_cancel, do_run, run_python_line
from engine.fill import is_filling
from engine.hints import ask_for_hint
from engine.hud import map_status
from engine.level_screen import boss_intro_text, intro_text
from engine.powerups import POWER_UPS, earned_help_lines, is_python_line, use_power_up
from engine.progression_help import next_level_to_play
from engine.results_screen import results_text
from engine.rewards import apply_submission
from engine.scoring import GUESSES_BEFORE_REVEAL, is_unlocked
from engine.screens import join_screens
from engine.stats import stats_text
from engine.submission import grade_text
from engine.suggest import CODE_WORDS, closest, did_you_mean
from engine.workspace import export_wave
from grader.answer_sheet import LETTERS
from render.level_clear import level_clear_frames, level_clear_text, load_clear_art
from render.world_map import load_map_art, map_screen, slither_frames, text_map


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
    at_the_map = "type the word"
    if state.keys:
        at_the_map = "press : and type the word"
    lines = [f"Commands. At the map {at_the_map}; in a wave put a colon first, like :submit."]
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
    for name in ALL_CODE_COMMANDS:
        _, description = ALL_CODE_COMMANDS[name]
        lines.append(f"  :{name:<7} {description}")
    if state.keys:
        # Waves are worked with keys and buttons, so only the map's words are listed.
        lines = ["On the map press : and type one of these. In a wave, Help shows the keys."]
        for name in ["map", "stats", "play", "quit"]:
            lines.append(f"  {name:<8} {COMMANDS[name][1]}")
    lines.extend(earned_help_lines(state))
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
    snek_index = None
    if current is not None:
        snek_index = ids.index(current.id)
    if state.plain:
        picture = text_map(world, ids, snek_index, status)
    else:
        picture = map_screen(world, ids, snek_index, load_map_art(), status)
    gap = "\n\n"
    if state.plain:
        picture = picture + "\n\n\u2605 stars earned \u00b7 locked: clear the level before it \u00b7 COINS buy hints"
        gap = "\n"
    if current is None:
        return picture + gap + "Type play <level> to start, for example: play " + ids[0]
    return picture + gap + f"You are at [{current.id}] {current.title}."


def see_the_map(state):
    """Return the advice to look at the map, which only line mode needs to type."""
    if state.keys:
        return ""
    return " Type map to see the levels."


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
        usage = "Usage: play <level>, for example: play 1-1"
        following = next_level_to_play(state)
        if following is not None:
            usage = usage + f"\nYour next level: play {following.id}"
        return usage
    level_id = arguments[0]
    level = state.find_level(level_id)
    if level is None:
        if state.find_slot(level_id) is not None:
            return f"Level {level_id} is not written yet." + see_the_map(state)
        meant = level_id.replace(".", "-").replace("_", "-")
        if state.find_level(meant) is not None:
            return f"There is no level {level_id}. Did you mean play {meant}?"
        return f"There is no level {level_id}." + see_the_map(state)
    slots = state.slots()
    if not is_unlocked(slots, state.cleared, level):
        before = slots[slot_index(slots, level.id) - 1]
        return f"Level {level.id} is locked. Pass every wave of {before.id} first."
    previous = state.find_level(state.current_level)
    start_coding(state, level)
    if level.boss:
        intro = join_screens([boss_intro_text(level, state.keys), start_boss_fight(state, level),
                              show_wave(state)])
    else:
        intro = join_screens([intro_text(level, state.keys), show_wave(state)])
    # The plain mode has no pictures, so Snek does not slither there.
    if state.plain or previous is None or previous.world != level.world or previous.id == level.id:
        return intro
    world_slots = state.slots_in_world(level.world)
    ids = level_ids(world_slots)
    frames = slither_frames(level.world, ids, ids.index(previous.id), ids.index(level.id),
                            load_map_art(), map_status(state, world_slots))
    frames[-1] = frames[-1] + "\n\n" + intro
    return frames


def reveal_text(wave):
    """Return the right answer of a wave and why, for after the last guess."""
    if wave.mode == "choice":
        lines = [f"That was guess {GUESSES_BEFORE_REVEAL}. The answers are:"]
        for number, question in enumerate(wave.questions, start=1):
            option = question["options"][LETTERS.index(question["answer"])]
            lines.append(f"  {number}: {question['answer']}) {option}")
            lines.append(f"     {question['explanation'].strip()}")
    elif wave.mode == "review":
        lines = [f"That was guess {GUESSES_BEFORE_REVEAL}. The faults are:"]
        for fault in wave.faults:
            category = wave.categories[LETTERS.index(fault["category"])]
            lines.append(f"  line {fault['line']}: {fault['category']}) {category}")
            lines.append(f"     {fault['explanation'].strip()}")
    else:
        lines = [f"That was guess {GUESSES_BEFORE_REVEAL}. The program prints:"]
        for line in wave.answer.rstrip("\n").split("\n"):
            lines.append("    " + line)
        if wave.explanation:
            lines.append("Why:")
            for line in wave.explanation.strip().split("\n"):
                lines.append("  " + line)
    lines.append("The wave counts as done, at half of its score.")
    return "\n".join(lines)


def advance_after_submit(state, level, number, result):
    """Move on if wave `number` passed or was revealed; return what to show under the results."""
    wave = level.waves[number - 1]
    progress = state.progress_for(level)
    revealed = progress.revealed[number - 1]
    if not result.all_passed() and not revealed:
        if wave.mode == "predict" or wave.is_quiz():
            left = GUESSES_BEFORE_REVEAL - progress.wave_attempts[number - 1]
            return (f"Not yet. Change your answer and :submit again, or buy a :hint.\n"
                    f"Wrong guesses left before Snek shows the output: {left}")
        again = "Not yet. Change your code and :submit again, or buy a :hint."
        if wave.goal is not None:
            again = again + f"\nGOAL: {wave.goal}"
        return again
    start = f"Wave {number} passed"
    before = ""
    if revealed:
        start = f"Wave {number} is done"
        before = reveal_text(wave) + "\n\n"
    if number < len(level.waves):
        state.current_wave = number + 1
        return before + f"{start}! Next:\n\n" + show_wave(state)
    state.coding = False
    following = next_level_to_play(state)
    where = "Type map to see where to go next."
    if following is not None and level.id in state.cleared:
        where = f"Next: play {following.id}"
    return before + f"{start}, and that was the last wave. {where}"


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
        return submission.problem or "Your code is empty. Type your first line, then :submit."
    reward = apply_submission(state, level, [submission])
    results = results_text(level, [submission], [], reward)
    results = results + "\n\n" + advance_after_submit(state, level, number, submission.result)
    if not has_earned_the_animation(reward):
        return results
    if state.plain:
        return level_clear_text(level.id, level.title, reward.best_score, reward.stars,
                                reward.coins_gained, level.power_up) + "\n\n" + results
    frames = clear_frames(state, level, reward)
    frames[-1] = frames[-1] + "\n\n" + results
    return frames


def has_earned_the_animation(reward):
    """Return True if the level is cleared now, or a cleared level earned more stars."""
    more_stars = reward.is_cleared and reward.stars > reward.old_stars
    return reward.cleared_now or more_stars


def clear_frames(state, level, reward):
    """Return the frames of the level-clear animation, or None if this submit did not earn it."""
    if not has_earned_the_animation(reward):
        return None
    return level_clear_frames(level.id, level.title, reward.best_score, reward.stars,
                              reward.coins_gained, level.power_up, load_clear_art())


def do_stats(state, arguments):
    """Return levels cleared and stars, world by world."""
    if arguments:
        return extra_words_message("stats")
    return stats_text(state)


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
    path = export_wave(level, number, state.wave_text(level, number), state.workspace_root)
    for name, text in level.waves[number - 1].files.items():
        (path.parent / name).write_text(text, encoding="utf-8")
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
    "stats": (do_stats, "show levels cleared and stars, world by world"),
    "play": (do_play, "start a level, for example: play 1-1"),
    "submit": (do_submit, "hand in the code of the wave you are on"),
    "hint": (do_hint, "buy a hint with coins, for example: hint 2 (or :hint)"),
    "where": (do_where, "save this wave's code in a file to open in an editor"),
    "quit": (do_quit, "leave the game"),
}


# The commands typed with a colon: the ones for code mode, plus :run and :cancel.
ALL_CODE_COMMANDS = dict(CODE_COMMANDS)
ALL_CODE_COMMANDS["run"] = (do_run, "try your code without handing it in (not graded)")
ALL_CODE_COMMANDS["cancel"] = (do_cancel, "stop what you were typing (a block, an edit, input)")


def run_command(state, text, colon):
    """Run the command at the start of `text`. `colon` is True if it was typed with a colon.

    The commands of code mode (:edit, :undo ...) only exist with a colon.
    A word without a colon that is not a command is Python: it goes to the
    quick console.
    """
    name, arguments = parse_command(text)
    if name == "":
        return ""
    if colon and name in ALL_CODE_COMMANDS:
        function, _ = ALL_CODE_COMMANDS[name]
        # They want the text after the command name exactly as typed, because
        # the spaces in ":edit 2     print(x)" are the code's indentation.
        return function(state, text.lstrip()[len(name):])
    rest = text.lstrip()[len(name):]
    # Key mode has no colon commands, but "show sensors.csv" reads a data file.
    if name == "show" and rest.strip() in state.wave_files():
        return ALL_CODE_COMMANDS["show"][0](state, rest)
    if name in POWER_UPS and not is_python_line(rest):
        return use_power_up(state, name, rest)
    # "stats = 5" is a player's own variable, not the command.
    if name not in COMMANDS or (name == "stats" and is_python_line(rest)):
        if colon:
            return (f"Unknown command: :{name}. Type :help to see the commands."
                    + did_you_mean(name, CODE_WORDS, colon=True))
        return run_python_line(state, text)
    # Each entry is (function, description); only the function is needed here.
    function, _ = COMMANDS[name]
    return function(state, arguments)


def is_bare_command(line):
    """Return True for a line that is exactly "submit", "hint" or "hint 2"."""
    words = line.split(" ")
    if words == ["submit"] or words == ["hint"]:
        return True
    return len(words) == 2 and words[0] == "hint" and words[1].isdigit()


def code_has_name(code, name):
    """Return True if the player's code makes something called `name`."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        pattern = rf"^\s*(?:def\s+{name}\b|{name}\s*=[^=])"
        return re.search(pattern, code, re.MULTILINE) is not None
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store):
            return True
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return True
    return False


def code_mode_line(state, line):
    """Handle a line typed in a wave: usually code, sometimes a command without its colon."""
    level, number = current_context(state)
    if level is None:
        return add_code_line(state, line)
    code = state.wave_text(level, number)
    word = line.split(" ")[0]
    if is_bare_command(line):
        if not code_has_name(code, word):
            return run_command(state, line, colon=False)
        add_code_line(state, line)
        return f"Your code has a name {word}, so this line is code. To hand in, type :submit."
    # A lone word close to submit or hint is probably a typo.
    meant = closest(line, ["submit", "hint"])
    if meant is not None and line.isidentifier() and not code_has_name(code, line):
        if is_filling(level.waves[number - 1], code):
            return f"Not filled in. Did you mean :{meant}?"
        add_code_line(state, line)
        return f"Added as code. Did you mean :{meant}? (:undo takes the line back)"
    return add_code_line(state, line)


def handle_line(state, line):
    """Run the line the player typed and return the text to show.

    - While the game waits for more (the rest of a block, the new text of
      :edit, the input of :run), the line goes there.
    - A line that starts with ":" is a command. It also ends anything the
      game was waiting for (":cancel" does only that).
    - Any other line is a line of code while the player is in code mode.
    - Otherwise it is a command, or Python for the quick console.
    A blank line outside code mode returns an empty string.
    """
    if state.pending is not None:
        if not line.startswith(":"):
            return continue_pending(state, line)
        state.pending = None
        if line.strip().lower() == ":cancel":
            return "Cancelled."
    if line.startswith(":"):
        return run_command(state, line[1:], colon=True)
    if state.coding:
        return code_mode_line(state, line)
    return run_command(state, line, colon=False)
