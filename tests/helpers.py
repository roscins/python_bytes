"""Small helpers shared by several test files."""

import os
import tempfile


def write_temporary_file(test, text, suffix=".txt"):
    """Write `text` to a temporary file, delete it after `test`, return its path."""
    handle, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(handle, "w", encoding="utf-8") as temporary_file:
        temporary_file.write(text)
    test.addCleanup(os.remove, path)
    return path
