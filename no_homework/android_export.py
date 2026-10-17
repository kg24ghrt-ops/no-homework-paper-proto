"""Android-friendly PNG export via MediaStore Downloads and the SAF picker.

Scoped storage (Android 10 / API 29+) blocks direct writes to shared
locations such as ``/sdcard/Download``.  Redirecting exports into the app's
private external-files directory avoids permission errors but leaves users
with a file they can hardly find.  This module provides two proper,
permission-free ways to save a page where the user can actually see it:

* :func:`save_to_downloads` -- publishes the PNG into the system *Downloads*
  collection through ``MediaStore``, so it shows up in the user's Downloads
  folder (Files app, gallery, other apps) immediately.  On API < 29 it falls
  back to a plain file write into the public Download directory plus a
  media scan.
* :func:`pick_save_location` -- launches the Storage Access Framework
  ``ACTION_CREATE_DOCUMENT`` picker so the user chooses the destination
  themselves (any folder, SD card, or cloud provider).  The result arrives
  asynchronously; Kivy delivers it when the app resumes, which is what the
  :class:`SaveRequester` helper wires up.

When neither path works, :func:`share_file` hands the PNG to another app
(mail, Drive, messaging, ...) through an ``ACTION_SEND`` chooser -- a
user-visible fallback that never needs storage permissions.

All helpers are inert off-device: platform checks keep ``jnius`` imports out
of desktop runs, so importing this module anywhere is safe.
"""

from __future__ import annotations

import os
import time
from typing import Callable, Dict, Optional

PNG_MIME_TYPE = "image/png"

#: Request code used for the SAF ``CREATE_DOCUMENT`` activity result.
SAVE_REQUEST_CODE = 54_321

# Status messages shared with the UI layer.
STATUS_SAVED_DOWNLOADS = "Saved to Downloads"
STATUS_SAVED_PICKED = "Saved to your chosen location"
STATUS_SHARED = "Shared via Android"


def _running_on_android() -> bool:
    try:
        from kivy.utils import platform  # noqa: PLC0415 - Kivy may be absent

        return platform == "android"
    except Exception:
        return False


def _activity():
    """Return the current Java activity, or ``None`` off-device."""
    try:
        from jnius import autoclass  # noqa: PLC0415 - only available on Android

        return autoclass("org.kivy.android.PythonActivity").mActivity
    except Exception:
        return None


def _unique_filename(directory: str, filename: str) -> str:
    """Return a name for *filename* that does not clash inside *directory*.

    Keeps repeated exports from silently clobbering earlier copies.
    """
    candidate = os.path.join(directory, filename)
    if not os.path.exists(candidate):
        return filename
    stem, ext = os.path.splitext(filename)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{stem}-{stamp}{ext}"


def _copy_file(src: str, dst: str) -> None:
    with open(src, "rb") as source, open(dst, "wb") as target:
        while True:
            chunk = source.read(65536)
            if not chunk:
                break
            target.write(chunk)


def _stream_to(output_stream, png_path: str) -> None:
    """Copy *png_path* into a Java ``OutputStream``, closing both streams.

    PyJNIus converts Python ``bytes`` to Java ``byte[]`` transparently on
    method calls, so each 64 KiB chunk is handed straight to
    ``OutputStream.write(byte[])`` -- no manual signed-byte juggling.
    """
    try:
        with open(png_path, "rb") as source:
            while True:
                chunk = source.read(65536)
                if not chunk:
                    break
                output_stream.write(chunk)
    finally:
        output_stream.flush()
        output_stream.close()


# ---------------------------------------------------------------------------
# MediaStore -> public Downloads collection
# ---------------------------------------------------------------------------


