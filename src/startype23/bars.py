"""Stacked proportion bar rendering."""

from collections.abc import Sequence

from rich.style import Style
from rich.text import Text

from .analyzer import FileTypeInfo


def render_stacked_bar(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 60,
    bar_height: int = 3,
    use_size: bool = False,
) -> Text:
    """Build a horizontal stacked bar made of coloured blocks.

    The bar is *bar_height* rows tall so it has enough visual weight.
    When *use_size* is True, segment widths are based on ``size_percentage``
    instead of ``percentage``.
    """
    if not infos:
        return Text("")

    num_segments = len(infos)
    separator_count = max(0, num_segments - 1)
    fill_width = bar_width - separator_count

    pct_key = "size_percentage" if use_size else "percentage"
    total_pct = sum(getattr(i, pct_key) for i in infos)

    segments: list[tuple[str, int]] = []
    allocated = 0
    for idx, info in enumerate(infos):
        width = max(1, round(getattr(info, pct_key) / total_pct * fill_width))
        if idx == num_segments - 1:
            width = fill_width - allocated
        segments.append((info.extension, width))
        allocated += width

    lines: list[Text] = []
    for _ in range(bar_height):
        line = Text()
        for seg_idx, (ext, width) in enumerate(segments):
            if seg_idx > 0:
                _ = line.append(" ")  # separator between segments
            hex_color = colors.get(ext, "#888888")
            _ = line.append("\u2593" * width, style=Style(color=hex_color))
        lines.append(line)

    combined = Text()
    for i, line in enumerate(lines):
        if i > 0:
            _ = combined.append("\n")
        _ = combined.append_text(line)
    return combined
