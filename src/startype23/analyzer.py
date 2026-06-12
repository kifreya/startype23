"""Directory traversal and file extension aggregation."""

import os
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

__all__ = ["FileTypeInfo", "scan_directory", "DEFAULT_EXCLUDE_DIRS"]

# Default directory names to skip during traversal.
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "node_modules",
        ".idea",
        ".vscode",
        ".DS_Store",
    }
)


@dataclass(slots=True)
class FileTypeInfo:
    """Aggregated statistics for a single file extension."""

    extension: str
    count: int
    total_size: int = 0
    percentage: float = 0.0
    size_percentage: float = 0.0


def scan_directory(
    path: str = ".",
    exclude_dirs: set[str] | None = None,
    include_hidden: bool = False,
    progress_callback: Callable[[int], None] | None = None,
) -> list[FileTypeInfo]:
    """Walk *path* and aggregate file counts by extension.

    Parameters
    ----------
    path : str
        Root directory to scan (defaults to current working directory).
    exclude_dirs : set[str] or None
        Directory names to skip.  When ``None``, the built-in
        ``DEFAULT_EXCLUDE_DIRS`` set is used.
    include_hidden : bool
        If ``False``, files whose name starts with ``"."`` and directories
        that have a leading dot are ignored.

    Returns
    -------
    list[FileTypeInfo]
        Sorted list (descending by count) of extension statistics.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    counter: Counter[str] = Counter()
    size_map: dict[str, int] = defaultdict(int)

    for dirpath_str, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath_str)

        # Filter out directories we should skip -- in-place for os.walk.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in exclude_dirs and (include_hidden or not d.startswith("."))
        ]

        for filename in filenames:
            if not include_hidden and filename.startswith("."):
                continue

            ext = _extract_extension(filename)
            counter[ext] += 1

            try:
                size_map[ext] += (dirpath / filename).stat().st_size
            except OSError:
                pass

        if progress_callback is not None:
            progress_callback(sum(counter.values()))

    total_files = sum(counter.values())
    total_size_all = sum(size_map.values())

    if total_files == 0:
        return []

    results: list[FileTypeInfo] = []
    for ext, count in counter.most_common():
        sz = size_map[ext]
        results.append(
            FileTypeInfo(
                extension=ext,
                count=count,
                total_size=sz,
                percentage=round((count / total_files) * 100, 2),
                size_percentage=round((sz / total_size_all) * 100, 2)
                if total_size_all
                else 0.0,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_extension(filename: str) -> str:
    """Return the lowercase file extension including the leading dot.

    Files without an extension are grouped under the label ``"[no extension]"``.
    Files consisting solely of an extension (e.g. ``".gitignore"``) are treated
    as having no extension.
    """
    name, dot, ext = filename.rpartition(".")
    if dot and name:
        return f".{ext.lower()}"
    return "[no extension]"
