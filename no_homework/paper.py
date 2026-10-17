"""Render a JIS B5 lined school notebook page using Pillow."""

from typing import Optional

from PIL import Image, ImageDraw

from .config import PaperConfig

# Extra pixel inset of the ruling lines from the left margin line.
_RULING_INSET_PX = 4
# Right-edge clearance kept between ruling lines and the page border (px).
_RULING_RIGHT_MARGIN_PX = 20


def render_page(config: Optional[PaperConfig] = None) -> Image.Image:
    """Return a full-resolution RGB image of a ruled notebook page.

    Args:
        config: Page geometry; defaults to standard JIS B5 at 300 DPI.

    Raises:
        ValueError: If the supplied configuration is invalid.
    """
    if config is None:
        config = PaperConfig()
    config.validate()

    width, height = config.export_size
    img = Image.new("RGB", (width, height), config.paper_color)
    draw = ImageDraw.Draw(img)

    margin_left = config.mm_to_px(config.margin_left_mm)
    top = config.mm_to_px(config.margin_top_mm)
    bottom = config.mm_to_px(config.margin_bottom_mm)
    spacing = config.mm_to_px(config.line_spacing_mm)
    line_thickness = max(1, config.mm_to_px(config.line_thickness_mm))
    margin_thickness = max(1, config.mm_to_px(config.margin_line_thickness_mm))

    _draw_ruling_lines(draw, config, width=width, height=height, top=top,
                       bottom=bottom, spacing=spacing, thickness=line_thickness,
                       margin_left=margin_left)
    _draw_margin_line(draw, config, height=height, top=top, bottom=bottom,
                     margin_left=margin_left, thickness=margin_thickness)

    return img


def _draw_ruling_lines(
    draw: ImageDraw.ImageDraw,
    config: PaperConfig,
    *,
    width: int,
    height: int,
    top: int,
    bottom: int,
    spacing: int,
    thickness: int,
    margin_left: int,
) -> None:
    """Draw evenly spaced horizontal ruling lines across the text area."""
    x_start = margin_left + _RULING_INSET_PX
    x_end = width - _RULING_RIGHT_MARGIN_PX
    for y in range(top, height - bottom, spacing):
        draw.line([(x_start, y), (x_end, y)], fill=config.ruling_color, width=thickness)


def _draw_margin_line(
    draw: ImageDraw.ImageDraw,
    config: PaperConfig,
    *,
    height: int,
    top: int,
    bottom: int,
    margin_left: int,
    thickness: int,
) -> None:
    """Draw the vertical red margin line down the left side of the page."""
    draw.line(
        [(margin_left, top), (margin_left, height - bottom)],
        fill=config.margin_line_color,
        width=thickness,
    )
