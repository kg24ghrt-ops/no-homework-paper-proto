"""Tests for the Android export paths (MediaStore Downloads, SAF, sharing).

The real device code lives behind ``jnius``/``android`` imports; these tests
fake those modules and Kivy's platform flag so the full scoped-storage logic
can be exercised on any machine.
"""

import importlib
import os
import sys
import tempfile
import types
import unittest


def _install_android_stubs(platform_value="android"):
    """Register fake kivy/jnius/android modules; return the stub bundle."""
    saved = {}

    def fake(name, module):
        saved[name] = sys.modules.get(name)
        sys.modules[name] = module

    kivy = types.ModuleType("kivy")
    utils = types.ModuleType("kivy.utils")
    utils.platform = platform_value
    kivy.utils = utils
    fake("kivy", kivy)
    fake("kivy.utils", utils)

    jnius = types.ModuleType("jnius")
    jnius.autoclass = lambda name: _JavaStub(name)
    jnius.cast = lambda cls, obj: obj
    fake("jnius", jnius)

    android = types.ModuleType("android")
    activity_bus = types.ModuleType("android.activity")
    listeners = []
    activity_bus.register_event_listener = listeners.append
    android.activity = activity_bus
    fake("android", android)
    fake("android.activity", activity_bus)

    return saved, listeners


def _restore(saved):
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


class _JavaStub:
    """Minimal stand-in for autoclass()'d Java classes."""

    registry = {}  # per-test overrides: class name -> attribute mapping

    def __init__(self, name):
        self._name = name

    def __getattr__(self, item):
        overrides = _JavaStub.registry.get(self._name, {})
        if item in overrides:
            return overrides[item]
        raise AttributeError(f"{self._name}.{item}")

    def __call__(self, *args, **kwargs):
        overrides = _JavaStub.registry.get(self._name, {})
        factory = overrides.get("__call__")
        if factory is not None:
            return factory(*args, **kwargs)
        raise AttributeError(f"{self._name} is not constructible in this test")


class AndroidExportTestBase(unittest.TestCase):
    def setUp(self):
        (
            self._saved_modules,
            self._listeners,
        ) = _install_android_stubs()
        _JavaStub.registry = {}
        for name in (
            "no_homework.android_export",
            "no_homework.export",
        ):
            sys.modules.pop(name, None)
        self.android_export = importlib.import_module(
            "no_homework.android_export"
        )
        self.export = importlib.import_module("no_homework.export")

    def tearDown(self):
        for name in (
            "no_homework.android_export",
            "no_homework.export",
        ):
            sys.modules.pop(name, None)
        _restore(self._saved_modules)

    def make_png(self, directory):
        from PIL import Image

        path = os.path.join(directory, "page.png")
        Image.new("RGB", (8, 8), (250, 245, 236)).save(path)
        return path


class TestPlatformGuard(AndroidExportTestBase):
    def test_off_device_helpers_are_inert(self):
        _restore(self._saved_modules)
        _install_android_stubs(platform_value="linux")
        # Re-import with the linux stub active.
        for name in ("no_homework.android_export", "no_homework.export"):
            sys.modules.pop(name, None)
        module = importlib.import_module("no_homework.android_export")
        with self.assertRaises(RuntimeError):
            module.save_to_downloads("/tmp/nonexistent.png")
        self.assertIsNone(module.pick_save_location("/tmp/nonexistent.png"))
        self.assertFalse(module.share_file("/tmp/nonexistent.png"))


class _FakeStream:
    """Stand-in for a Java OutputStream; records everything written."""

    instances = []

    def __init__(self):
        self.data = bytearray()
        self.closed = False
        _FakeStream.instances.append(self)

    def write(self, chunk):
        self.data.extend(chunk)

    def flush(self):
        pass

    def close(self):
        self.closed = True


