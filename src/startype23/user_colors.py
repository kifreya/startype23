"""User-provided color loading from CLI args, files, and default config paths."""

import re
from pathlib import Path

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _parse_hex_line(text: str) -> list[str]:
    """Split *text* by comma, semicolon, colon, or whitespace and extract hex codes."""
    parts = re.split(r"[,;:\s]+", text.strip())
    colors: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        normalized = part if part.startswith("#") else f"#{part}"
        if _HEX_RE.match(normalized):
            colors.append(normalized.upper())
    return colors


def _load_colors_from_file(path: Path) -> list[str]:
    """Read hex codes from a text file and return parsed colors."""
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Cannot read file: {exc}") from exc

    colors = _parse_hex_line(text)
    if not colors:
        raise ValueError(f"No valid hex codes found in {path}")
    return colors


def _find_default_config() -> Path | None:
    """Locate ``$HOME/.config/startype23/colors.txt`` (case-insensitive directory)."""
    config_root = Path.home() / ".config"
    if not config_root.is_dir():
        return None
    for child in config_root.iterdir():
        if child.is_dir() and child.name.lower() == "startype23":
            candidate = child / "colors.txt"
            if candidate.is_file():
                return candidate
    return None


def resolve_user_colors(
    cli_values: tuple[str, ...] | None,
    num_needed: int,
) -> tuple[list[str] | None, str | None]:
    """Resolve user-supplied colors from CLI or default config.

    Parameters
    ----------
    cli_values
        Raw values from the ``--colors`` flag (each may be a file path or inline hex).
    num_needed
        Number of distinct extensions that need a colour.

    Returns
    -------
    (colors_list, warning)
        ``colors_list`` is ``None`` when falling back to generated colours.
        ``warning`` is a human-readable message to display, or ``None``.
    """
    raw_sources: list[str] = []

    if cli_values:
        for val in cli_values:
            p = Path(val)
            if p.is_file():
                try:
                    raw_sources.extend(_load_colors_from_file(p))
                except (FileNotFoundError, ValueError) as exc:
                    return None, f"Invalid file: {exc}"
            else:
                raw_sources.append(val)
    else:
        cfg = _find_default_config()
        if cfg is not None:
            try:
                raw_sources.extend(_load_colors_from_file(cfg))
            except (FileNotFoundError, ValueError):
                pass

    if not raw_sources:
        return None, None

    all_colors: list[str] = []
    for src in raw_sources:
        parsed = _parse_hex_line(src)
        if not parsed:
            return None, f"Invalid color value: {src}"
        all_colors.extend(parsed)

    if not all_colors:
        return None, None

    if len(all_colors) < num_needed:
        return (
            None,
            f"Warning: only {len(all_colors)} colour(s) provided for {num_needed} type(s). "
            f"Using default colours.",
        )

    return all_colors, None
