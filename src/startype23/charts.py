"""Chart rendering: color assignment, stacked-bar, and rich Table."""

# ---------------------------------------------------------------------------
# Color generator
#
# Generates visually distinct, background-safe colors on demand using
# golden-angle hue distribution with collision avoidance.
# ---------------------------------------------------------------------------
import colorsys
import shutil
from collections.abc import Sequence

from rich.console import Console
from rich.padding import Padding
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .analyzer import FileTypeInfo
from .extensions import EXTENSION_INFO

_GOLDEN_ANGLE = 137.508  # degrees -- optimal spacing around the colour wheel
_MIN_HUE_GAP = 25  # degrees -- safety threshold to avoid lookalikes
_SATURATION = 0.70  # HSL saturation (vivid but not neon)
_LIGHTNESS = 0.58  # HSL lightness (visible on both light and dark backgrounds)


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HLS (0-1 range) to a hex colour string like ``"#7CB342"``."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def _luminance(hex_color: str) -> float:
    """Relative luminance of a hex colour (WCAG sRGB formula)."""
    h = hex_color.lstrip("#")
    r, g, b = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def linearise(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearise(r) + 0.7152 * linearise(g) + 0.0722 * linearise(b)


def _contrast_ratio(l1: float, l2: float) -> float:
    """WCAG contrast ratio between two relative luminances."""
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _generate_colour(n: int, assigned_hues: list[float]) -> str:
    """Return the *n*th colour in the sequence, avoiding hue collisions."""
    hue = (n * _GOLDEN_ANGLE) % 360.0

    # Nudge away from any previously assigned hue that is too close.
    for _ in range(12):
        if any(abs(hue - h) < _MIN_HUE_GAP for h in assigned_hues):
            hue = (hue + _MIN_HUE_GAP) % 360.0
        else:
            break

    assigned_hues.append(hue)
    hex_colour = _hsl_to_hex(hue, _SATURATION, _LIGHTNESS)

    # Safety net: if the colour has poor contrast against a dark background
    # (luminance too low) or a light background (luminance too high), adjust
    # lightness and regenerate.
    lum = _luminance(hex_colour)

    if lum < 0.15:
        # Too dark on a dark terminal -- boost lightness.
        for boost in range(1, 10):
            candidate = _hsl_to_hex(
                hue, _SATURATION, min(_LIGHTNESS + boost * 0.04, 0.85)
            )
            if _luminance(candidate) >= 0.20:
                hex_colour = candidate
                break
    elif lum > 0.80:
        # Too bright on a light terminal -- reduce lightness.
        for cut in range(1, 10):
            candidate = _hsl_to_hex(
                hue, _SATURATION, max(_LIGHTNESS - cut * 0.04, 0.15)
            )
            if _luminance(candidate) <= 0.70:
                hex_colour = candidate
                break

    return hex_colour


def assign_colors(infos: Sequence[FileTypeInfo]) -> dict[str, str]:
    """Map every extension in *infos* to a visually distinct, background-safe colour.

    Colours are generated dynamically using golden-angle hue distribution,
    with collision avoidance and luminance safety nets.
    """
    assigned_hues: list[float] = []
    mapping: dict[str, str] = {}
    for idx, info in enumerate(infos):
        mapping[info.extension] = _generate_colour(idx, assigned_hues)
    return mapping


# ---------------------------------------------------------------------------
# Stacked proportion bar
# ---------------------------------------------------------------------------


def _render_stacked_bar(
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


# ---------------------------------------------------------------------------
# Size formatting
# ---------------------------------------------------------------------------

_SIZE_SUFFIXES = ["B", "KB", "MB", "GB", "TB"]


def _format_size(size_bytes: int) -> str:
    """Return a human-readable size string (e.g. ``"4.2 KB"``, ``"1.5 MB"``)."""
    if size_bytes == 0:
        return "0 B"
    magnitude = 0
    remaining = float(size_bytes)
    while remaining >= 1024 and magnitude < len(_SIZE_SUFFIXES) - 1:
        remaining /= 1024
        magnitude += 1
    if magnitude == 0:
        return f"{size_bytes} B"
    return f"{remaining:.1f} {_SIZE_SUFFIXES[magnitude]}"


# ---------------------------------------------------------------------------
# Column visibility helpers
# ---------------------------------------------------------------------------

ColumnSet = set[str]

_COL_EXTENSION = "extension"
_COL_FILETYPE = "filetype"
_COL_COUNT = "count"
_COL_PERCENTAGE = "percentage"
_COL_DISTRIBUTION = "distribution"
_COL_SIZE = "size"
_COL_SIZE_PCT = "size_pct"

_ALL_COLUMNS: ColumnSet = {
    _COL_EXTENSION,
    _COL_FILETYPE,
    _COL_COUNT,
    _COL_PERCENTAGE,
    _COL_DISTRIBUTION,
}

_ALL_SIZE_COLUMNS: ColumnSet = {
    _COL_EXTENSION,
    _COL_FILETYPE,
    _COL_COUNT,
    _COL_SIZE,
    _COL_SIZE_PCT,
    _COL_DISTRIBUTION,
}


def _resolve_columns(visible: ColumnSet | None, all_available: ColumnSet) -> ColumnSet:
    """Return the effective set of columns to display.

    When *visible* is ``None`` or empty, all available columns are shown.
    Otherwise only the explicitly listed columns (plus Extension) are shown.
    """
    if visible is None or not visible:
        return all_available
    result: ColumnSet = {_COL_EXTENSION, *visible}
    return result & all_available


# ---------------------------------------------------------------------------
# Detailed table (count mode)
# ---------------------------------------------------------------------------


def _render_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
) -> Table:
    """Create a rich ``Table`` with per-extension details and a mini bar."""
    show_cols = _resolve_columns(columns, _ALL_COLUMNS)

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

        bar_text = Text()
        num_blocks = bar_fill // 2
        _ = bar_text.append("\u2593" * num_blocks, style=Style(color=hex_color))

        ftype, _desc = EXTENSION_INFO.get(info.extension, ("Unknown", ""))

        row = [info.extension]
        if _COL_FILETYPE in show_cols:
            row.append(ftype)
        if _COL_COUNT in show_cols:
            row.append(str(info.count))
        if _COL_PERCENTAGE in show_cols:
            row.append(f"{info.percentage}%")
        if _COL_DISTRIBUTION in show_cols:
            row.append(bar_text)

        table.add_row(*row)

    return table


# ---------------------------------------------------------------------------
# Size table
# ---------------------------------------------------------------------------


def _render_size_table(
    infos: Sequence[FileTypeInfo],
    colors: dict[str, str],
    bar_width: int = 40,
    columns: ColumnSet | None = None,
) -> Table:
    """Create a rich ``Table`` showing size distribution per extension."""
    show_cols = _resolve_columns(columns, _ALL_SIZE_COLUMNS)

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

        bar_text = Text()
        num_blocks = bar_fill // 2
        _ = bar_text.append("\u2593" * num_blocks, style=Style(color=hex_color))

        ftype, _desc = EXTENSION_INFO.get(info.extension, ("Unknown", ""))

        row = [info.extension]
        if _COL_FILETYPE in show_cols:
            row.append(ftype)
        if _COL_COUNT in show_cols:
            row.append(str(info.count))
        if _COL_SIZE in show_cols:
            row.append(_format_size(info.total_size))
        if _COL_SIZE_PCT in show_cols:
            row.append(f"{info.size_percentage}%")
        if _COL_DISTRIBUTION in show_cols:
            row.append(bar_text)

        table.add_row(*row)

    return table


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------


def _render_legend(
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


# ---------------------------------------------------------------------------
# Top-level render entry points
# ---------------------------------------------------------------------------


def normalize_extension(ext: str) -> str:
    """Ensure an extension string has a leading dot, lowercased.

    Accepts ``".py"``, ``"py"``, ``".PY"``, ``"PY"``.
    Returns the lowercased form with a leading dot.
    """
    ext = ext.strip().lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return ext


def render_explain(
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
    table.add_column("Description")

    table.add_row(ext, ftype, desc)

    console.print(table)


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
    stacked_bar = _render_stacked_bar(
        infos, colors, bar_width=stacked_width, bar_height=3, use_size=size_mode
    )
    console.print(Padding(stacked_bar, (0, 2, 1, 2)))

    # --- Legend ---
    legend = _render_legend(infos, colors)
    console.print(Padding(legend, (0, 0, 1, 0)))

    # --- Table ---
    if size_mode:
        table = _render_size_table(
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
        table = _render_table(infos, colors, bar_width=table_bar_width, columns=columns)
        total_files = sum(i.count for i in infos)
        console.print(table)
        console.print(
            Padding(
                f"[dim]{total_files} files across {len(infos)} distinct types[/dim]",
                (1, 0, 0, 0),
            )
        )
