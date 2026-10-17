"""Kivy front end for the No Homework notebook paper prototype."""

from typing import Optional

from PIL import Image as PILImage
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from no_homework.config import PaperConfig
from no_homework.export import export_png
from no_homework.paper import render_page

# Fraction of full resolution used for the on-screen preview texture.
_PREVIEW_SCALE = 0.25

KV = """
<NotebookRoot>:
    orientation: 'vertical'
    spacing: dp(12)
    padding: dp(16)

    Label:
        text: 'No Homework Notebook'
        font_size: sp(26)
        bold: True
        color: 0.16, 0.40, 0.70, 1
        size_hint_y: None
        height: dp(44)
        halign: 'center'
        valign: 'middle'
        text_size: self.width, None

    Image:
        id: preview
        size_hint_y: 0.70
        allow_stretch: True
        keep_ratio: True

    BoxLayout:
        size_hint_y: None
        height: dp(66)
        spacing: dp(12)

        Button:
            id: regen_btn
            text: 'Regenerate Page'
            background_normal: ''
            background_color: 0.18, 0.50, 0.82, 1
            color: 1, 1, 1, 1
            font_size: sp(15)
            bold: True

        Button:
            id: export_btn
            text: 'Export PNG'
            background_normal: ''
            background_color: 0.22, 0.66, 0.32, 1
            color: 1, 1, 1, 1
            font_size: sp(15)
            bold: True

    Label:
        id: status
        text: 'Ready'
        size_hint_y: None
        height: dp(28)
        color: 0.60, 0.60, 0.60, 1
        font_size: sp(13)
        halign: 'center'
"""


class NotebookRoot(BoxLayout):
    """Root layout widget referenced by the KV string above."""


def _make_preview_texture(image: PILImage.Image):
    """Build a Kivy texture from a downscaled copy of *image*."""
    from kivy.core.image import Texture

    preview = image.resize(
        (int(image.width * _PREVIEW_SCALE), int(image.height * _PREVIEW_SCALE))
    )
    texture = Texture.create(size=preview.size, colorfmt="rgb")
    texture.blit_buffer(preview.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
    return texture


class NotebookApp(App):
    """Small desktop/Android UI to preview and export the generated page."""

    def __init__(self, config: Optional[PaperConfig] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or PaperConfig()
        self.image: Optional[PILImage.Image] = None

    def build(self) -> NotebookRoot:
        self.title = "No Homework Notebook"
        root: NotebookRoot = Builder.load_string(KV)
        self.root = root
        self.image = render_page(self.config)
        self._update_preview()
        root.ids.regen_btn.bind(on_press=self.regenerate)
        root.ids.export_btn.bind(on_press=self.export)
        return root

    # Internal helpers -----------------------------------------------------

    @property
    def _preview_widget(self):
        return self.root.ids.preview

    @property
    def _status_widget(self):
        return self.root.ids.status

    def _update_preview(self) -> None:
        if self.image is not None:
            self._preview_widget.texture = _make_preview_texture(self.image)

    def _set_status(self, text: str) -> None:
        self._status_widget.text = text

    # Event callbacks ------------------------------------------------------

    def regenerate(self, *_args) -> None:
        self.image = render_page(self.config)
        self._update_preview()
        self._set_status("Page regenerated")

    def export(self, *_args) -> None:
        try:
            path = export_png("no_homework.png", self.config, overwrite=True)
        except Exception as exc:  # surface any failure in the status bar
            self._set_status(f"Error: {exc}")
        else:
            self._set_status(f"Exported: {path}")


def main() -> None:
    NotebookApp().run()


if __name__ == "__main__":
    main()