def save_to_downloads(png_path: str, display_name: Optional[str] = None) -> str:
    """Publish an existing PNG into the system Downloads collection.

    Uses ``MediaStore.Downloads`` on Android 10+ (API 29+), which requires no
    storage permissions at all under scoped storage.  On older devices it
    writes into the public Download directory and triggers a media scan.

    Args:
        png_path: Absolute path of the PNG to publish.
        display_name: Name shown to the user; defaults to the basename of
            *png_path*.  Existing names are de-duplicated with a timestamp.

    Returns:
        The ``content://`` URI (API 29+) or absolute file path (legacy) of
        the saved copy.

    Raises:
        RuntimeError: If not running on Android or the publish fails.
    """
    if not _running_on_android():
        raise RuntimeError("MediaStore Downloads is only available on Android")

    from jnius import autoclass  # noqa: PLC0415

    name = display_name or os.path.basename(png_path)
    activity = _activity()
    if activity is None:
        raise RuntimeError("Could not obtain the Android activity")
    sdk_int = autoclass("android.os.Build$VERSION").SDK_INT

    if sdk_int >= 29:
        return _mediastore_insert(activity, png_path, name)

    # Legacy path (API < 29): direct write into the public Download dir.
    Environment = autoclass("android.os.Environment")
    downloads_dir = Environment.getExternalStoragePublicDirectory(
        Environment.DIRECTORY_DOWNLOADS
    ).getAbsolutePath()
    name = _unique_filename(downloads_dir, name)
    target = os.path.join(downloads_dir, name)
    _copy_file(png_path, target)
    autoclass("android.media.MediaScannerConnection").scanFile(
        activity, [target], [PNG_MIME_TYPE], None
    )
    return target


def _mediastore_insert(activity, png_path: str, name: str) -> str:
    """Insert *png_path* into ``MediaStore.Downloads`` (API 29+)."""
    from jnius import autoclass  # noqa: PLC0415

    ContentValues = autoclass("android.content.ContentValues")
    Downloads = autoclass("android.provider.MediaStore$Downloads")

    resolver = activity.getContentResolver()

    # De-duplicate against names already present in the collection.
    taken = set()
    cursor = resolver.query(
        Downloads.EXTERNAL_CONTENT_URI, None, None, None, None
    )
    if cursor is not None:
        try:
            index = cursor.getColumnIndexOrThrow(Downloads.Columns.DISPLAY_NAME)
            while cursor.moveToNext():
                taken.add(cursor.getString(index))
        finally:
            cursor.close()
    if name in taken:
        stem, ext = os.path.splitext(name)
        name = f"{stem}-{time.strftime('%Y%m%d-%H%M%S')}{ext}"

    values = ContentValues()
    values.put(Downloads.Columns.DISPLAY_NAME, name)
    values.put(Downloads.Columns.MIME_TYPE, PNG_MIME_TYPE)
    values.put(Downloads.Columns.RELATIVE_PATH, "Download")
    values.put(Downloads.Columns.IS_PENDING, 1)

    uri = resolver.insert(Downloads.EXTERNAL_CONTENT_URI, values)
    if uri is None:
        raise RuntimeError("MediaStore refused to create the Downloads entry")

    try:
        stream = resolver.openOutputStream(uri)
        if stream is None:
            raise RuntimeError("Could not open the MediaStore output stream")
        _stream_to(stream, png_path)
    except Exception:
        resolver.delete(uri, None, None)  # do not leave an empty entry behind
        raise

    values.clear()
    values.put(Downloads.Columns.IS_PENDING, 0)
    resolver.update(uri, values, None, None)
    return uri.toString()


# ---------------------------------------------------------------------------
# Storage Access Framework -> ACTION_CREATE_DOCUMENT picker
# ---------------------------------------------------------------------------

# Latest CREATE_DOCUMENT results waiting to be collected on resume, keyed by
# request code.  Value "" means the user cancelled the picker.
_LAST_RESULTS: Dict[int, str] = {}
_RESULT_LISTENER_REGISTERED = False


def on_activity_result(request_code: int, result_code: int, intent) -> None:
    """Record an activity result for later pickup by :class:`SaveRequester`.

    Registered as a listener on python-for-android's activity-result event
    bus (``android.activity.register_event_listener``); safe to call from
    the Java thread.
    """
    if request_code != SAVE_REQUEST_CODE:
        return
    if result_code != _RESULT_OK:  # Activity.RESULT_CANCELED (or other)
        _LAST_RESULTS[request_code] = ""
        return
    try:
        data = intent.getData() if intent is not None else None
        _LAST_RESULTS[request_code] = data.toString() if data is not None else ""
    except Exception:
        _LAST_RESULTS[request_code] = ""


_RESULT_OK = -1  # android.app.Activity.RESULT_OK


def _ensure_result_listener() -> bool:
    """Subscribe :func:`on_activity_result` to p4a's activity-result bus."""
    global _RESULT_LISTENER_REGISTERED

    if _RESULT_LISTENER_REGISTERED:
        return True
    try:
        from android import activity  # noqa: PLC0415 - device-only module

        activity.register_event_listener(on_activity_result)
    except Exception:
        return False
    _RESULT_LISTENER_REGISTERED = True
    return True


