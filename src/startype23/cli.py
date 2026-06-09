"""CLI entry-point for StarType23."""

from pathlib import Path

import click

from .analyzer import scan_directory
from .charts import render_chart
from .tables import render_explain_table

_NONE = "__none__"


@click.command()
@click.option(
    "--path",
    default=".",
    show_default=True,
    help="Directory to scan for file types.",
)
@click.option(
    "--exclude",
    "-x",
    multiple=True,
    help="Additional directory names to exclude (repeatable).",
)
@click.option(
    "--include-hidden/--no-include-hidden",
    default=False,
    show_default=True,
    help="Include hidden files and directories in the scan.",
)
@click.option(
    "--explain",
    "-e",
    metavar="EXTENSION",
    help="Show file type and description for a given extension.",
)
@click.option(
    "--size",
    "-s",
    is_flag=True,
    default=False,
    help="Show size distribution instead of file count distribution.",
)
@click.option(
    "--filetype",
    "-ft",
    "col_filetype",
    flag_value="filetype",
    default=_NONE,
    help="Show the File Type column (use alone to show only selected columns).",
)
@click.option(
    "--count",
    "-c",
    "col_count",
    flag_value="count",
    default=_NONE,
    help="Show the Count column (use alone to show only selected columns).",
)
@click.option(
    "--percentage",
    "-p",
    "col_percentage",
    flag_value="percentage",
    default=_NONE,
    help="Show the Percentage column (use alone to show only selected columns).",
)
@click.option(
    "--distribution",
    "-d",
    "col_distribution",
    flag_value="distribution",
    default=_NONE,
    help="Show the Distribution column (use alone to show only selected columns).",
)
def main(
    path: str = ".",
    exclude: tuple[str, ...] | None = None,
    include_hidden: bool = False,
    explain: str | None = None,
    size: bool = False,
    col_filetype: str | None = _NONE,
    col_count: str | None = _NONE,
    col_percentage: str | None = _NONE,
    col_distribution: str | None = _NONE,
) -> None:
    """Analyze file types in a directory and display a colourful chart."""
    if explain is not None:
        render_explain_table(explain)
        return

    target = Path(path).resolve()

    exclude_set: set[str] = set(exclude) if exclude else set()

    try:
        infos = scan_directory(
            path=str(target),
            exclude_dirs=exclude_set if exclude_set else None,
            include_hidden=include_hidden,
        )
    except NotADirectoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    col_values = [
        v
        for v in (col_filetype, col_count, col_percentage, col_distribution)
        if v != _NONE
    ]
    columns: set[str] | None = set(col_values) if col_values else None

    render_chart(infos, root_label=str(target), columns=columns, size_mode=size)
