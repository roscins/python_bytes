"""One thing at a time: an answer can hold several screens, shown one by one.

A command puts PAGE_BREAK between screens. After each screen but the last,
the player presses Enter. "s" skips to the last screen. Any other line also
skips there and is then handled as typed, so nothing the player types is lost.
"""

import textwrap

PAGE_BREAK = "\f"
CONTINUE_PROMPT = "Enter to continue (s skips) > "
SKIP_WORDS = ["s", "skip"]


def join_screens(screens):
    """Return several screens as one answer."""
    return PAGE_BREAK.join(screens)


def split_screens(text):
    """Return the screens of an answer, without blank lines around each."""
    return [screen.strip("\n") for screen in text.split(PAGE_BREAK)]


def looks_laid_out(line):
    """Return True for code, tables and drawings, whose spaces must stay as they are."""
    if "   " in line.strip() or line.lstrip()[:1] in ["|", "+"] or "\x1b" in line:
        return True
    # An indented line is code, unless it ends like a sentence.
    return line.startswith("    ") and not line.rstrip().endswith((".", "?"))


def wrap_text(text, width):
    """Return `text` with long sentences wrapped to `width`; code and tables are left alone."""
    result = []
    for line in text.split("\n"):
        if len(line) <= width or looks_laid_out(line):
            result.append(line)
            continue
        indent = " " * (len(line) - len(line.lstrip()))
        if line.lstrip().startswith("• "):
            indent = indent + "  "
        result.extend(textwrap.wrap(line, width=width, subsequent_indent=indent))
    return "\n".join(result)
