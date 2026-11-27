"""Suggest the command a mistyped word was meant to be."""

import difflib

MAP_WORDS = ["help", "map", "stats", "play", "submit", "hint", "where", "quit"]
CODE_WORDS = ["submit", "hint", "show", "undo", "clear", "edit", "ins", "del", "wave", "run",
              "cancel", "help", "map", "stats", "quit", "play", "where"]
CLOSENESS = 0.7


def closest(word, words):
    """Return the word of `words` that `word` was most likely meant to be, or None."""
    matches = difflib.get_close_matches(word.lower(), words, n=1, cutoff=CLOSENESS)
    if matches:
        return matches[0]
    return None


def did_you_mean(word, words, colon):
    """Return " Did you mean :submit?" for a typo, or "" if nothing is close."""
    found = closest(word, words)
    if found is None:
        return ""
    prefix = ":" if colon else ""
    return f" Did you mean {prefix}{found}?"
