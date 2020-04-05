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
from .shape import addShapePrim
import omni.isaac.shapenet
import asyncio
from .settings import ShapenetSettings
from .shape import convert
from .globals import *

SETTINGS_MENU_ITEM = "Shapenet Menu/Settings"
ADD_SHAPE_SETTINGS_MENU_ITEM = "Shapenet Menu/Add Shape/From Settings"
ADD_SHAPE_RANDOM_MENU_ITEM = "Shapenet Menu/Add Shape/Random"
HELP_MENU_ITEM = "Shapenet Menu/Help"
HELP_TEXT = [
    "This omni.isaac.shapenet plugin allows you to add models from shapenet.org to",
    "your stage in kit.",
    "",
    "You can use an external python session to send json formatted commands via http",
    "and load shapes with comm_kit.py.",
    "",
    "See comm_kit.test_comm() or run:",
    "\t>  jupyter notebook ShapeNet Python Example.ipynb",
    "for examples.",
    "",
    "You can also use the menu to add shapes.",
    "",
    "If you already have ShapeNetCore V2 installed locally, this plugin can use that",
    "instead of downloading models from the web.  Use the env var SHAPENET_LOCAL_DIR",
    "to set that location (IMPORTANT NOTE: Make sure there are no periods, ., in the",
    "path name).  Otherwise, omni.isaac.shapenet will use the ${data}/shapenet folder.",
    "",
    "If the shape is already on the omniverse server at g_omni_shape_loc (defaults to",
    "omni:/Projects/shapenet), then that model will be used instead of the original",
    "shapenet obj file.",
    "",
    "The plugin python code lives in: ",
    "\t\tsource\\extensions\\omni.isaac\\shapenet\\python\\scripts",
]


class ShapenetMenu:
    def __init__(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._input = carb.input.acquire_input_interface()
        self._settings = None

        global g_shapenet_db
        g_shapenet_db = get_database()

        self.menus = []
        editor_menu = omni.kit.ui.get_editor_menu()

        self.menus.append(editor_menu.add_item(SETTINGS_MENU_ITEM, self._on_settings_menu_click))
        self.menus.append(editor_menu.add_item(ADD_SHAPE_SETTINGS_MENU_ITEM, self._on_add_from_settings_menu_click))
        self.menus.append(editor_menu.add_item(ADD_SHAPE_RANDOM_MENU_ITEM, self._on_add_random_menu_click))

        with open(os.path.dirname(os.path.realpath(__file__)) + "/menu_tree.json", "r") as read_file:
            self._menu_list = json.load(read_file)

        for menu_item in self._menu_list:
            self.menus.append(editor_menu.add_item(menu_item, self._on_add_random_menu_click))

        self.menus.append(editor_menu.add_item(HELP_MENU_ITEM, self._on_help_menu_click))

    def _on_settings_menu_click(self, menu, value):
        if menu == SETTINGS_MENU_ITEM:
            if self._settings != None:
                self._settings._window.show()
            else:
                self._settings = ShapenetSettings()

    def _on_add_from_settings_menu_click(self, menu, value):

        if self._settings == None:
            self._settings = ShapenetSettings()
            self._settings._window.hide()

        pos = self._settings.getPos()
        rot = self._settings.getRot()
        scale = self._settings.getScale()
        synsetId = self._settings.getSynsetId()
        global g_shapenet_db
        g_shapenet_db = get_database()
        if synsetId not in g_shapenet_db:
            synsetId = random.choice(list(g_shapenet_db))

        modelId = self._settings.getModelId()
        if modelId not in g_shapenet_db[synsetId]:
            modelId = random.choice(list(g_shapenet_db[synsetId]))

        return addShapePrim(False, synsetId, modelId, pos, rot, scale)

    def _on_add_random_menu_click(self, menu, value):
        stage = omni.usd.get_context().get_stage()
        prims = omni.usd.get_context().get_selection().get_selected_prim_paths()
        upAxis = UsdGeom.GetStageUpAxis(stage)

        if menu == ADD_SHAPE_RANDOM_MENU_ITEM:
            synsetId = random.choice(list(g_shapenet_db))
        elif menu in self._menu_list:
            synsetId = self._menu_list[menu]

        modelId = random.choice(list(g_shapenet_db[synsetId]))

        if self._settings == None:
            self._settings = ShapenetSettings()
            self._settings._window.hide()

        pos = self._settings.getPos()
        rot = self._settings.getRot()
        scale = self._settings.getScale()
        return addShapePrim(False, synsetId, modelId, pos, rot, scale)

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
        for line in HELP_TEXT:
            self._window.layout.add_child(omni.kit.ui.Label(line))
        self._window.show()

    def shutdown(self):
        self.menus = []
