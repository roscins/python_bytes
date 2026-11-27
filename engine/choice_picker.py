"""Picking the answers of a choice wave with the arrow keys. No terminal here."""

from grader.answer_sheet import LETTERS, read_sheet, write_sheet
from render.highlight import highlight_lines
from render.panel import wrap_lines


class ChoicePicker:
    """The questions of a choice wave, and where the player is in them.

    Attributes:
        questions: the wave's questions.
        answers: {question number: letter} picked so far.
        question: the index of the question on screen.
        option: the index of the option the cursor is on.
    """

    footer = "↑↓ option  ←→ question  Enter pick  ^S submit  ^T hint  ^O map"

    help_lines = [
        "Up and Down move over the options. Enter picks one and goes on.",
        "Left and Right change question. Down from the last option goes to",
        "the buttons. Ctrl-S submits     Ctrl-T hint     Ctrl-O map",
    ]

    def __init__(self, wave, sheet):
        """Start on the first question, with the answers of the saved `sheet`."""
        self.questions = wave.questions
        self.answers, _ = read_sheet(sheet)
        self.show_question(0)

    def sheet(self):
        """Return the answers as the text that is saved and graded."""
        return write_sheet(self.answers)

    def show_question(self, index):
        """Go to question `index`, with the cursor on its picked option."""
        self.question = index
        letters = LETTERS[:len(self.questions[index]["options"])]
        picked = self.answers.get(index + 1, "a")
        self.option = max(0, letters.find(picked))

    def press(self, key):
        """Handle one key; return "buttons" if the cursor should leave for the buttons."""
        last_option = len(self.questions[self.question]["options"]) - 1
        if key == "up":
            self.option = max(0, self.option - 1)
        elif key == "down" and self.option < last_option:
            self.option = self.option + 1
        elif key == "down":
            return "buttons"
        elif key == "left" and self.question > 0:
            self.show_question(self.question - 1)
        elif key == "right" and self.question < len(self.questions) - 1:
            self.show_question(self.question + 1)
        elif key == "enter":
            self.answers[self.question + 1] = LETTERS[self.option]
            if self.question == len(self.questions) - 1:
                return "buttons"
            self.show_question(self.question + 1)
        return None

    def rows(self, width, focused=True):
        """Return (the lines to show, the index of the line with the cursor)."""
        question = self.questions[self.question]
        rows = [f"Question {self.question + 1} of {len(self.questions)} · "
                f"{len(self.answers)} answered"]
        rows.extend(wrap_lines([question["ask"]], width))
        for line in highlight_lines(question.get("code", "").strip(), True):
            rows.append("    " + line)
        cursor_row = 0
        for index, option in enumerate(question["options"]):
            pointer = " "
            if focused and index == self.option:
                pointer = ">"
                cursor_row = len(rows)
            picked = " "
            if self.answers.get(self.question + 1) == LETTERS[index]:
                picked = "x"
            text = f"{pointer} [{picked}] {LETTERS[index]}) {option}"
            rows.extend(wrap_lines([text], width))
        return rows, cursor_row
