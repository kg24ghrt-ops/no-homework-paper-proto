from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.image import Texture
from kivy.graphics.texture import Texture as KTexture

from no_homework.config import PaperConfig
from no_homework.paper import render_page
from no_homework.export import export_png


class NotebookApp(App):
    def build(self):
        self.config = PaperConfig()
        self.image = render_page(self.config)
        layout = BoxLayout(orientation="vertical")
        self.preview = KivyImage(size_hint=(1, 0.8))
        self._update_preview()
        regen = Button(text="Regenerate")
        regen.bind(on_press=self.regenerate)
        export = Button(text="Export PNG")
        export.bind(on_press=self.export)
        status = Label(text="Ready", size_hint=(1, 0.1))
        self.status = status
        layout.add_widget(self.preview)
        layout.add_widget(regen)
        layout.add_widget(export)
        layout.add_widget(status)
        return layout

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
        self.status.text = "Regenerated"

    def export(self, *args):
        try:
            path = export_png("/sdcard/no_homework.png", self.config, overwrite=True)
            self.status.text = f"Exported: {path}"
        except Exception as exc:
            self.status.text = f"Error: {exc}"
