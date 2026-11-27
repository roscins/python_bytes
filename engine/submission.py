"""Grade the code the player typed for a wave.

This is what :submit does before it shows the results. It joins the game
(where the code is) and the grader (which checks it).
"""

from grader.wave_grader import grade_wave


class WaveSubmission:
    """One wave of a submitted level.

    Attributes:
        number: the wave's number, counting from 1.
        wave: the Wave from the level pack.
        file_name: a name for the wave's code ("your code").
        result: the WaveResult, or None if the code is empty
            (the player has not started this wave yet).
    """

    def __init__(self, number, wave, file_name, result, code=""):
        """Remember the wave, its file, its result and the code that was graded."""
        self.code = code
        self.number = number
        self.wave = wave
        self.file_name = file_name
        self.result = result


def grade_text(wave, number, text):
    """Grade the code typed for one wave and return a WaveSubmission.

    Code that is empty or only blank lines is not graded: the result is None.
    """
    result = None
    if text is not None and text.strip() != "":
        result = grade_wave(wave, text)
    return WaveSubmission(number, wave, "your code", result, text or "")
