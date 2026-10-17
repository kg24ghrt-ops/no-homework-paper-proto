"""Entry point for the No Homework notebook paper prototype."""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Texture
from kivy.utils import platform

from no_homework.config import PaperConfig
from no_homework.paper import render_page
from no_homework.export import export_png

KV = '''
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
'''


class NotebookRoot(BoxLayout):
    pass


class NotebookApp(App):
    def build(self):
        self.title = 'No Homework Notebook'
        self.root = Builder.load_string(KV)
        self.config = PaperConfig()
        self.image = render_page(self.config)
        self.preview = self.root.ids.preview
        self.status = self.root.ids.status
        self.regen_btn = self.root.ids.regen_btn
        self.export_btn = self.root.ids.export_btn
        self._update_preview()
        self.regen_btn.bind(on_press=self.regenerate)
        self.export_btn.bind(on_press=self.export)
        return self.root

    def _update_preview(self):
        from PIL import Image as PILImage
        preview = self.image.resize((int(self.image.width * 0.25), int(self.image.height * 0.25)))
        data = preview.tobytes()
        texture = Texture.create(size=preview.size, colorfmt="rgb")
        texture.blit_buffer(data, colorfmt="rgb", bufferfmt="ubyte")
        self.preview.texture = texture

    def regenerate(self, *args):
        self.image = render_page(self.config)
        self._update_preview()
        self.status.text = 'Page regenerated'

    def export(self, *args):
        try:
            path = export_png('no_homework.png', self.config, overwrite=True)
            self.status.text = f'Exported: {path}'
        except Exception as exc:
            self.status.text = f'Error: {exc}'


def main() -> None:
    NotebookApp().run()


if __name__ == "__main__":
    main()
