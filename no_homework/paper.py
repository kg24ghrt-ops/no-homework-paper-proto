"""Render a JIS B5 lined school notebook page using Pillow."""

from PIL import Image, ImageDraw

from .config import PaperConfig


def render_page(config: PaperConfig = None) -> "Image.Image":
    if config is None:
        config = PaperConfig()
    if config.width_mm <= 0 or config.height_mm <= 0 or config.dpi <= 0:
        raise ValueError("Invalid paper configuration")
    width, height = config.export_size
    img = Image.new("RGB", (width, height), config.paper_color)
    draw = ImageDraw.Draw(img)
    ppm = config.px_per_mm()

    margin_left = int(round(config.margin_left_mm * ppm))
    top = int(round(config.margin_top_mm * ppm))
    bottom = int(round(config.margin_bottom_mm * ppm))
    spacing = int(round(config.line_spacing_mm * ppm))
    line_thickness = max(1, int(round(config.line_thickness_mm * ppm)))
    margin_thickness = max(1, int(round(config.margin_line_thickness_mm * ppm)))

    # horizontal ruling lines
    y = top
    while y < height - bottom:
        draw.line([(margin_left + 4, y), (width - 20, y)], fill=config.ruling_color, width=line_thickness)
        y += spacing

    # vertical red margin line
    draw.line([(margin_left, top), (margin_left, height - bottom)], fill=config.margin_line_color, width=margin_thickness)

    return img
