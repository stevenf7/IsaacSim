import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import carb
from .extension import *
import weakref

EXTENSION_NAME = "Exploded View"


class Exploded_view(omni.ext.IExt):
    """
    Exploded view basit UI example
    """

    def on_startup(self):
        carb.log_info("Loading Exploded View Extension")
        self._exploded_view_manager = Exploded_view_manager()
        self._context = omni.usd.get_context()
        self._selection = self._context.get_selection()
        self._window = None

        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Window")

    def _menu_callback(self):
        if self._window:
            self._window.visible = value
        elif value:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=500, height=300, visible=value, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )

            with self._window.frame:
                with ui.HStack():
                    with ui.VStack():
                        self._enable_explode_btn = ui.Button(
                            "Enable Explode View", clicked_fn=lambda: self.toggle_explode(), height=ui.Pixel(20)
                        )
                        self._add_prim_btn = ui.Button(
                            "Add Selected Prim", clicked_fn=lambda: self.add_selected_prim(), height=ui.Pixel(20)
                        )
                        self._disable_prim_btn = ui.Button(
                            "Disable Selected Prim",
                            clicked_fn=lambda: self.disable_selected_prim(),
                            height=ui.Pixel(20),
                        )
                        self._remove_prim_btn = ui.Button(
                            "Remove Selected Prim", clicked_fn=lambda: self.remove_selected_prim(), height=ui.Pixel(20)
                        )
                    with ui.VStack():
                        ui.Label("Explode Direction", height=ui.Pixel(20))
                        self._explode_direction_combo = ui.ComboBox(
                            4,
                            "Global Origin",
                            "Global X",
                            "Global Y",
                            "Global Z",
                            "Local Origin",
                            "Local X",
                            "Local Y",
                            "Local Z",
                            height=ui.Pixel(20),
                        )
                        ui.Label("Explode scale", height=ui.Pixel(20))
                        self.explode_scale_model = ui.SimpleFloatModel()
                        self.explode_scale_model.add_value_changed_fn(
                            lambda m: self._exploded_view_manager.explode(m.get_value_as_float())
                        )
                        self._explode_scale_slider = ui.FloatDrag(self.explode_scale_model, min=0, max=3.0)

    def toggle_explode(self):
        if self._exploded_view_manager.enabled:
            self._exploded_view_manager.disable()
            self._enable_explode_btn.text = "Enable Explode View"
        else:
            self._exploded_view_manager.enable()
            self._enable_explode_btn.text = "Disable Explode View"

    def add_selected_prim(self):
        stage = self._context.get_stage()
        prims = [stage.GetPrimAtPath(i) for i in self._selection.get_selected_prim_paths()]
        for prim in prims:
            self._exploded_view_manager.add_explode_view_item(
                prim, self._explode_direction_combo.model.get_item_value_model().as_int
            )

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Window")
        self._exploded_view_manager.shutdown()
