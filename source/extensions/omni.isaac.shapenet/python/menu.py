import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, rebuild_menus, MenuItemDescription
import weakref
from .login import ShapenetLogin
from .settings import ShapenetSettings
from .globals import *
from pathlib import Path

EXTENSION_NAME = "ShapeNet Loader"


class ShapenetMenu:
    def __init__(self, icon_path):
        self._settings_window = None
        self._login_window = None
        self.icon_path = icon_path

        self._sub_menu = []
        if pickle_file_exists():
            self._sub_menu.append(
                MenuItemDescription(
                    name="Add a model", onclick_fn=lambda a=weakref.proxy(self): a._on_settings_menu_click()
                )
            )
        else:
            self._sub_menu.append(
                MenuItemDescription(
                    name="Create Model ID Database",
                    onclick_fn=lambda a=weakref.proxy(self): a._on_create_database_click(),
                )
            )

        self._menu_items = [MenuItemDescription(name=EXTENSION_NAME, sub_menu=self._sub_menu)]
        add_menu_items(self._menu_items, "Isaac Utils")

        self._on_create_database_click()

    def _on_create_database_click(self):
        if self._login_window != None:
            self._login_window.visible = True
        else:
            self._login_window = ShapenetLogin(self, self.icon_path)

    def _on_settings_menu_click(self):
        if self._settings_window != None:
            self._settings_window.visible = True
        else:
            self._settings_window = ShapenetSettings()

    def _hide_db_show_add(self):
        # hide the CREATE_DATABASE_MENU_ITEM, show the add model menu
        if pickle_file_exists():
            self._sub_menu[0] = MenuItemDescription(
                name="Add a model", onclick_fn=lambda a=weakref.proxy(self): a._on_settings_menu_click()
            )
            rebuild_menus()

    def shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._settings_window = None
        self._login_window = None
