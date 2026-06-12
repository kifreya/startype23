"""Table rendering for count, size, and explain views."""

from collections.abc import Sequence

from rich import box as rich_box
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .analyzer import FileTypeInfo
from .extensions import EXTENSION_INFO
from .formatting import (
    _ALL_COLUMNS,
    _ALL_SIZE_COLUMNS,
    _COL_COUNT,
    _COL_DISTRIBUTION,
    _COL_FILETYPE,
    _COL_PERCENTAGE,
    _COL_SIZE,
    _COL_SIZE_PCT,
    ColumnSet,
    _format_count,
    _format_size,
    normalize_extension,
    resolve_columns,
)

__all__ = [
    "render_table",
    "render_size_table",
    "render_legend",
    "render_explain_table",
]


def _make_mini_bar(fill: int, hex_color: str) -> Text:
    """Build a short coloured block bar for table cells."""
    return Text("\u2593" * (fill // 2), style=Style(color=hex_color))


# Mapping of column-id -> (header_label, value_getter, justify, key)
# value_getter receives (info, ftype) and returns a renderable string.
_CT_COLS = {
    _COL_FILETYPE: ("File Type", lambda info, ftype: ftype, None, False),
    _COL_COUNT: ("Count", lambda info, _: _format_count(info.count), "right", False),
    _COL_PERCENTAGE: (
        "Percentage",
        lambda info, _: f"{info.percentage:.2f}%",
        "right",
        False,
    ),
    _COL_DISTRIBUTION: ("Distribution", lambda info, _: ..., "left", True),
}

_SZ_COLS = {
    _COL_FILETYPE: ("File Type", lambda info, ftype: ftype, None, False),
    _COL_COUNT: ("Count", lambda info, _: _format_count(info.count), "right", False),
    _COL_SIZE: (
        "Total Size",
        lambda info, _: _format_size(info.total_size),
        "right",
        False,
    ),
    _COL_SIZE_PCT: (
        "Size %",
        lambda info, _: f"{info.size_percentage:.2f}%",
        "right",
        False,
    ),
    _COL_DISTRIBUTION: ("Distribution", lambda info, _: ..., "left", True),
}


def _build_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int,
    columns: ColumnSet | None,
    all_available: ColumnSet,
    col_specs: dict,
    title: str,
    borderless: bool,
    bar_attr: str = "count",
) -> Table:
    """Shared table builder used by both count and size renderers.

    ``col_specs`` maps column-ids to ``(header_label, value_fn, justify, is_bar)``
    tuples.  ``is_bar`` signals that the column renders a mini distribution bar,
    which requires special fill-width logic.

    ``bar_attr`` is the ``FileTypeInfo`` attribute name used for bar sizing,
    either ``"count"`` or ``"total_size"``.
    """
    show_cols = resolve_columns(columns, all_available)

    table = Table(
        title=title,
        title_style="bold",
        expand=False,
        padding=(0, 1),
        show_header=True,
        header_style="bold",
        show_edge=not borderless,
        box=rich_box.SIMPLE if borderless else None,
    )

    table.add_column("Extension", style="bold", no_wrap=True)

    visible_specs = [(cid, col_specs[cid]) for cid in col_specs if cid in show_cols]
    for cid, (label, _value_fn, justify, _is_bar) in visible_specs:
        kw = {}
        if justify:
            kw["justify"] = justify
        if cid == _COL_DISTRIBUTION:
            kw["min_width"] = bar_width + 2
        table.add_column(label, no_wrap=True, **kw)

    max_val = max(getattr(i, bar_attr) for i in infos) or 1

    lookup_cache = {}  # extension -> filetype string

    for info in infos:
        ext = info.extension
        if ext not in lookup_cache:
            lookup_cache[ext] = EXTENSION_INFO.get(ext, ("Unknown", ""))[0]
        ftype = lookup_cache[ext]

        row = [ext]
        for cid, (_label, value_fn, _justify, is_bar) in visible_specs:
            if is_bar:
                fill = round(getattr(info, bar_attr) / max_val * bar_width)
                row.append(_make_mini_bar(max(1, fill), colors.get(ext, "#888888")))
            else:
                row.append(value_fn(info, ftype))

        table.add_row(*row)

    return table


def render_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
    borderless: bool = False,
) -> Table:
    """Create a rich ``Table`` with per-extension details and a mini bar (by count)."""
    return _build_table(
        infos,
        colors,
        bar_width,
        columns,
        _ALL_COLUMNS,
        _CT_COLS,
        "File Type Distribution (by Count)",
        borderless,
        bar_attr="count",
    )


def render_size_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
    borderless: bool = False,
) -> Table:
    """Create a rich ``Table`` showing size distribution per extension."""
    return _build_table(
        infos,
        colors,
        bar_width,
        columns,
        _ALL_SIZE_COLUMNS,
        _SZ_COLS,
        "File Type Distribution (by Size)",
        borderless,
        bar_attr="total_size",
    )


def render_legend(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
) -> Text:
    """Build a compact colour legend."""
    legend = Text()
    for info in infos:
        hex_color = colors.get(info.extension, "#888888")
        _ = legend.append("  ")
        _ = legend.append(" ", style=Style(bgcolor=hex_color))
        _ = legend.append(f" {info.extension} ", style="dim")
    return legend


def render_explain_table(
    extension: str,
    *,
    console: Console | None = None,
) -> None:
    """Look up a single extension and display its file type and description."""
    if console is None:
        console = Console()

    ext = normalize_extension(extension)
    entry = EXTENSION_INFO.get(ext)

    if entry is None:
        console.print(
            f"[bold yellow]No information found for extension '{ext}'.[/bold yellow]"
        )
        return

    ftype, desc = entry

    table = Table(
        title=f"Extension: {ext}",
        title_style="bold",
        expand=False,
        padding=(0, 1),
        show_header=True,
        header_style="bold",
        show_edge=False,
    )
    table.add_column("Extension", style="bold", no_wrap=True)
    table.add_column("File Type", no_wrap=True)
    table.add_column("Description", ratio=1)

    table.add_row(ext, ftype, desc)

    console.print(table)
