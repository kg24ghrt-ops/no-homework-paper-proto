"""Centralized physical paper configuration for JIS B5 notebook paper."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperConfig:
    width_mm: float = 182.0
    height_mm: float = 257.0
    dpi: int = 300

    # Margins and ruling in millimetres, converted to pixels by DPI
    margin_left_mm: float = 25.0
    margin_top_mm: float = 15.0
    margin_bottom_mm: float = 15.0
    line_spacing_mm: float = 8.0
    line_thickness_mm: float = 0.15
    margin_line_thickness_mm: float = 0.3

    # Colors
    paper_color: tuple = (248, 245, 236)  # warm white
    ruling_color: tuple = (170, 195, 225)  # light blue-gray
    margin_line_color: tuple = (200, 110, 110)  # muted red

    def __post_init__(self):
        if self.width_mm <= 0 or self.height_mm <= 0 or self.dpi <= 0:
            raise ValueError("Invalid paper configuration")

    def px_per_mm(self) -> float:
        return self.dpi / 25.4
    def width_px(self) -> int:
        return int(round(self.width_mm * self.px_per_mm()))

    def height_px(self) -> int:
        return int(round(self.height_mm * self.px_per_mm()))

    def aspect_ratio(self) -> float:
        return self.width_mm / self.height_mm

    @property
    def export_size(self) -> tuple:
        return (self.width_px(), self.height_px())
