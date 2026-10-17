"""PNG export helpers with Android scoped-storage support.

Desktop flow: :func:`export_png` renders the page and writes it straight to
the requested path.

Android flow (scoped storage, API 29+): direct writes to shared locations
such as ``/sdcard/Download`` are blocked, so :func:`export_png` renders into
the app's own files directory and then *publishes* the PNG somewhere the
user can find it -- see :mod:`no_homework.android_export`:

1. A destination content URI previously granted by the SAF create-document
   picker (``destination_uri``).
2. The public MediaStore ``Downloads`` collection (default), so the file
   appears in the user's Downloads folder.
3. If publishing fails, callers can still offer the ``ACTION_SEND`` share
   sheet via :func:`no_homework.android_export.share_file`; the staged copy
   inside the app directory is returned as a last resort.
"""

import os
from typing import Optional

from .config import PaperConfig
from .paper import render_page

#: Subdirectory of the app's files area used for staging exports on Android.
_EXPORT_SUBDIR = "exports"


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


def write_png(image, path: str, overwrite: bool = False) -> str:
    """Save an already-rendered Pillow *image* as PNG at *path*.

    Creates parent directories as needed.  This is the low-level primitive
    shared by desktop export and the Android staging step; publishing to
    user-visible locations happens on top of it in
    :mod:`no_homework.android_export`.

    Returns the path actually written.

    Raises:
        FileExistsError: If the target exists and *overwrite* is false.
        OSError: If the image cannot be written.
    """
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")

    try:
        image.save(path, format="PNG")
    except Exception as exc:
        raise OSError(f"Failed to write PNG: {exc}") from exc
    return path


def _stage_on_android(image, filename: str) -> str:
    """Write *image* into the app's own files area and return its path."""
    base = _android_external_files_dir()
    if not base:
        # Extremely defensive: fall back to Kivy's private data directory.
        try:
            from kivy.app import App  # noqa: PLC0415

            base = App.get_running_app().user_data_dir
        except Exception:
            base = os.getcwd()
    path = os.path.join(base, _EXPORT_SUBDIR, filename)
    return write_png(image, path, overwrite=True)


def export_png(
    path: str,
    config: Optional[PaperConfig] = None,
    overwrite: bool = False,
    destination_uri: Optional[str] = None,
    publish: bool = True,
) -> str:
    """Render a page and save it as a PNG at *path*.

    On desktop the image is written directly to *path*.

    On Android, *path* is treated as a *name* (only its basename is used):
    the PNG is staged inside the app's own files directory and then made
    available to the user through one of the sanctioned scoped-storage
    routes:

    * *destination_uri* -- a content URI previously granted by the Storage
      Access Framework create-document picker; the PNG is copied there.
    * otherwise, when *publish* is true -- the PNG is inserted into the
      public MediaStore Downloads collection, so it shows up in the user's
      Downloads folder.

    Pass ``publish=False`` to keep the file in the app directory only; the
    UI uses this to stage a PNG before launching the SAF picker.

    Args:
        path: Destination path (desktop) or file name (Android).
        config: Page geometry; defaults to standard JIS B5 at 300 DPI.
        overwrite: Off-Android, whether an existing *path* may be replaced.
        destination_uri: Optional SAF/MediaStore content URI to write into.
        publish: Whether to publish to Downloads on Android.

    Returns:
        Where the user can access the result: the destination URI, the
        ``content://`` URI of the new Downloads entry, or the staged file
        path when no publishing was requested or possible.

    Raises:
        FileExistsError: Off-Android, if the target exists and *overwrite*
            is false.
        OSError: If the image cannot be written anywhere.
    """
    if config is None:
        config = PaperConfig()
    img = render_page(config)

    if not _running_on_android():
        return write_png(img, path, overwrite=overwrite)

    from . import android_export  # noqa: PLC0415 - device-only logic lives here

    staged = _stage_on_android(img, os.path.basename(path))

    if destination_uri:
        try:
            return android_export.write_png_to_uri(destination_uri, staged)
        except Exception:
            pass  # fall through to the Downloads publication below

    if publish:
        try:
            return android_export.save_to_downloads(staged)
        except Exception:
            # Even MediaStore failed (rare).  The staged copy still exists;
            # callers can offer ACTION_SEND sharing via share_file(staged).
            pass
    return staged
