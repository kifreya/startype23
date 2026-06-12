"""Interactive REPL mode for building flags without a single command line."""

from pathlib import Path

from rich.console import Console
from rich.text import Text

from .analyzer import scan_directory
from .charts import render_chart
from .filter import filter_infos
from .user_colors import resolve_user_colors


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

        parts = line.split()
        for part in parts:
            if part == "--size":
                state["size"] = not state["size"]
                console.print(f"  size = {state['size']}")
            elif part == "--filetype":
                state["filetype"] = not state["filetype"]
                console.print(f"  filetype = {state['filetype']}")
            elif part == "--count":
                state["count"] = not state["count"]
                console.print(f"  count = {state['count']}")
            elif part == "--percentage":
                state["percentage"] = not state["percentage"]
                console.print(f"  percentage = {state['percentage']}")
            elif part == "--distribution":
                state["distribution"] = not state["distribution"]
                console.print(f"  distribution = {state['distribution']}")
            elif part == "--borderless":
                state["borderless"] = not state["borderless"]
                console.print(f"  borderless = {state['borderless']}")
            elif part.startswith("--path="):
                state["path"] = part.split("=", 1)[1]
                console.print(f"  path = {state['path']}")
            elif part.startswith("--filter="):
                state["filter"] = part.split("=", 1)[1]
                console.print(f"  filter = {state['filter']}")
            elif part == "--path" or part == "--filter":
                # Value follows in next token -- handled below
                pass
            elif part.startswith("--colors"):
                colour_args.append(part)
            else:
                # Check for --path <val> or --filter <val> where value is
                # the current part and is a standalone token
                pass

    # Build column set from toggled flags
    col_values = [
        v
        for k, v in [
            ("filetype", state["filetype"]),
            ("count", state["count"]),
            ("percentage", state["percentage"]),
            ("distribution", state["distribution"]),
        ]
        if v
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
