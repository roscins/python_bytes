"""Showing the data files of a wave, and what a program wrote to files."""

# How many lines of a written file are shown after Run.
WRITTEN_LINES_SHOWN = 20


def files_line(wave, keys):
    """Return the line that names a wave's data files and says how to read them, or ""."""
    if not wave.files:
        return ""
    command = ":show"
    if keys:
        command = "Ctrl-E, then show"
    return f"Files: {', '.join(wave.files)}  (read one: {command} {next(iter(wave.files))})"


def file_text(name, text):
    """Return a data file with its name and line numbers."""
    lines = [f"FILE {name}"]
    for number, line in enumerate(text.splitlines(), start=1):
        lines.append(f"{number:>4} | {line}")
    return "\n".join(lines)


def written_lines(written):
    """Return the lines that show the files a program wrote."""
    lines = []
    for name, text in written.items():
        lines.append(f"WROTE {name}")
        content = text.splitlines()
        for line in content[:WRITTEN_LINES_SHOWN]:
            lines.append(f"    {line}")
        if len(content) > WRITTEN_LINES_SHOWN:
            lines.append(f"    ... {len(content) - WRITTEN_LINES_SHOWN} more lines")
    return lines
