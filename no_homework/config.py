"""Centralized physical paper configuration for JIS B5 notebook paper."""

from dataclasses import dataclass
from typing import Tuple

DotsPerInch = int
Millimetres = float


@dataclass(frozen=True)
class PaperConfig:
    """Immutable description of the sheet: size, ruling geometry and colors.

    All geometry is expressed in millimetres; pixel values are derived from
    the configured DPI via :meth:`px_per_mm`.
    """

    width_mm: Millimetres = 182.0
    height_mm: Millimetres = 257.0
    dpi: DotsPerInch = 300

    # Margins and ruling in millimetres, converted to pixels by DPI
    margin_left_mm: Millimetres = 25.0
    margin_top_mm: Millimetres = 15.0
    margin_bottom_mm: Millimetres = 15.0
    line_spacing_mm: Millimetres = 8.0
    line_thickness_mm: Millimetres = 0.15
    margin_line_thickness_mm: Millimetres = 0.3

    # Colors (RGB, 0-255)
    paper_color: Tuple[int, int, int] = (248, 245, 236)  # warm white
    ruling_color: Tuple[int, int, int] = (170, 195, 225)  # light blue-gray
    margin_line_color: Tuple[int, int, int] = (200, 110, 110)  # muted red

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise :class:`ValueError` for invalid geometry or colors.

        Checks that page dimensions and DPI are positive, margins and ruling
        sizes are non-negative, the drawable text area stays positive after
        subtracting the top/bottom margins, every color is an RGB triple with
        components in the 0-255 range, and the line spacing converts to at
        least one pixel (a zero-pixel step makes ``range()`` in the drawing
        code fail, e.g. when rounding at a very low DPI).
        """
        name = type(self).__name__

        if self.width_mm <= 0 or self.height_mm <= 0:
            raise ValueError(f"{name}: width_mm and height_mm must be positive")
        if self.dpi <= 0:
            raise ValueError(f"{name}: dpi must be positive")

        for field in (
            "margin_left_mm",
            "margin_top_mm",
            "margin_bottom_mm",
            "line_spacing_mm",
            "line_thickness_mm",
            "margin_line_thickness_mm",
        ):
            value = getattr(self, field)
            if value < 0:
                raise ValueError(f"{name}: {field} must not be negative")

        # Leave room for at least one pixel of text area between the margins.
        if self.margin_top_mm + self.margin_bottom_mm >= self.height_mm:
            raise ValueError(
                f"{name}: top and bottom margins must leave usable page height"
            )
        if self.margin_left_mm >= self.width_mm:
            raise ValueError(
                f"{name}: left margin must be smaller than the page width"
            )

        for field in ("paper_color", "ruling_color", "margin_line_color"):
            self._validate_color(getattr(self, field), field, name)

        # A very low DPI can round the line spacing down to zero pixels,
        # which would crash range() in the drawing code (range() arg 3 must
        # not be zero).  mm_to_px() clamps positive lengths to >= 1 px, so
        # this normally holds; it also guards hand-mutated configs where the
        # converted step could still be zero.
        if self.line_spacing_mm > 0 and self.mm_to_px(self.line_spacing_mm) < 1:
            raise ValueError(
                f"{name}: line spacing must convert to at least one pixel; "
                "increase line_spacing_mm or the DPI"
            )

    @staticmethod
    def _validate_color(color: object, field: str, name: str) -> None:
        """Ensure *color* is an RGB triple of integers within 0-255."""
        if not isinstance(color, tuple) or len(color) != 3:
            raise ValueError(f"{name}: {field} must be an (R, G, B) tuple")
        for component in color:
            if (
                not isinstance(component, int)
                or isinstance(component, bool)
                or not 0 <= component <= 255
            ):
                raise ValueError(
                    f"{name}: {field} components must be integers from 0 to 255"
                )

    @property
    def px_per_mm(self) -> float:
        """Number of pixels per millimetre implied by :attr:`dpi`."""
        return self.dpi / 25.4

    def mm_to_px(self, mm: Millimetres) -> int:
        """Convert a millimetre length to whole pixels (rounded).

        A non-zero length is never converted to zero pixels: values that
        would round away at a very low DPI are clamped up to one pixel, so
        the drawing code always receives a usable line-spacing step (a zero
        step crashes ``range()``) and line widths.  Zero-length inputs
        convert to zero pixels.
        """
        px = int(round(mm * self.px_per_mm))
        if mm != 0 and px == 0:
            px = 1
        return px

    @property
    def width_px(self) -> int:
        return self.mm_to_px(self.width_mm)

    @property
    def height_px(self) -> int:
        return self.mm_to_px(self.height_mm)

    @property
    def aspect_ratio(self) -> float:
        return self.width_mm / self.height_mm

    @property
    def export_size(self) -> Tuple[int, int]:
        """Full-resolution page size in pixels, suitable for Pillow/exports."""
        return (self.width_px, self.height_px)
