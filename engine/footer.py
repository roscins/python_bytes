"""The footer: which mode you are in, and the few keys that matter there."""

from engine.fill import is_filling
from engine.progression_help import next_level_to_play

PENDING_FOOTERS = {
    "edit": "EDIT · type the new line · Enter alone keeps the old one · :cancel",
    "ins": "INSERT · type the new line · Enter alone adds nothing · :cancel",
    "repl": "BLOCK · an empty line runs it · :cancel",
    "run_input": "INPUT · an empty line starts the program · :cancel",
}


def footer_for(state):
    """Return the footer line for what the player is doing now."""
    if state.pending is not None:
        return PENDING_FOOTERS.get(state.pending["kind"], "")
    level = state.find_level(state.current_level)
    if not state.coding or level is None:
        slot = next_level_to_play(state)
        play = ""
        if slot is not None:
            play = f" · play {slot.id}"
        return f"MAP{play} · stats · help · quit"
    wave = level.waves[state.current_wave - 1]
    if level.boss:
        return "BOSS · :run is free · :submit uses a try · :show code · :help"
    if wave.mode == "predict":
        return "ANSWER · one printed line per Enter · :submit check · :hint · :help"
    if wave.mode == "review":
        return "REVIEW · line: letter, for example 4: a · :submit check · :hint · :help"
    if wave.is_quiz():
        return "ANSWER · number: letter, for example 1: a · :submit check · :hint · :help"
    if is_filling(wave, state.wave_text(level, state.current_wave)):
        return "FILL · type what goes in the blank · :submit check · :hint · :help"
    return "CODE · Enter = new line · :submit check · :hint · :help"