def pick_save_location(
    png_path: str, suggested_name: Optional[str] = None
) -> Optional[str]:
    """Open the SAF create-document picker for *png_path*.

    Renders nothing itself: *png_path* must already exist (see
    :func:`no_homework.export.export_png`).  The actual copy happens later,
    once the user has chosen a destination and the app resumes -- wire that
    up with :class:`SaveRequester`.

    Returns:
        The suggested document name on success, or ``None`` if the picker
        could not be launched (the caller should fall back to another route).
    """
    if not _running_on_android():
        return None
    if not _ensure_result_listener():
        return None
    activity = _activity()
    if activity is None:
        return None

    from jnius import autoclass  # noqa: PLC0415

    Intent = autoclass("android.content.Intent")
    name = suggested_name or os.path.basename(png_path)
    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType(PNG_MIME_TYPE)
    intent.putExtra(Intent.EXTRA_TITLE, name)
    try:
        activity.startActivityForResult(intent, SAVE_REQUEST_CODE)
    except Exception:
        return None
    return name


class SaveRequester:
    """Delivers the result of an SAF ``CREATE_DOCUMENT`` request.

    Android gives Python no way to block on ``startActivityForResult``, so
    the URI chosen by the system dialog is collected when the app resumes
    (the picker pauses our activity while it is up).  One instance per app;
    drive it from ``App.on_resume``.
    """

    def __init__(self, on_saved: Callable[[str], None]) -> None:
        self._on_saved = on_saved
        self._pending = False
        self._source_path = ""

    @property
    def pending(self) -> bool:
        return self._pending

    def start(self, source_png: str) -> Optional[str]:
        """Launch the picker for *source_png*; returns the suggested name.

        Marks the request pending only if the picker actually opened, so a
        failed launch never leaves stale state behind.
        """
        name = pick_save_location(source_png)
        if name is None:
            return None
        self._source_path = source_png
        self._pending = True
        return name

    def cancel(self) -> None:
        """Forget a pending request (e.g. the app was reset)."""
        self._pending = False
        _LAST_RESULTS.pop(SAVE_REQUEST_CODE, None)

    def handle_resume(self) -> bool:
        """Try to collect a pending picker result.

        Returns ``True`` if the PNG was written through the chosen URI.
        Never raises: write failures are reported through the callback with
        an ``"Error: ..."`` string.
        """
        if not self._pending:
            return False
        uri = _LAST_RESULTS.pop(SAVE_REQUEST_CODE, None)
        if uri is None:
            # App resumed for another reason; keep waiting for the result.
            return False
        self._pending = False
        if not uri:  # empty string => user cancelled the picker
            return False
        try:
            target = write_png_to_uri(uri, self._source_path)
        except Exception as exc:
            self._on_saved(f"Error: {exc}")
            return False
        self._on_saved(target)
        return True


def write_png_to_uri(uri_string: str, png_path: str) -> str:
    """Copy *png_path* into the SAF/MediaStore-granted *uri_string*.

    Returns the URI string that now holds the image.
    """
    from jnius import autoclass  # noqa: PLC0415

    Uri = autoclass("android.net.Uri")

    activity = _activity()
    if activity is None:
        raise RuntimeError("Android activity unavailable")
    resolver = activity.getContentResolver()
    output = resolver.openOutputStream(Uri.parse(uri_string))
    if output is None:
        raise RuntimeError("Picker returned a URI we cannot write to")
    _stream_to(output, png_path)
    return uri_string


# ---------------------------------------------------------------------------
# ACTION_SEND share sheet (fallback that always works without permissions)
# ---------------------------------------------------------------------------


def share_file(file_path: str) -> bool:
    """Hand *file_path* to another app through the Android share sheet.

    Wraps the PNG in an ``ACTION_SEND`` chooser ("Save notebook paper"), so
    even when saving in place is impossible the user can push the image to
    Drive, mail, Messages, or any other handler -- no permissions required.

    Returns:
        ``True`` if the chooser was launched successfully.
    """
    if not _running_on_android():
        return False
    activity = _activity()
    if activity is None:
        return False

    from jnius import autoclass  # noqa: PLC0415

    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")

    uri = Uri.fromFile(autoclass("java.io.File")(file_path))
    if uri is None:
        return False

    send = Intent(Intent.ACTION_SEND)
    send.setType(PNG_MIME_TYPE)
    send.putExtra(Intent.EXTRA_STREAM, uri)
    send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    try:
        activity.startActivity(Intent.createChooser(send, "Save notebook paper"))
    except Exception:
        return False
    return True
