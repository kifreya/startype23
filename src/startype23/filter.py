"""Filtering helpers for the --filter flag."""

import re
from collections.abc import Sequence

from .analyzer import FileTypeInfo


def filter_infos(
    infos: Sequence[FileTypeInfo],
    filter_str: str,
) -> list[FileTypeInfo]:
    """Return only entries whose extension matches one of the types in *filter_str*.

    *filter_str* may contain extensions separated by comma, period, colon,
    semicolon, or newline.  A leading dot is optional.
    """
    parts = re.split(r"[,.:;\n]+", filter_str)
    wanted: set[str] = set()
    for p in parts:
        p = p.strip().lower()
        if not p:
            continue
        if not p.startswith("."):
            p = f".{p}"
        wanted.add(p)

    return [info for info in infos if info.extension.lower() in wanted]
