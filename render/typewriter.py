"""Text that types itself out, and a way to play frames that the player can skip.

typewriter_frames() makes the frames (the text so far); play_frames() shows
them one after the other. The time between frames (`sleep`) and the "was
Enter pressed" check (`skipped`) are given by the caller, so the tests
need no clock and no keyboard.
"""

# After one of these the typing stops for a moment, like a person reading aloud.
PAUSE_AFTER = ".!?"
PAUSE_FRAMES = 3


def typewriter_frames(text, step=3):
    """Return the frames of `text` being typed: every frame has `step` more letters.

    After a full stop, question mark or exclamation mark, the same frame is
    repeated a few times, which makes the typing pause there. The last
    frame is the whole text.
    """
    if text == "":
        return [""]
    frames = []
    shown = step
    while shown < len(text):
        frames.append(text[:shown])
        if text[shown - 1] in PAUSE_AFTER:
            for _ in range(PAUSE_FRAMES - 1):
                frames.append(text[:shown])
        shown = shown + step
    frames.append(text)
    return frames


def play_frames(frames, show, sleep, skipped, delay):
    """Show the frames one after the other; return True if the player skipped to the end.

    `show(frame)` draws a frame. `sleep(delay)` waits between frames, and
    `skipped()` says if the player pressed Enter: then the last frame is
    shown at once. With a delay of 0 there is no waiting and no skipping:
    all the frames are shown straight away (the plain mode).
    """
    for index in range(len(frames)):
        if index > 0 and delay:
            if skipped():
                show(frames[-1])
                return True
            sleep(delay)
        show(frames[index])
    return False
