"""Grade waves: the code typed in the game, or (older way) the files in the workspace.

This is what submit does before it shows the results. It joins the
workspace (where the files are) and the grader (which checks them).
"""

from engine.workspace import read_wave_file, wave_file_name
from grader.wave_grader import grade_wave


class WaveSubmission:
    """One wave of a submitted level.

    Attributes:
        number: the wave's number, counting from 1.
        wave: the Wave from the level pack.
        file_name: the name of the wave's file, for example "wave1.py".
        result: the WaveResult, or None if the file is missing or empty
            (the player has not started this wave yet).
    """

    def __init__(self, number, wave, file_name, result):
        """Remember the wave, its file and its result."""
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
    return WaveSubmission(number, wave, "your code", result)


def grade_submission(level, root, wave_numbers=None):
    """Grade the wave files of `level` in the workspace `root`.

    Returns a list of WaveSubmission, one per wave in `wave_numbers` (all
    waves if it is None). A file that is missing or holds only blank lines
    is not graded: its result is None.
    """
    submissions = []
    number = 0
    for wave in level.waves:
        number = number + 1
        if wave_numbers is not None and number not in wave_numbers:
            continue
        text = read_wave_file(level, number, root)
        result = None
        if text is not None and text.strip() != "":
            result = grade_wave(wave, text)
        submissions.append(WaveSubmission(number, wave, wave_file_name(wave, number), result))
    return submissions
