"""Which button or menu line is chosen. No terminal here: keys come in as names."""


class Choice:
    """A row of buttons or a menu, with one of them chosen.

    Attributes:
        labels: the texts to choose from.
        index: which one is chosen.
    """

    def __init__(self, labels, index=0, back="left", forward="right"):
        """Choose `labels[index]`; `back` and `forward` are the keys that move."""
        self.labels = list(labels)
        self.index = index
        self.back = back
        self.forward = forward

    def move(self, key):
        """Move the choice if `key` is one of the moving keys; stop at the ends."""
        if key == self.back and self.index > 0:
            self.index = self.index - 1
        if key == self.forward and self.index < len(self.labels) - 1:
            self.index = self.index + 1

    def label(self):
        """Return the chosen text."""
        return self.labels[self.index]
