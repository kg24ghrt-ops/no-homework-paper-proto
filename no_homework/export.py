"""PNG export helpers with Android scoped-storage support."""

import os
from typing import Optional

from .config import PaperConfig
from .paper import render_page


def _android_external_files_dir() -> Optional[str]:
    """Return the app-specific external files directory on Android.

    Works on Android 10+ (API 29+) without special storage permissions because
    it targets the app's own external files directory, which is exempt from
    scoped storage restrictions. Returns ``None`` off-device or on failure.
    """
    try:
        from jnius import autoclass  # noqa: PLC0415 - only available on Android

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        files_dir = activity.getExternalFilesDir(None)
        return files_dir.getAbsolutePath() if files_dir is not None else None
    except Exception:
        return None


def _running_on_android() -> bool:
    try:
        from kivy.utils import platform  # noqa: PLC0415 - Kivy may be absent

        return platform == "android"
    except Exception:
        return False


def export_png(
    path: str,
    config: Optional[PaperConfig] = None,
    overwrite: bool = False,
) -> str:
    """Render a page and save it as a PNG at *path*.

    On Android the file is redirected to the app's external files directory,
    since scoped storage blocks writes to shared locations such as /sdcard.

    Returns the path actually written.

    Raises:
        FileExistsError: If the target exists and *overwrite* is false.
        OSError: If the image cannot be written.
    """
    if config is None:
        config = PaperConfig()
    img = render_page(config)

    if _running_on_android():
        android_dir = _android_external_files_dir()
        if android_dir:
            path = os.path.join(android_dir, os.path.basename(path))

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")

    try:
        img.save(path, format="PNG")
    except Exception as exc:
        raise OSError(f"Failed to write PNG: {exc}") from exc
    return path
