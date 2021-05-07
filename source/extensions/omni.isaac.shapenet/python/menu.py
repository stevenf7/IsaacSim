import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, rebuild_menus, MenuItemDescription
import weakref
from .login import ShapenetLogin
from .settings import ShapenetSettings
from .globals import *


#   "Keep Help text the width of this line or shorter -------------------------------",
ADD_DB_TEXT = (
    "    Please register an account at https://www.shapenet.org/ so you can make the "
    "database of ShapeNetCore.V1 csv files necessary to run this extension.  Once you "
    "have a validate shapenet.org login, use the menu to create the database.  You "
    "should only have to do this once.\n\n"
)

HELP_TEXT = (
    "    This omni.isaac.shapenet plugin allows you to add ShapeNetCore.V2 models from shapenet.org to your stage in Omniverse Kit.\n\n"
    "    You can use the ShapeNet menu to add shapes.\n\n"
    "    You can also use an external python session to send json formatted commands via http and load shapes with comm_kit.py.\n\n"
    "    See comm_kit.test_comm() or run:\n"
    "\t>  jupyter notebook ShapeNet Python Example.ipynb\n"
    "for examples.\n\n"
    "    If you already have ShapeNetCore V2 installed locally, this plugin can use the local files.  Use the env var SHAPENET_LOCAL_DIR to set that location (IMPORTANT NOTE: Make sure there are no periods, ., in the path name), otherwise, omni.isaac.shapenet will use the default ${data}/shapenet folder.  By using local folders, you can edit shapenet models before their conversion to usd.  If you want to keep the original file, just save the modified file as "
    ' "models/modified/model.obj" in that shape\'s /models folder.\n\n'
    "    If the shape is already on the omniverse server at g_omni_shape_loc (defaults to /Projects/shapenet), then that model will be used instead of the downloaded original or locally saved or modified shapenet obj file.\n\n"
    "    The plugin python code lives in: \n"
    "\t\tsource\\extensions\\omni.isaac\\shapenet\\python"
)


class ShapenetMenu:
    def __init__(self):
        self._settings_window = None
        self._login_window = None
        self._help_window = None

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
        self._sub_menu.append(
            MenuItemDescription(name="Help", onclick_fn=lambda a=weakref.proxy(self): a._on_help_menu_click())
        )

        self._menu_items = [MenuItemDescription(name="Shapenet", sub_menu=self._sub_menu)]
        add_menu_items(self._menu_items, "Isaac Tools")

    def _on_create_database_click(self):
        if self._login_window != None:
            self._login_window.visible = True
        else:
            self._login_window = ShapenetLogin(self)

    def _on_settings_menu_click(self):
        if self._settings_window != None:
            self._settings_window.visible = True
        else:
            self._settings_window = ShapenetSettings()

    def _on_help_menu_click(self):
        help_message = ""
        if not pickle_file_exists():
            help_message = ADD_DB_TEXT
        help_message = help_message + HELP_TEXT
        if not self._help_window:
            flags = ui.WINDOW_FLAGS_NO_RESIZE
            flags |= ui.WINDOW_FLAGS_NO_SCROLLBAR
            self._help_window = ui.Window("Shapenet Help", width=500, height=0, flags=flags)
            with self._help_window.frame:
                with ui.VStack(name="root", style={"VStack::root": {"margin": 10}}, height=0, spacing=20):
                    ui.Label(help_message, alignment=ui.Alignment.LEFT, word_wrap=True)

        self._help_window.visible = True

    def _hide_db_show_add(self):
        # hide the CREATE_DATABASE_MENU_ITEM, show the add model menu
        if pickle_file_exists():
            self._sub_menu[0] = MenuItemDescription(
                name="Add a model", onclick_fn=lambda a=weakref.proxy(self): a._on_settings_menu_click()
            )
            rebuild_menus()

    def shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Tools")
        self._help_window = None
        self._settings_window = None
        self._login_window = None
