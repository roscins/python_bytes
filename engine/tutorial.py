"""The tutorial: four short screens for a brand new player, before the map."""

from engine.screens import join_screens

SCREENS = [
    """TUTORIAL 1 of 4 · THE MAP
You start at the map. Type play 1-1 and press Enter to start the first level.
Stars show how well you did. A locked level opens when you clear the one before.
Type s and press Enter to skip this tutorial.""",
    """TUTORIAL 2 of 4 · TYPING CODE
A level has three waves. Type your code one line at a time and press Enter.
The game keeps every line. In a fill-in wave, type only what goes in the blank.""",
    """TUTORIAL 3 of 4 · CHECKING IT
Commands inside a wave start with a colon.
:run tries your code. It is free and nothing is graded.
:submit checks it. :undo takes back your last change.""",
    """TUTORIAL 4 of 4 · IF YOU ARE STUCK
:hint buys a hint with coins. You earn coins by passing a wave on the first try.
The combo counts first-try passes in a row. :help lists every command.
The line at the bottom always shows where you are and what you can type.""",
]


def tutorial_text():
    """Return the whole tutorial, one screen after the other."""
    return join_screens(SCREENS)
