"""Kivy front end for the No Homework notebook paper prototype."""

import os
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

# File name (or path, off-Android) the Export button writes to.
_EXPORT_NAME = "no_homework.png"

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

        Button:
            id: save_as_btn
            text: 'Save As...'
            background_normal: ''
            background_color: 0.86, 0.55, 0.20, 1
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
    """Small desktop/Android UI to preview and export the generated page.

    Export behaviour differs per platform (see :mod:`no_homework.export`
    and :mod:`no_homework.android_export`):

    * Desktop: "Export PNG" writes straight to ``no_homework.png``;
      "Save As..." opens a native file chooser.
    * Android: "Export PNG" publishes the page into the system Downloads
      collection through MediaStore -- no permissions, and the file lands
      where users expect it.  If that is impossible, the PNG is handed to
      the share sheet instead.  "Save As..." launches the Storage Access
      Framework document picker so the user chooses any destination; the
      picked URI is written when the app resumes (``on_resume``).
    """

    def __init__(self, config: Optional[PaperConfig] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or PaperConfig()
        self.image: Optional[PILImage.Image] = None
        self._save_requester = None  # created lazily in build()

    def build(self) -> NotebookRoot:
        self.title = "No Homework Notebook"
        root: NotebookRoot = Builder.load_string(KV)
        self.root = root
        self.image = render_page(self.config)
        self._update_preview()
        root.ids.regen_btn.bind(on_press=self.regenerate)
        root.ids.export_btn.bind(on_press=self.export)
        root.ids.save_as_btn.bind(on_press=self.save_as)
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

    @staticmethod
    def _is_android() -> bool:
        try:
            from kivy.utils import platform

            return platform == "android"
        except Exception:
            return False

    def _requester(self):
        """Lazily build the SAF result collector for this app."""
        if self._save_requester is None:
            from no_homework.android_export import SaveRequester

            self._save_requester = SaveRequester(self._on_picked_uri_saved)
        return self._save_requester

    def _on_picked_uri_saved(self, target: str) -> None:
        if target.startswith("Error:"):
            self._set_status(target)
        else:
            from no_homework.android_export import STATUS_SAVED_PICKED

            self._set_status(f"{STATUS_SAVED_PICKED}: {target}")

    # Event callbacks ------------------------------------------------------

    def regenerate(self, *_args) -> None:
        self.image = render_page(self.config)
        self._update_preview()
        self._set_status("Page regenerated")

    def export(self, *_args) -> None:
        """One-tap export to a place the user can find.

        On Android this publishes into Downloads (MediaStore); if the whole
        scoped-storage route fails, the share sheet is opened as fallback.
        Off-Android it simply writes the file next to the app.
        """
        if not self._is_android():
            self._export_desktop()
            return

        # Cancel any half-finished "Save As..." request: this tap means the
        # user changed their mind about picking a destination.
        if self._save_requester is not None:
            self._save_requester.cancel()

        try:
            staged = export_png(_EXPORT_NAME, self.config, publish=False)
        except Exception as exc:
            self._set_status(f"Error: {exc}")
            return

        from no_homework import android_export

        try:
            target = android_export.save_to_downloads(staged)
        except Exception:
            # Even MediaStore failed; the share sheet still gets the file
            # out of the app sandbox to wherever the user wants it.
            if android_export.share_file(staged):
                self._set_status(
                    f"{android_export.STATUS_SHARED}: pick an app to save or send"
                )
            else:
                self._set_status(f"Exported (app storage only): {staged}")
        else:
            self._set_status(
                f"{android_export.STATUS_SAVED_DOWNLOADS}: {_EXPORT_NAME}"
            )

    def _export_desktop(self) -> None:
        try:
            path = export_png(_EXPORT_NAME, self.config, overwrite=True)
        except Exception as exc:  # surface any failure in the status bar
            self._set_status(f"Error: {exc}")
        else:
            self._set_status(f"Exported: {path}")

    def save_as(self, *_args) -> None:
        """Let the user choose the destination themselves."""
        if self._is_android():
            self._save_as_android()
        else:
            self._save_as_desktop()

    def _save_as_android(self) -> None:
        from no_homework.export import export_png as _export

        # Stage the PNG inside the app directory first (publish=False), then
        # hand the user the SAF picker; the copy happens on resume.
        try:
            staged = _export(_EXPORT_NAME, self.config, publish=False)
        except Exception as exc:
            self._set_status(f"Error: {exc}")
            return
        name = self._requester().start(staged)
        if name is None:
            # Picker unavailable: fall back to direct Downloads publication.
            self.export()
        else:
            self._set_status("Choose where to save the PNG...")

    def _save_as_desktop(self) -> None:
        try:
            from kivy.uix.filechooser import FileChooserListView  # noqa: F401
        except Exception:
            self._set_status("File chooser unavailable; used Export instead")
            self.export()
            return

        from kivy.uix.popup import Popup

        chooser = FileChooserListView(path=os.getcwd(), filters=[_EXPORT_NAME])
        popup = Popup(
            title="Save PNG as",
            content=chooser,
            size_hint=(0.9, 0.9),
        )

        def submit(*_args) -> None:
            selection = chooser.selection
            popup.dismiss()
            if not selection:
                return
            target = selection[0]
            if os.path.isdir(target):
                target = os.path.join(target, _EXPORT_NAME)
            try:
                path = export_png(target, self.config, overwrite=True)
            except Exception as exc:
                self._set_status(f"Error: {exc}")
            else:
                self._set_status(f"Exported: {path}")

        chooser.on_touch_up = lambda *_a: None  # keep popup open on scroll
        ok = BoxLayout(size_hint_y=None, height="50dp")
        ok.add_widget(_popup_button("Save", submit))
        ok.add_widget(_popup_button("Cancel", popup.dismiss))
        container = BoxLayout(orientation="vertical")
        container.add_widget(chooser)
        container.add_widget(ok)
        popup.content = container
        popup.open()

    # Lifecycle ------------------------------------------------------------

    def on_resume(self) -> None:
        """Collect a pending SAF picker result after 'Save As...'."""
        if self._save_requester is not None:
            self._save_requester.handle_resume()


def _popup_button(text: str, on_press) -> "object":
    from kivy.uix.button import Button

    return Button(text=text, bold=True, on_press=on_press)


def main() -> None:
    NotebookApp().run()


if __name__ == "__main__":
    main()
