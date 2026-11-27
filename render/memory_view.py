"""Draw names and the values they point to, for the memory power-up.

    MEMORY
    NAMES          VALUES
    power  -------> [ 9 ]  int
    name   --+----> [ 'Snek' ]  str
    twin   --+

Names of the very same object share one box. The same drawing shows
aliasing of lists later in the game.
"""

WIDTH = 74              # the room inside a panel
MAX_NAME_WIDTH = 24
MAX_VARIABLES = 30

# Python may reuse one object for equal values of these kinds.
SMALL_INT_RANGE = range(-5, 257)
SHORT_STRING_LENGTH = 20
REUSE_NOTE = "Python reuses them as an optimisation; compare with ==, never rely on `is`."


def cut(text, width):
    """Return `text`, shortened with "..." if it is longer than `width`."""
    if len(text) <= width:
        return text
    return text[:width - 3] + "..."


def group_by_object(variables):
    """Return lists of variables, one list per object, in the order the names were made."""
    groups = {}
    for variable in variables:
        groups.setdefault(variable["id"], []).append(variable)
    return list(groups.values())


def is_reused_value(variable):
    """Return True for a small int or a short string, which Python may share by itself."""
    if variable["type"] == "int":
        return len(variable["repr"]) < 5 and int(variable["repr"]) in SMALL_INT_RANGE
    if variable["type"] == "str":
        return variable["text"] is not None and len(variable["text"]) <= SHORT_STRING_LENGTH
    return False


def group_lines(group, name_width):
    """Return the lines for one box and every name that points to it."""
    first = group[0]
    joint = "-"
    if len(group) > 1:
        joint = "+"
    start = f"{cut(first['name'], name_width):<{name_width}} --{joint}----> [ "
    end = f" ]  {first['type']}"
    value = cut(first["repr"], max(10, WIDTH - len(start) - len(end)))
    lines = [start + value + end]
    for variable in group[1:]:
        lines.append(f"{cut(variable['name'], name_width):<{name_width}} --+")
    return lines


def memory_view(variables):
    """Return the drawing for a list of variable descriptions (see runner/repl_worker.py)."""
    if not variables:
        return "MEMORY\nNo variables yet. Make one, for example: power = 5"
    shown = variables[:MAX_VARIABLES]
    name_width = len("NAMES")
    for variable in shown:
        name_width = max(name_width, min(len(variable["name"]), MAX_NAME_WIDTH))
    lines = ["MEMORY", f"{'NAMES':<{name_width}}          VALUES"]
    note_needed = False
    for group in group_by_object(shown):
        lines.extend(group_lines(group, name_width))
        if len(group) > 1 and is_reused_value(group[0]):
            note_needed = True
    if len(variables) > len(shown):
        lines.append(f"... and {len(variables) - len(shown)} more names")
    if note_needed:
        lines.append(REUSE_NOTE)
    return "\n".join(lines)
