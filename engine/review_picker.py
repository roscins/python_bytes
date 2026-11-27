"""Marking the faulty lines of a review wave with the arrow keys. No terminal here."""

from grader.answer_sheet import LETTERS, read_comments, read_sheet, write_sheet
from render.highlight import highlight_lines

# The longest comment, so that it fits on one row of the screen.
MAX_COMMENT = 56


class ReviewPicker:
    """The code of a review wave, the marked lines and the cursor.

    Attributes:
        lines: the code to review, one string per line.
        categories: what a fault can be called.
        limit: how many lines may be marked (the number of faults).
        marks: {line number: category letter}.
        row: the index of the line the cursor is on.
        choosing: True while the list of categories is open.
        option: the index of the category the cursor is on.
        notice: why the last key did nothing, or "".
        comments: {line number: the player's comment}.
        typing: True while the player types a comment (choosing is then True too).
    """

    footer = "↑↓ line  Space mark  Enter pick  ^S submit  ^T hint  ^O map"

    help_lines = [
        "Up and Down move over the code. Space marks a line and opens the",
        "categories; Enter picks one, Esc closes. Space on a marked line",
        "removes the mark. Ctrl-S submits     Ctrl-T hint     Ctrl-O map",
    ]

    def __init__(self, wave, sheet):
        """Start on the first line, with the marks of the saved `sheet`."""
        self.lines = wave.code_lines()
        self.categories = wave.categories
        self.limit = len(wave.faults)
        self.marks, _ = read_sheet(sheet)
        self.row = 0
        self.choosing = False
        self.option = 0
        self.notice = ""
        self.takes_comments = wave.takes_comments()
        self.comments = read_comments(sheet)
        self.typing = False
        if self.takes_comments:
            self.help_lines = self.help_lines + [
                "After the category you may type a comment; Enter or Esc ends it."]

    def sheet(self):
        """Return the marks as the text that is saved and graded."""
        return write_sheet(self.marks, self.comments)

    def press(self, key):
        """Handle one key; return "buttons" if the cursor should leave for the buttons."""
        self.notice = ""
        if self.typing:
            self.press_in_comment(key)
        elif self.choosing:
            self.press_in_categories(key)
        elif key == "up":
            self.row = max(0, self.row - 1)
        elif key == "down" and self.row < len(self.lines) - 1:
            self.row = self.row + 1
        elif key == "down":
            return "buttons"
        elif key == " ":
            self.toggle_mark()
        return None

    def toggle_mark(self):
        """Remove this line's mark, or open the categories to make one."""
        number = self.row + 1
        if number in self.marks:
            del self.marks[number]
            self.comments.pop(number, None)
        elif len(self.marks) >= self.limit:
            self.notice = f"Only {self.limit} can be marked. Space on a marked line frees one."
        else:
            self.choosing = True
            self.option = 0

    def press_in_categories(self, key):
        """Move in the list of categories, pick one, or close the list."""
        if key == "up":
            self.option = max(0, self.option - 1)
        elif key == "down":
            self.option = min(len(self.categories) - 1, self.option + 1)
        elif key == "enter":
            self.marks[self.row + 1] = LETTERS[self.option]
            if self.takes_comments:
                self.typing = True
            else:
                self.choosing = False
        elif key == "escape":
            self.choosing = False

    def press_in_comment(self, key):
        """Type the comment of the marked line; Enter or Esc ends it."""
        number = self.row + 1
        comment = self.comments.get(number, "")
        if key in ("enter", "escape"):
            self.typing = False
            self.choosing = False
        elif key == "backspace":
            self.comments[number] = comment[:-1]
        elif len(key) == 1 and len(comment) < MAX_COMMENT:
            self.comments[number] = comment + key

    def rows(self, width, focused=True):
        """Return (the lines to show, the index of the line with the cursor).

        The categories open right under the line being marked.
        """
        heading = f"Faults to find: {self.limit} · marked: {len(self.marks)}"
        if self.typing:
            heading = "Your comment (optional): Enter ends it"
        rows = [self.notice or heading]
        cursor_row = 0
        for index, line in enumerate(highlight_lines("\n".join(self.lines), True)):
            pointer = " "
            if focused and index == self.row:
                pointer = ">"
                cursor_row = len(rows)
            mark = "   "
            if index + 1 in self.marks:
                mark = f"[{self.marks[index + 1]}]"
            rows.append(f"{pointer}{mark} {index + 1:>2} │ {line}")
            if self.typing and index == self.row:
                cursor_row = len(rows)
                rows.append(f"        # {self.comments.get(index + 1, '')}_")
            elif self.choosing and index == self.row:
                for number, category in enumerate(self.categories):
                    chosen = " "
                    if number == self.option:
                        chosen = ">"
                        cursor_row = len(rows)
                    rows.append(f"          {chosen} {LETTERS[number]}) {category}")
        return rows, cursor_row
