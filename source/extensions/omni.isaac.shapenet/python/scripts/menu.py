import carb
import carb.input
import omni.kit.editor
import omni.kit.ui
import omni.kit.commands
import omni.usd
import random
import json
import sys
from pxr import Usd, UsdGeom, Sdf, Gf, Tf
import omni.isaac.shapenet
import asyncio
from .login import ShapenetLogin
from .settings import ShapenetSettings
from .globals import *

CREATE_DATABASE_MENU_ITEM = "ShapeNet/Create Model ID Database"
SETTINGS_MENU_ITEM = "ShapeNet/Add a model"
HELP_MENU_ITEM = "ShapeNet/Help"
SHAPENET_MENU_ITEM = "ShapeNet"
#   "Keep Help text the width of this line or shorter -------------------------------",
ADD_DB_TEXT = [
    "    Please register an account at https://www.shapenet.org/ so you can make the",
    "database of ShapeNetCore.V1 csv files necessary to run this extension.  Once you",
    "have a validate shapenet.org login, use the menu to create the database.  You",
    "should only have to do this once.",
]

HELP_TEXT = [
    "    This omni.isaac.shapenet plugin allows you to add ShapeNetCore.V2 models ",
    "from shapenet.org to your stage in Omniverse Kit.",
    "",
    "You can use the ShapeNet menu to add shapes.",
    "",
    "You can also use an external python session to send json formatted commands via",
    "http and load shapes with comm_kit.py.",
    "",
    "See comm_kit.test_comm() or run:",
    "\t>  jupyter notebook ShapeNet Python Example.ipynb",
    "for examples.",
    "",
    "If you already have ShapeNetCore V2 installed locally, this plugin can use the",
    "local files.  Use the env var SHAPENET_LOCAL_DIR to set that location (IMPORTANT",
    "NOTE: Make sure there are no periods, ., in the path name), otherwise, ",
    "omni.isaac.shapenet will use the default ${data}/shapenet folder.  By using",
    "local folders, you can edit shapenet models before their conversion to usd.  If",
    "you want to keep the original file, just save the modified file as ",
    ' "models/modified/model.obj" in that shape\'s /models folder.' "",
    "If the shape is already on the omniverse server at g_omni_shape_loc (defaults to",
    "/Projects/shapenet), then that model will be used instead of the downloaded",
    "original or locally saved or modified shapenet obj file.",
    "",
    "The plugin python code lives in: ",
    "\t\tsource\\extensions\\omni.isaac\\shapenet\\python\\scripts",
]


class ShapenetMenu:
    def __init__(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._input = carb.input.acquire_input_interface()
        self._settings = None
        self._editor_menu = omni.kit.ui.get_editor_menu()
        self._login_window = None
        global g_shapenet_db
        g_shapenet_db = get_database()

        self.menus = []

        if pickle_file_exists():
            self.menus.append(self._editor_menu.add_item(SETTINGS_MENU_ITEM, self._on_settings_menu_click))
        else:
            self.menus.append(self._editor_menu.add_item(CREATE_DATABASE_MENU_ITEM, self._on_create_database_click))

        self.menus.append(self._editor_menu.add_item(HELP_MENU_ITEM, self._on_help_menu_click))

    def _on_create_database_click(self, menu, value):
        if menu == CREATE_DATABASE_MENU_ITEM:
            if self._login_window != None:
                self._login_window._window.show()
            else:
                self._login_window = ShapenetLogin(self)

    def _on_settings_menu_click(self, menu, value):
        if menu == SETTINGS_MENU_ITEM:
            if self._settings != None:
                self._settings._window.show()
            else:
                self._settings = ShapenetSettings()

    def _on_help_menu_click(self, menu, value):
        self._window = omni.kit.ui.Window(
            "Shapenet Help",
            0,
            0,
            menu_path="Window/Shapenet Help",
            open=False,
            dock=omni.kit.ui.DockPreference.DISABLED,
            is_toggle_menu=False,
        )
        if not pickle_file_exists():
            for line in ADD_DB_TEXT:
                self._window.layout.add_child(omni.kit.ui.Label(line))

        for line in HELP_TEXT:
            self._window.layout.add_child(omni.kit.ui.Label(line))
        self._window.show()

    def _hide_db_show_add(self):
        # hide the CREATE_DATABASE_MENU_ITEM, show the add model menu
        if pickle_file_exists():
            self._editor_menu.remove_item(CREATE_DATABASE_MENU_ITEM)
            self.menus.append(self._editor_menu.add_item(SETTINGS_MENU_ITEM, self._on_settings_menu_click))

    def shutdown(self):
        self.menus = []
