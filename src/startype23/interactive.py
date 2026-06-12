"""Interactive REPL mode for building flags without a single command line."""

from pathlib import Path

from rich.console import Console
from rich.text import Text

from .analyzer import scan_directory
from .charts import render_chart
from .filter import filter_infos
from .user_colors import resolve_user_colors

__all__ = ["run_interactive"]


def _show_help(console: Console) -> None:
    """Print available commands."""
    console.print()
    console.print("[bold underline]Interactive commands[/bold underline]")
    console.print("  --size               Toggle size mode")
    console.print("  --filetype           Toggle File Type column")
    console.print("  --count              Toggle Count column")
    console.print("  --percentage         Toggle Percentage column")
    console.print("  --distribution       Toggle Distribution column")
    console.print("  --borderless         Toggle borderless mode")
    console.print("  --path DIR           Set scan directory")
    console.print("  --filter EXTS        Filter by extensions (e.g. .py,.md)")
    console.print("  --colors HEX ...     Add custom colours")
    console.print("  run / go             Execute the scan with current flags")
    console.print("  help                 Show this help")
    console.print("  quit / exit          Exit")
    console.print()


def run_interactive() -> None:
    """REPL loop: collect flags interactively, then scan and render."""
    console = Console()

    state: dict = {
        "size": False,
        "filetype": False,
        "count": False,
        "percentage": False,
        "distribution": False,
        "borderless": False,
        "filter": None,
        "path": ".",
        "colors": None,
    }
    colour_args: list[str] = []

    # Dispatch table: maps flag name -> callable that mutates state.
    def _toggle(key: str) -> None:
        state[key] = not state[key]
        console.print(f"  {key} = {state[key]}")

    def _set_path(val: str) -> None:
        state["path"] = val
        console.print(f"  path = {val}")

    def _set_filter(val: str) -> None:
        state["filter"] = val
        console.print(f"  filter = {val}")

    def _add_colour(val: str) -> None:
        colour_args.append(val)

    _TOGGLE_FLAGS = frozenset(
        {
            "--size",
            "--filetype",
            "--count",
            "--percentage",
            "--distribution",
            "--borderless",
        }
    )

    _SET_FLAGS = {
        "--path": _set_path,
        "--filter": _set_filter,
    }

    console.print()
    console.print(Text("StarType23 interactive mode", style="bold underline"))
    console.print("Type flags, then 'run' to scan. Type 'help' for commands.")
    console.print()

    while True:
        line = input("st23> ").strip()
        if not line:
            continue
        lower = line.lower()

        if lower in ("quit", "exit", "q"):
            return
        if lower in ("run", "go"):
            break
        if lower == "help":
            _show_help(console)
            continue

        for token in line.split():
            if token in _TOGGLE_FLAGS:
                _toggle(token.lstrip("-").replace("-", "_"))
            elif token.startswith("--path=") or token.startswith("--filter="):
                flag, _, val = token.partition("=")
                _SET_FLAGS[flag](val)
            elif token in _SET_FLAGS:
                # Value follows as next token -- skip, handled by lookahead below
                pass
            elif token.startswith("--colors"):
                _add_colour(token)
            elif token.startswith("-"):
                # Could be a value for the previous flag
                pass

    # Build column set from toggled flags
    col_values = [
        k for k in ("filetype", "count", "percentage", "distribution") if state[k]
    ]
    columns: set[str] | None = set(col_values) if col_values else None

    target = Path(state["path"]).resolve()

    try:
        infos = scan_directory(path=str(target))
    except NotADirectoryError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        return

    if state["filter"]:
        infos = filter_infos(infos, state["filter"])
        if not infos:
            console.print(
                "[bold yellow]No file types matched the filter.[/bold yellow]"
            )
            return

    user_colors, color_warning = resolve_user_colors(
        tuple(colour_args) if colour_args else None, len(infos)
    )
    if color_warning:
        console.print(f"[bold yellow]{color_warning}[/bold yellow]")

    render_chart(
        infos,
        root_label=str(target),
        columns=columns,
        size_mode=state["size"],
        user_colors=user_colors,
        borderless=state["borderless"],
    )
