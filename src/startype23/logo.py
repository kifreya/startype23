"""Dotted ASCII-art logo rendering for StarType23."""

from rich.text import Text

from . import __version__

_DOTTED = "\u2591"  # light shade -- gives a dotted/stippled appearance


def _row(
    logo: Text, content: str, w: int, left_pad: int = 0, right_pad: int = 0
) -> None:
    """Append a single row of the logo with dotted borders."""
    _ = logo.append(_DOTTED)
    if content:
        _ = logo.append(" " * left_pad)
        _ = logo.append(content)
        _ = logo.append(" " * right_pad)
    else:
        _ = logo.append(" " * (w - 2))
    _ = logo.append(_DOTTED)


def render_logo() -> Text:
    """Build a dotted ASCII-art logo banner for StarType23."""
    w = 48
    inner = w - 2
    title = f"StarType23  {__version__}"
    pad = inner - len(title)
    left_pad = pad // 2
    right_pad = pad - left_pad

    logo = Text()
    logo.append(_DOTTED * w)
    logo.append("\n")
    _row(logo, "", w)
    logo.append("\n")
    _row(logo, title, w, left_pad, right_pad)
    logo.append("\n")
    _row(logo, "", w)
    logo.append("\n")
    logo.append(_DOTTED * w)
    return logo
