"""PNG export helpers."""

import os
from PIL import Image

from .paper import render_page
from .config import PaperConfig


def _android_external_files_dir():
    """Return the app-specific external files directory on Android.

    Works on Android 10+ (API 29+) without special storage permissions because
    it targets the app's own external files directory, which is exempt from
    scoped storage restrictions.
    """
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        files_dir = activity.getExternalFilesDir(None)
        if files_dir is not None:
            return files_dir.getAbsolutePath()
    except Exception:
        pass
    return None


def export_png(path: str, config: PaperConfig = None, overwrite: bool = False) -> str:
    if config is None:
        config = PaperConfig()
    img = render_page(config)

    # On Android 10+, scoped storage blocks writing to shared locations such as
    # /sdcard. Redirect to the app's external files directory so export works on
    # every Android model 10 and up without extra permissions.
    try:
        from kivy.utils import platform as _platform
        if _platform == 'android':
            android_dir = _android_external_files_dir()
            if android_dir:
                path = os.path.join(android_dir, os.path.basename(path))
    except Exception:
        pass

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
