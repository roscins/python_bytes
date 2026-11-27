"""The text being edited: lines, a cursor, blanks and undo. No terminal here.

Keys come in as names (see engine/keys.py). Rows and columns count from 0.
In a fill-in wave the blank ___ is one thing: typing on it replaces all of
it, and Backspace or Delete removes all of it.
"""

BLANK = "___"
TAB = "    "

# How many earlier versions Ctrl-Z can go back to.
UNDO_LIMIT = 100

MOVE_KEYS = ["left", "right", "up", "down", "home", "end"]


class Editor:
    """Lines of text with a cursor.

    Attributes:
        lines: the text, one string per line; there is always at least one.
        row, column: where the cursor is.
        blanks: True if ___ is a blank to be filled in.
        undo_stack: earlier (lines, row, column), newest last.
        undo_row: the row the last undo step belongs to, or None to start a new step.
    """

    def __init__(self, text="", blanks=False):
        """Start with `text` and the cursor at its beginning."""
        self.lines = text.splitlines() or [""]
        self.row = 0
        self.column = 0
        self.blanks = blanks
        self.undo_stack = []
        self.undo_row = None

    def text(self):
        """Return the text as it is saved: every line ends with a newline."""
        if self.lines == [""]:
            return ""
        return "\n".join(self.lines) + "\n"

    # ---- where to start

    def go_to_first_blank(self):
        """Put the cursor on the first blank; return False if there is none."""
        for row in range(len(self.lines)):
            if BLANK in self.lines[row]:
                self.row = row
                self.column = self.lines[row].index(BLANK)
                return True
        return False

    def go_to_end(self):
        """Put the cursor after the last character."""
        self.row = len(self.lines) - 1
        self.column = len(self.lines[self.row])

    def go_to_new_last_line(self):
        """Put the cursor on an empty line after the text, adding one if needed."""
        if self.lines[-1] != "":
            self.lines.append("")
        self.go_to_end()

    def on_last_line(self):
        """Return True if the cursor is on the last line."""
        return self.row == len(self.lines) - 1

    # ---- moving

    def move(self, key):
        """Move the cursor for an arrow, Home or End."""
        # After moving, the next change is a new undo step.
        self.undo_row = None
        if key == "up" and self.row > 0:
            self.row = self.row - 1
        elif key == "down" and not self.on_last_line():
            self.row = self.row + 1
        elif key == "home":
            self.column = 0
        elif key == "end":
            self.column = len(self.lines[self.row])
        elif key == "left" and self.column > 0:
            self.column = self.column - 1
        elif key == "left" and self.row > 0:
            self.row = self.row - 1
            self.column = len(self.lines[self.row])
        elif key == "right" and self.column < len(self.lines[self.row]):
            self.column = self.column + 1
        elif key == "right" and not self.on_last_line():
            self.row = self.row + 1
            self.column = 0
        self.column = min(self.column, len(self.lines[self.row]))

    # ---- changing

    def remember(self, alone=False):
        """Keep the text for undo, once for each line worked on; `alone` always makes a step."""
        if alone or self.undo_row != self.row:
            self.undo_stack.append((list(self.lines), self.row, self.column))
            del self.undo_stack[:-UNDO_LIMIT]
        self.undo_row = None if alone else self.row

    def undo(self):
        """Go back one step; return False if there is nothing to undo."""
        if not self.undo_stack:
            return False
        lines, self.row, self.column = self.undo_stack.pop()
        self.lines = list(lines)
        self.undo_row = None
        return True

    def blank_at(self, column):
        """Return where the blank covering `column` of this line starts, or None."""
        if not self.blanks:
            return None
        line = self.lines[self.row]
        start = line.find(BLANK)
        while start != -1:
            if start <= column < start + len(BLANK):
                return start
            start = line.find(BLANK, start + len(BLANK))
        return None

    def replace(self, start, end, new_text):
        """Replace characters `start` to `end` of this line and put the cursor after the new text."""
        line = self.lines[self.row]
        self.lines[self.row] = line[:start] + new_text + line[end:]
        self.column = start + len(new_text)

    def insert(self, new_text):
        """Type `new_text` (one character, or the spaces of a Tab) at the cursor."""
        self.remember()
        start = self.blank_at(self.column)
        if start is None:
            self.replace(self.column, self.column, new_text)
        else:
            self.replace(start, start + len(BLANK), new_text)

    def enter(self):
        """Split the line at the cursor."""
        self.remember(alone=True)
        line = self.lines[self.row]
        self.lines[self.row] = line[:self.column]
        self.lines.insert(self.row + 1, line[self.column:])
        self.row = self.row + 1
        self.column = 0

    def join_with_next(self):
        """Put the next line at the end of this one."""
        self.lines[self.row] = self.lines[self.row] + self.lines.pop(self.row + 1)

    def backspace(self):
        """Delete what is before the cursor; at the start of a line, join it to the one above."""
        start = self.blank_at(self.column)
        if start is None and self.column > 0:
            start = self.blank_at(self.column - 1)
        if start is not None:
            self.remember(alone=True)
            self.replace(start, start + len(BLANK), "")
        elif self.column > 0:
            self.remember()
            self.replace(self.column - 1, self.column, "")
        elif self.row > 0:
            self.remember(alone=True)
            self.row = self.row - 1
            self.column = len(self.lines[self.row])
            self.join_with_next()

    def delete(self):
        """Delete what is at the cursor; at the end of a line, join the next one to it."""
        start = self.blank_at(self.column)
        if start is not None:
            self.remember(alone=True)
            self.replace(start, start + len(BLANK), "")
        elif self.column < len(self.lines[self.row]):
            self.remember()
            self.replace(self.column, self.column + 1, "")
        elif not self.on_last_line():
            self.remember(alone=True)
            self.join_with_next()

    def press(self, key):
        """Handle one editing key; return True if the key was one."""
        if key in MOVE_KEYS:
            self.move(key)
        elif key == "enter":
            self.enter()
        elif key == "tab":
            self.insert(TAB)
        elif key == "backspace":
            self.backspace()
        elif key == "delete":
            self.delete()
        elif len(key) == 1:
            self.insert(key)
        else:
            return False
        return True
