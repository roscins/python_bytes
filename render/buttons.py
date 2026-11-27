"""Draw buttons and menu lines. The chosen one is shown in reverse video."""

CHOSEN = "\x1b[7m"
NORMAL = "\x1b[27m"


def button_row(labels, chosen=None):
    """Return "[Play] [Stats]" with button number `chosen` highlighted (None: none)."""
    buttons = []
    for index in range(len(labels)):
        button = f"[{labels[index]}]"
        if index == chosen:
            button = CHOSEN + button + NORMAL
        buttons.append(button)
    return " " + "  ".join(buttons)


def menu_lines(labels, chosen):
    """Return one line for each menu entry, with an arrow and a highlight on the chosen one."""
    lines = []
    for index in range(len(labels)):
        if index == chosen:
            lines.append(f"> {CHOSEN} {labels[index]} {NORMAL}")
        else:
            lines.append(f"   {labels[index]}")
    return lines
