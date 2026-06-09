"""Table rendering for count, size, and explain views."""

from collections.abc import Sequence

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
    _COL_EXTENSION,
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


def _make_mini_bar(fill: int, hex_color: str) -> Text:
    """Build a short coloured block bar for table cells."""
    bar = Text()
    num_blocks = fill // 2
    _ = bar.append("\u2593" * num_blocks, style=Style(color=hex_color))
    return bar


def render_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
) -> Table:
    """Create a rich ``Table`` with per-extension details and a mini bar (by count)."""
    show_cols = resolve_columns(columns, _ALL_COLUMNS)

    table = Table(
        title="File Type Distribution (by Count)",
        title_style="bold",
        expand=False,
        padding=(0, 1),
        show_header=True,
        header_style="bold",
    )

    table.add_column("Extension", style="bold", no_wrap=True)
    if _COL_FILETYPE in show_cols:
        table.add_column("File Type", no_wrap=True)
    if _COL_COUNT in show_cols:
        table.add_column("Count", justify="right")
    if _COL_PERCENTAGE in show_cols:
        table.add_column("Percentage", justify="right")
    if _COL_DISTRIBUTION in show_cols:
        table.add_column("Distribution", justify="left", min_width=bar_width + 2)

    max_count = max(i.count for i in infos) if infos else 1

    for info in infos:
        hex_color = colors.get(info.extension, "#888888")
        bar_fill = round(info.count / max_count * bar_width) if max_count else 0
        bar_fill = max(1, bar_fill)

        ftype, _desc = EXTENSION_INFO.get(info.extension, ("Unknown", ""))

        row = [info.extension]
        if _COL_FILETYPE in show_cols:
            row.append(ftype)
        if _COL_COUNT in show_cols:
            row.append(_format_count(info.count))
        if _COL_PERCENTAGE in show_cols:
            row.append(f"{info.percentage:.2f}%")
        if _COL_DISTRIBUTION in show_cols:
            row.append(_make_mini_bar(bar_fill, hex_color))

        table.add_row(*row)

    return table


def render_size_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
) -> Table:
    """Create a rich ``Table`` showing size distribution per extension."""
    show_cols = resolve_columns(columns, _ALL_SIZE_COLUMNS)

    table = Table(
        title="File Type Distribution (by Size)",
        title_style="bold",
        expand=False,
        padding=(0, 1),
        show_header=True,
        header_style="bold",
    )

    table.add_column("Extension", style="bold", no_wrap=True)
    if _COL_FILETYPE in show_cols:
        table.add_column("File Type", no_wrap=True)
    if _COL_COUNT in show_cols:
        table.add_column("Count", justify="right")
    if _COL_SIZE in show_cols:
        table.add_column("Total Size", justify="right")
    if _COL_SIZE_PCT in show_cols:
        table.add_column("Size %", justify="right")
    if _COL_DISTRIBUTION in show_cols:
        table.add_column("Distribution", justify="left", min_width=bar_width + 2)

    max_size = max(i.total_size for i in infos) if infos else 1

    for info in infos:
        hex_color = colors.get(info.extension, "#888888")
        bar_fill = round(info.total_size / max_size * bar_width) if max_size else 0
        bar_fill = max(1, bar_fill)

        ftype, _desc = EXTENSION_INFO.get(info.extension, ("Unknown", ""))

        row = [info.extension]
        if _COL_FILETYPE in show_cols:
            row.append(ftype)
        if _COL_COUNT in show_cols:
            row.append(_format_count(info.count))
        if _COL_SIZE in show_cols:
            row.append(_format_size(info.total_size))
        if _COL_SIZE_PCT in show_cols:
            row.append(f"{info.size_percentage:.2f}%")
        if _COL_DISTRIBUTION in show_cols:
            row.append(_make_mini_bar(bar_fill, hex_color))

        table.add_row(*row)

    return table


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
    )
    table.add_column("Extension", style="bold", no_wrap=True)
    table.add_column("File Type", no_wrap=True)
    table.add_column("Description", ratio=1)

    table.add_row(ext, ftype, desc)

    console.print(table)
