"""Color generation with 3D golden-ratio distribution and luminance safety."""

import colorsys
from collections.abc import Sequence

from .analyzer import FileTypeInfo

# Golden-angle hue spacing -- optimal around the colour wheel.
_GOLDEN_ANGLE = 137.508  # degrees

# Golden-ratio constants for cycling saturation and lightness independently.
# These are irrational relative to the golden angle, so the three HSL
# dimensions drift apart and create well-separated colours.
_GOLDEN_CONJUGATE = 0.618034  # 1 / phi
_GOLDEN_COMPLEMENT = 0.381966  # 1 - conjugate

_SAT_BASE = 0.60
_SAT_RANGE = 0.25  # sat varies 0.60 - 0.85
_LIT_BASE = 0.45
_LIT_RANGE = 0.25  # lit varies 0.45 - 0.70


def _hsl_to_hex(hue_deg: float, saturation: float, lightness: float) -> str:
    """Convert HLS values to a hex colour string like ``"#7CB342"``."""
    r, g, b = colorsys.hls_to_rgb(hue_deg / 360.0, lightness, saturation)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def _luminance(hex_color: str) -> float:
    """Relative luminance of a hex colour (WCAG sRGB formula)."""
    h = hex_color.lstrip("#")
    r, g, b = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def linearise(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearise(r) + 0.7152 * linearise(g) + 0.0722 * linearise(b)


def _generate_colour(n: int) -> str:
    """Return the *n*th colour in a perceptually varied sequence.

    Hue is spread via the golden angle.  Saturation and lightness drift
    independently using golden-ratio multiples, so colours stay visually
    distinct even when their hues are close.
    """
    hue = (n * _GOLDEN_ANGLE) % 360.0
    sat = _SAT_BASE + (n * _GOLDEN_CONJUGATE) % 1.0 * _SAT_RANGE
    lit = _LIT_BASE + (n * _GOLDEN_COMPLEMENT) % 1.0 * _LIT_RANGE

    hex_colour = _hsl_to_hex(hue, sat, lit)

    # Safety net: ensure the colour is readable on both light and dark terminals.
    lum = _luminance(hex_colour)

    if lum < 0.15:
        for boost in range(1, 10):
            candidate = _hsl_to_hex(hue, sat, min(lit + boost * 0.04, 0.85))
            if _luminance(candidate) >= 0.20:
                return candidate
    elif lum > 0.80:
        for cut in range(1, 10):
            candidate = _hsl_to_hex(hue, sat, max(lit - cut * 0.04, 0.15))
            if _luminance(candidate) <= 0.70:
                return candidate

    return hex_colour


def assign_colors(
    infos: Sequence[FileTypeInfo],
    user_colors: list[str] | None = None,
) -> dict[str, str]:
    """Map every extension to a colour.

    When *user_colors* is provided and contains enough entries, they are used
    directly (cycled if fewer than needed rather than failing).  Otherwise
    colours are generated via golden-ratio distribution across HSL dimensions.
    """
    mapping: dict[str, str] = {}
    if user_colors:
        for idx, info in enumerate(infos):
            mapping[info.extension] = user_colors[idx % len(user_colors)]
    else:
        for idx, info in enumerate(infos):
            mapping[info.extension] = _generate_colour(idx)
    return mapping
