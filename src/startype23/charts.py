"""Top-level rendering orchestration for StarType23."""

import shutil
from collections.abc import Sequence

from rich.console import Console
from rich.padding import Padding
from rich.text import Text

from .analyzer import FileTypeInfo
from .bars import render_stacked_bar
from .colors import assign_colors
from .formatting import (
    ColumnSet,
    _format_size,
    resolve_columns,
)
from .tables import render_legend, render_size_table, render_table


def render_chart(
    infos: Sequence[FileTypeInfo],
    root_label: str = "",
    *,
    console: Console | None = None,
    columns: ColumnSet | None = None,
    size_mode: bool = False,
) -> None:
    """Render the full file-type distribution chart on *console*.

    Parameters
    ----------
    infos
        Sorted extension statistics.
    root_label
        Display path for the header.
    console
        Rich Console to print to.
    columns
        Which columns to show (``None`` = all default columns).
    size_mode
        If ``True``, render the size-distribution view instead of count.
    """
    if console is None:
        console = Console()

    if not infos:
        console.print("[bold]No files found in the scanned directory.[/bold]")
        return

    term_width = shutil.get_terminal_size((80, 24)).columns
    stacked_width = min(term_width - 4, 80)
    table_bar_width = min(term_width - 36, 40)

    colors = assign_colors(infos)

    # --- Heading ---
    mode_label = "File Size Distribution" if size_mode else "File Type Distribution"
    heading = Text()
    _ = heading.append(mode_label, style="bold underline")
    if root_label:
        _ = heading.append(f"  --  {root_label}", style="italic dim")
    console.print(Padding(heading, (0, 0, 1, 0)))

    # --- Stacked bar ---
    stacked_bar = render_stacked_bar(
        infos, colors, bar_width=stacked_width, bar_height=3, use_size=size_mode
    )
    console.print(Padding(stacked_bar, (0, 2, 1, 2)))

    # --- Legend ---
    legend = render_legend(infos, colors)
    console.print(Padding(legend, (0, 0, 1, 0)))

    # --- Table ---
    if size_mode:
        table = render_size_table(
            infos, colors, bar_width=table_bar_width, columns=columns
        )
        total_sz = sum(i.total_size for i in infos)
        console.print(table)
        console.print(
            Padding(
                f"[dim]{_format_size(total_sz)} across {len(infos)} distinct types[/dim]",
                (1, 0, 0, 0),
            )
        )
    else:
        table = render_table(infos, colors, bar_width=table_bar_width, columns=columns)
        total_files = sum(i.count for i in infos)
        console.print(table)
        console.print(
            Padding(
                f"[dim]{total_files} files across {len(infos)} distinct types[/dim]",
                (1, 0, 0, 0),
            )
        )
