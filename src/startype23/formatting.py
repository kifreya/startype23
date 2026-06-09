"""Formatting utilities and column-visibility helpers."""

_SIZE_SUFFIXES = ["B", "KB", "MB", "GB", "TB"]

ColumnSet = set[str]

_COL_EXTENSION = "extension"
_COL_FILETYPE = "filetype"
_COL_COUNT = "count"
_COL_PERCENTAGE = "percentage"
_COL_DISTRIBUTION = "distribution"
_COL_SIZE = "size"
_COL_SIZE_PCT = "size_pct"

_ALL_COLUMNS: ColumnSet = {
    _COL_EXTENSION,
    _COL_FILETYPE,
    _COL_COUNT,
    _COL_PERCENTAGE,
    _COL_DISTRIBUTION,
}

_ALL_SIZE_COLUMNS: ColumnSet = {
    _COL_EXTENSION,
    _COL_FILETYPE,
    _COL_COUNT,
    _COL_SIZE,
    _COL_SIZE_PCT,
    _COL_DISTRIBUTION,
}


def _format_size(size_bytes: int) -> str:
    """Return a human-readable size string (e.g. ``"4.2 KB"``, ``"1.5 MB"``)."""
    if size_bytes == 0:
        return "0 B"
    magnitude = 0
    remaining = float(size_bytes)
    while remaining >= 1024 and magnitude < len(_SIZE_SUFFIXES) - 1:
        remaining /= 1024
        magnitude += 1
    if magnitude == 0:
        return f"{size_bytes} B"
    return f"{remaining:.1f} {_SIZE_SUFFIXES[magnitude]}"


def _format_count(n: int) -> str:
    """Format an integer with French spacing (space every 3 digits).

    ``1234567`` becomes ``"1 234 567"``.
    """
    if n < 0:
        return f"-{_format_count(-n)}"
    s = str(n)
    parts = []
    while len(s) > 3:
        parts.append(s[-3:])
        s = s[:-3]
    parts.append(s)
    return " ".join(reversed(parts))


def normalize_extension(ext: str) -> str:
    """Ensure an extension string has a leading dot, lowercased.

    Accepts ``".py"``, ``"py"``, ``".PY"``, ``"PY"``.
    Returns the lowercased form with a leading dot.
    """
    ext = ext.strip().lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return ext


def resolve_columns(visible: ColumnSet | None, all_available: ColumnSet) -> ColumnSet:
    """Return the effective set of columns to display.

    When *visible* is ``None`` or empty, all available columns are shown.
    Otherwise only the explicitly listed columns (plus Extension) are shown.
    """
    if visible is None or not visible:
        return all_available
    result: ColumnSet = {_COL_EXTENSION, *visible}
    return result & all_available
