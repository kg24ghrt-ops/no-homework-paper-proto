"""PNG export helpers."""

import os
from PIL import Image

from .paper import render_page
from .config import PaperConfig


def export_png(path: str, config: PaperConfig = None, overwrite: bool = False) -> str:
    if config is None:
        config = PaperConfig()
    img = render_page(config)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    try:
        img.save(path, format="PNG")
    except Exception as exc:
        raise IOError(f"Failed to write PNG: {exc}") from exc
    return path