class TestMediaStoreDownloads(AndroidExportTestBase):
    def setUp(self):
        super().setUp()
        _FakeStream.instances = []
    def _fake_api29_environment(self, writes):
        class Resolver:
            def query(self, uri, *args):
                return None

            def insert(self, uri, values):
                return UriObj()

            def openOutputStream(self, uri):
                return _FakeStream()

            def delete(self, uri, *args):
                writes.setdefault("deleted", []).append(uri)

            def update(self, uri, values, *args):
                writes["final_pending"] = values.items.get(
                    "IS_PENDING", "missing"
                )

        class Activity:
            def getContentResolver(self):
                return Resolver()

        class UriObj:
            def toString(self):
                return "content://media/downloads/1"

        _JavaStub.registry = {
            "android.os.Build$VERSION": {"SDK_INT": 29},
            "org.kivy.android.PythonActivity": {"mActivity": Activity()},
            "android.content.ContentValues": {
                "__call__": lambda: _ContentValues()
            },
            "android.provider.MediaStore$Downloads": {
                "Columns": _Columns(),
                "EXTERNAL_CONTENT_URI": UriObj(),
            },
            "android.net.Uri": {"parse": staticmethod(lambda s: UriObj())},
        }

    def test_save_to_downloads_inserts_and_clears_pending(self):
        writes = {}
        with tempfile.TemporaryDirectory() as d:
            png = self.make_png(d)
            with open(png, "rb") as handle:
                expected = handle.read()
            self._fake_api29_environment(writes)
            result = self.android_export.save_to_downloads(png)
        self.assertEqual(result, "content://media/downloads/1")
        self.assertEqual(writes["final_pending"], 0)
        stream = _FakeStream.instances[-1]
        self.assertEqual(bytes(stream.data), expected)  # byte-exact copy
        self.assertTrue(stream.closed)

    def test_failed_stream_deletes_empty_entry(self):
        writes = {}
        with tempfile.TemporaryDirectory() as d:
            png = self.make_png(d)
            self._fake_api29_environment(writes)

            class BrokenStream(_FakeStream):
                def write(self, chunk):
                    raise IOError("disk full")

            resolver = _JavaStub.registry[
                "org.kivy.android.PythonActivity"
            ]["mActivity"].getContentResolver()
            resolver.openOutputStream = lambda uri: BrokenStream()
            with self.assertRaises(OSError):  # IOError is an OSError alias
                self.android_export.save_to_downloads(png)
        self.assertIn("deleted", writes)
        self.assertNotIn("final_pending", writes)  # entry never finalized


class _ContentValues:
    def __init__(self):
        self.items = {}

    def put(self, key, value):
        self.items[str(key)] = value

    def clear(self):
        self.items.clear()


class _Columns:
    DISPLAY_NAME = "DISPLAY_NAME"
    MIME_TYPE = "MIME_TYPE"
    RELATIVE_PATH = "RELATIVE_PATH"
    IS_PENDING = "IS_PENDING"


class _FakeIntent:
    """Stand-in for android.content.Intent instances."""

    def addCategory(self, category):
        pass

    def setType(self, mime):
        pass

    def putExtra(self, key, value):
        pass


