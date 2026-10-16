import os
import tempfile
import unittest

from no_homework.config import PaperConfig
from no_homework.paper import render_page
from no_homework.export import export_png


class TestConfig(unittest.TestCase):
    def test_jis_b5_pixels(self):
        c = PaperConfig()
        self.assertEqual(c.width_px(), 2150)
        self.assertEqual(c.height_px(), 3035)
        self.assertAlmostEqual(c.aspect_ratio(), 0.7082, places=3)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            PaperConfig(width_mm=0)
        # render should reject
        with self.assertRaises(ValueError):
            render_page(PaperConfig(dpi=0))


class TestRender(unittest.TestCase):
    def test_dimensions_and_mode(self):
        img = render_page()
        self.assertEqual(img.size, (2150, 3035))
        self.assertEqual(img.mode, "RGB")

    def test_export(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.png")
            export_png(path)
            from PIL import Image
            with Image.open(path) as im:
                self.assertEqual(im.format, "PNG")
                self.assertEqual(im.size, (2150, 3035))

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.png")
            export_png(path)
            with self.assertRaises(FileExistsError):
                export_png(path)

    def test_missing_dir(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "out.png")
            export_png(path)
            self.assertTrue(os.path.exists(path))

    def test_write_failure(self):
        with self.assertRaises(IOError):
            export_png("/nonexistent_root_dir/x/out.png", overwrite=True)


if __name__ == "__main__":
    unittest.main()
