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
        """Raise :class:`ValueError` if any core dimension is non-positive."""
        if self.width_mm <= 0 or self.height_mm <= 0 or self.dpi <= 0:
            raise ValueError("Invalid paper configuration")

    @property
    def px_per_mm(self) -> float:
        """Number of pixels per millimetre implied by :attr:`dpi`."""
        return self.dpi / 25.4

    def mm_to_px(self, mm: Millimetres) -> int:
        """Convert a millimetre length to whole pixels (rounded)."""
        return int(round(mm * self.px_per_mm))

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