class TestSaveRequester(AndroidExportTestBase):
    def _fake_picker(self, launched):
        class Activity:
            def startActivityForResult(self, intent, code):
                launched.append(code)

        _JavaStub.registry = {
            "org.kivy.android.PythonActivity": {"mActivity": Activity()},
            "android.content.Intent": {
                "ACTION_CREATE_DOCUMENT": "CREATE",
                "CATEGORY_OPENABLE": "OPENABLE",
                "EXTRA_TITLE": "TITLE",
                "__call__": lambda action: _FakeIntent(),
            },
        }

    def test_start_registers_result_listener(self):
        launched = []
        self._fake_picker(launched)
        reporter = []
        requester = self.android_export.SaveRequester(reporter.append)
        name = requester.start("/tmp/page.png")
        self.assertEqual(name, "page.png")
        self.assertEqual(launched, [self.android_export.SAVE_REQUEST_CODE])
        self.assertTrue(requester.pending)
        self.assertIn(
            self.android_export.on_activity_result, self._listeners
        )

    def test_resume_writes_chosen_uri(self):
        launched = []
        self._fake_picker(launched)
        reporter = []
        requester = self.android_export.SaveRequester(reporter.append)

        written = {}

        def fake_write(uri, source):
            written["uri"] = uri
            return uri

        self.android_export.write_png_to_uri = fake_write
        requester.start("/tmp/page.png")

        # A resume without a result must not consume anything.
        self.assertFalse(requester.handle_resume())
        self.assertTrue(requester.pending)

        # Simulate the Java-side callback delivering the picked URI.
        class Data:
            def toString(self):
                return "content://picked/42"

        class IntentResult:
            def getData(self):
                return Data()

        self.android_export.on_activity_result(
            self.android_export.SAVE_REQUEST_CODE, -1, IntentResult()
        )
        self.assertTrue(requester.handle_resume())
        self.assertEqual(written["uri"], "content://picked/42")
        self.assertEqual(reporter, ["content://picked/42"])
        self.assertFalse(requester.pending)

    def test_cancelled_picker_is_not_written(self):
        launched = []
        self._fake_picker(launched)
        reporter = []
        requester = self.android_export.SaveRequester(reporter.append)
        requester.start("/tmp/page.png")
        # RESULT_CANCELED == 0
        self.android_export.on_activity_result(
            self.android_export.SAVE_REQUEST_CODE, 0, None
        )
        self.assertFalse(requester.handle_resume())
        self.assertEqual(reporter, [])
        self.assertFalse(requester.pending)

    def test_other_request_codes_ignored(self):
        self.android_export.on_activity_result(999, -1, None)
        self.assertNotIn(999, self.android_export._LAST_RESULTS)


class TestExportAndroidFlow(AndroidExportTestBase):
    def _fake_stage_dir(self, directory):
        class FilesDir:
            def getAbsolutePath(self):
                return directory

        class Activity:
            def getExternalFilesDir(self, _type):
                return FilesDir()

        _JavaStub.registry["org.kivy.android.PythonActivity"] = {
            "mActivity": Activity()
        }

    def test_publishes_to_downloads_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            self._fake_stage_dir(d)
            published = {}

            def fake_save(path, display_name=None):
                published["path"] = path
                return "content://media/downloads/7"

            self.android_export.save_to_downloads = fake_save
            result = self.export.export_png("whatever.png")
            self.assertEqual(result, "content://media/downloads/7")
            self.assertTrue(published["path"].endswith("whatever.png"))
            self.assertTrue(os.path.exists(published["path"]))

    def test_destination_uri_route(self):
        with tempfile.TemporaryDirectory() as d:
            self._fake_stage_dir(d)
            calls = []

            def fake_write(uri, path):
                calls.append((uri, path))
                return uri

            self.android_export.write_png_to_uri = fake_write
            result = self.export.export_png(
                "paper.png", destination_uri="content://picked/1"
            )
            self.assertEqual(result, "content://picked/1")
            self.assertEqual(calls[0][0], "content://picked/1")

    def test_publish_false_keeps_file_in_app_dir(self):
        with tempfile.TemporaryDirectory() as d:
            self._fake_stage_dir(d)
            result = self.export.export_png("paper.png", publish=False)
            self.assertEqual(result, os.path.join(d, "exports", "paper.png"))
            self.assertTrue(os.path.exists(result))

    def test_download_failure_returns_staged_path(self):
        with tempfile.TemporaryDirectory() as d:
            self._fake_stage_dir(d)

            def boom(path, display_name=None):
                raise RuntimeError("MediaStore unavailable")

            self.android_export.save_to_downloads = boom
            result = self.export.export_png("paper.png")
            self.assertTrue(result.endswith(os.path.join("exports", "paper.png")))
            self.assertTrue(os.path.exists(result))


if __name__ == "__main__":
    unittest.main()
