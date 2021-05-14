import carb
import omni
import omni.ui as ui

from pathlib import Path

from .style import *


class ToolBarUtilities(omni.ui.ToolBar):
    def __init__(self, icon_path, btn_dict):

        self._style = TOOLBAR
        self._visible = True

        self._toolbar = None
        self.icon_path = icon_path
        self.btn_dict = btn_dict

        # dictionary of named models used for any live ui elements
        self._models = {}

        self.build_ui()

    def build_ui(self):
        w = ui.Pixel(40)
        h = ui.Pixel(2 * w)
        dock_preference = ui.DockPreference.RIGHT

        self._toolbar = ui.ToolBar("Isaac Utilities Toolbar", noTabBar=False)
        with self._toolbar.frame:
            with ui.VStack(style=self._style, height=h):
                tb_width = 75
                icon_size = 25

                # Tray Open/Close Button
                with ui.HStack(width=tb_width):
                    ui.Spacer(width=ui.Pixel(2 * icon_size))

                    image_url = str(self.icon_path.joinpath("tray_close.png"))
                    self._models["visibility"] = ui.Button(
                        name="Visibility",
                        width=icon_size,
                        height=icon_size,
                        image_url=image_url,
                        alignment=ui.Alignment.RIGHT_CENTER,
                        style=self._style,
                        tooltip="Show/Hide",
                    )

                # Main Utilities Navigation Buttons
                ui.Separator()
                for group in self.btn_dict:
                    self._models[group] = ui.ToolButton(
                        name="main",
                        text=group,
                        width=tb_width,
                        height=icon_size,
                        alignment=ui.Alignment.CENTER,
                        style=self._style,
                        tooltip=(group + " Utilities"),
                    ).model
                    ui.Separator(name="separator")

    def clean(self):
        """Should be called when the extesion us unloaded or reloaded"""
        # Unfortunatley, the member variables are not destroyed when the extension is unloaded. We need to do it
        # automatically. Usually, it's OK because the Python garbage collector will eventually destroy everythigng. But
        # we need the images to be destroyed right now because Kit know nothing about Python garbage collector and it
        # will fire warning that texture is not destroyed.
        self._models = []
        self._toolbar = None
