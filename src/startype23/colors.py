"""Color generation with golden-angle hue distribution and luminance safety."""

import colorsys
from collections.abc import Sequence

from .analyzer import FileTypeInfo

_GOLDEN_ANGLE = 137.508  # degrees -- optimal spacing around the colour wheel
_MIN_HUE_GAP = 25  # degrees -- safety threshold to avoid lookalikes
_SATURATION = 0.70  # HSL saturation (vivid but not neon)
_LIGHTNESS = 0.58  # HSL lightness (visible on both light and dark backgrounds)


def _hsl_to_hex(hue_deg: float, saturation: float, lightness: float) -> str:
    """Convert HLS (0-1 range) to a hex colour string like ``"#7CB342"``."""
    r, g, b = colorsys.hls_to_rgb(hue_deg / 360.0, lightness, saturation)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def _luminance(hex_color: str) -> float:
    """Relative luminance of a hex colour (WCAG sRGB formula)."""
    h = hex_color.lstrip("#")
    r, g, b = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def linearise(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearise(r) + 0.7152 * linearise(g) + 0.0722 * linearise(b)


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
