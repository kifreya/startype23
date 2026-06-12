"""CLI entry-point for StarType23."""

from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .analyzer import scan_directory
from .charts import render_chart
from .filter import filter_infos
from .interactive import run_interactive
from .logo import render_logo
from .tables import render_explain_table
from .user_colors import resolve_user_colors

_NONE = "__none__"


def _print_logo() -> None:
    """Print the logo and exit."""
    from rich.console import Console

    console = Console()
    console.print(render_logo())


@click.command()
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="StarType23",
    message="%(prog)s %(version)s",
)
@click.option(
    "--logo",
    is_flag=True,
    default=False,
    expose_value=False,
    callback=lambda ctx, param, value: _print_logo() or ctx.exit() if value else None,
    help="Display the StarType23 logo.",
)
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
@click.option(
    "--colors",
    multiple=True,
    help="Hex colour codes or path to a colour file. Repeatable. Accepts # or without.",
)
@click.option(
    "--borderless",
    is_flag=True,
    default=False,
    help="Render tables without borders.",
)
@click.option(
    "--filter",
    "filter_str",
    default=None,
    help="Filter by extensions (comma, period, colon, semicolon, newline separated).",
)
@click.option(
    "--interactive",
    is_flag=True,
    default=False,
    help="Launch interactive REPL mode for building flags.",
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
    colors: tuple[str, ...] | None = None,
    borderless: bool = False,
    filter_str: str | None = None,
    interactive: bool = False,
) -> None:
    """Analyze file types in a directory and display a colourful chart."""
    if explain is not None:
        render_explain_table(explain)
        return

    if interactive:
        run_interactive()
        return

    target = Path(path).resolve()

    exclude_set: set[str] = set(exclude) if exclude else set()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Scanning...", total=None)

            def progress_callback(count: int) -> None:
                progress.update(task, description=f"Scanning... {count} files found")

            infos = scan_directory(
                path=str(target),
                exclude_dirs=exclude_set if exclude_set else None,
                include_hidden=include_hidden,
                progress_callback=progress_callback,
            )
    except NotADirectoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if filter_str:
        filtered = filter_infos(infos, filter_str)
        if not filtered:
            click.echo("No file types matched the filter.", err=True)
            raise SystemExit(1)
        infos = filtered

    col_values = [
        v
        for v in (col_filetype, col_count, col_percentage, col_distribution)
        if v != _NONE
    ]
    columns: set[str] | None = set(col_values) if col_values else None

    user_colors, color_warning = resolve_user_colors(colors, len(infos))
    if color_warning:
        click.echo(color_warning, err=True)

    render_chart(
        infos,
        root_label=str(target),
        columns=columns,
        size_mode=size,
        user_colors=user_colors,
        borderless=borderless,
    )
