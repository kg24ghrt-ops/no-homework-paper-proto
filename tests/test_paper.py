"""Tests for the No Homework notebook paper prototype."""

import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from no_homework.config import PaperConfig
from no_homework.export import export_png
from no_homework.paper import render_page

# JIS B5 at 300 DPI, in pixels.
B5_PX = (2150, 3035)


class TestConfig(unittest.TestCase):
    def test_jis_b5_pixels(self):
        c = PaperConfig()
        self.assertEqual((c.width_px, c.height_px), B5_PX)
        self.assertEqual(c.export_size, B5_PX)
        self.assertAlmostEqual(c.aspect_ratio, 0.7082, places=3)

    def test_mm_to_px(self):
        c = PaperConfig(dpi=300)
        self.assertEqual(c.mm_to_px(25.4), 300)  # one inch -> dpi pixels
        self.assertAlmostEqual(c.px_per_mm, 300 / 25.4)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            PaperConfig(width_mm=0)
        with self.assertRaises(ValueError):
            PaperConfig(dpi=0)
        # render should also reject a hand-mutated invalid config
        c = PaperConfig()
        object.__setattr__(c, "dpi", 0)
        with self.assertRaises(ValueError):
            render_page(c)

    def test_invalid_margins_rejected(self):
        with self.assertRaises(ValueError):
            PaperConfig(margin_left_mm=-1.0)
        with self.assertRaises(ValueError):
            PaperConfig(margin_top_mm=-5.0)
        # Margins that leave no drawable text area are rejected too.
        with self.assertRaises(ValueError):
            PaperConfig(margin_top_mm=200.0, margin_bottom_mm=60.0)  # >= 257 mm tall
        with self.assertRaises(ValueError):
            PaperConfig(margin_left_mm=182.0)  # == page width


class TestColorValidation(unittest.TestCase):
    def test_out_of_range_components_rejected(self):
        with self.assertRaises(ValueError):
            PaperConfig(paper_color=(300, 0, 0))
        with self.assertRaises(ValueError):
            PaperConfig(ruling_color=(0, -1, 0))

    def test_wrong_shape_or_type_rejected(self):
        with self.assertRaises(ValueError):
            PaperConfig(margin_line_color=(0, 0))  # not an RGB triple
        with self.assertRaises(ValueError):
            PaperConfig(paper_color="blue")  # not a tuple
        with self.assertRaises(ValueError):
            PaperConfig(ruling_color=(0.5, 0.5, 0.5))  # non-integer components

    def test_boundary_values_accepted(self):
        c = PaperConfig(paper_color=(0, 0, 0), ruling_color=(255, 255, 255))
        self.assertEqual(c.paper_color, (0, 0, 0))


class TestLineSpacingPixels(unittest.TestCase):
    def test_converted_line_spacing_at_least_one_pixel(self):
        # Any positive line spacing converts to at least one pixel, even at
        # an extremely low DPI where plain rounding would produce zero.
        c = PaperConfig(dpi=1, line_spacing_mm=0.05)
        self.assertGreaterEqual(c.mm_to_px(c.line_spacing_mm), 1)
        c.validate()  # must not raise

    def test_zero_lengths_convert_to_zero_pixels(self):
        c = PaperConfig(dpi=1)
        self.assertEqual(c.mm_to_px(0.0), 0)
        # A zero line spacing means "no ruling" and stays legal.
        PaperConfig(line_spacing_mm=0.0)

    def test_rounding_boundary_accepted(self):
        # 0.1 mm at 1 DPI rounds up to exactly one pixel -> valid config.
        c = PaperConfig(dpi=1, line_spacing_mm=0.1)
        self.assertEqual(c.mm_to_px(c.line_spacing_mm), 1)
        img = render_page(c)
        self.assertGreater(img.height, 0)

    def test_render_with_subpixel_spacing_does_not_crash(self):
        # The classic failure: at 72 DPI, 0.05 mm rounded to zero pixels and
        # range() raised "arg 3 must not be zero".  Now the converted spacing
        # is at least one pixel and rendering succeeds.
        c = PaperConfig(dpi=72, line_spacing_mm=0.05)
        img = render_page(c)
        self.assertEqual(img.mode, "RGB")

    def test_render_never_gets_zero_spacing(self):
        # Defense in depth: even if validation were bypassed entirely, the
        # drawing code guards the range() step with max(1, ...) and renders.
        import no_homework.config as config_module

        c = PaperConfig(dpi=72)
        object.__setattr__(c, "line_spacing_mm", 0.0)  # raw conversion is 0 px

        original = config_module.PaperConfig.validate
        try:
            config_module.PaperConfig.validate = lambda self: None
            img = render_page(c)
        finally:
            config_module.PaperConfig.validate = original
        self.assertEqual(img.mode, "RGB")


class TestRender(unittest.TestCase):
    def test_dimensions_and_mode(self):
        img = render_page()
        self.assertEqual(img.size, B5_PX)
        self.assertEqual(img.mode, "RGB")

    def test_paper_color_and_ruling(self):
        c = PaperConfig()
        img = render_page(c)
        margin_x = c.mm_to_px(c.margin_left_mm)
        first_line_y = c.mm_to_px(c.margin_top_mm)
        # Top-left corner is plain paper.
        self.assertEqual(img.getpixel((2, 2)), c.paper_color)
        # The red margin line and the first ruling line are where expected.
        self.assertEqual(img.getpixel((margin_x, first_line_y + 5)), c.margin_line_color)
        self.assertEqual(img.getpixel((margin_x + 50, first_line_y)), c.ruling_color)


class TestExport(unittest.TestCase):
    def test_export(self):
        with tempfile.TemporaryDirectory() as d:
            path = export_png(os.path.join(d, "out.png"))
            self.assertTrue(path.endswith("out.png"))
            with Image.open(path) as im:
                self.assertEqual(im.format, "PNG")
                self.assertEqual(im.size, B5_PX)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.png")
            export_png(path)
            with self.assertRaises(FileExistsError):
                export_png(path)
            export_png(path, overwrite=True)  # allowed with overwrite

    def test_missing_dir(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "out.png"
            export_png(str(path))
            self.assertTrue(path.exists())

    def test_write_failure(self):
        # Point at a path whose parent is an existing *file*, so the PNG
        # cannot be written regardless of platform/permissions.
        with tempfile.TemporaryDirectory() as d:
            blocker = os.path.join(d, "blocker")
            with open(blocker, "w"):
                pass
            with self.assertRaises(OSError):
                export_png(os.path.join(blocker, "out.png"), overwrite=True)


if __name__ == "__main__":
    unittest.main()
