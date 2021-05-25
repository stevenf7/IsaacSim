import omni.ext
import omni.kit.commands
import omni.kit.ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
import carb
import gc
import weakref


class Extension(omni.ext.IExt):
    def on_startup(self):

        manip_menu = [
            MenuItemDescription(
                name="Franka",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Franka/franka_alt_fingers.usd", "/Franka"
                ),
            ),
            MenuItemDescription(
                name="UR10",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UR10/ur10.usd", "/UR10"),
            ),
        ]

        mobile_menu = [
            MenuItemDescription(
                name="Carter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Carter/carter_sphere_wheels_lidar.usd", "/Carter"
                ),
            ),
            MenuItemDescription(
                name="STR",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/STR/STR_V4_Physics_Caster_Sensors.usda", "/STR"
                ),
            ),
            MenuItemDescription(
                name="Kaya",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Kaya/kaya.usd", "/Kaya"),
            ),
            MenuItemDescription(
                name="Jetbot",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Jetbot/jetbot.usd", "/Jetbot"),
            ),
            MenuItemDescription(
                name="Jetracer",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Jetracer/jetracer.usd", "/STR"),
            ),
        ]

        robot_menu = [
            MenuItemDescription(name="Manipulators", sub_menu=manip_menu),
            MenuItemDescription(name="Mobile Bases", sub_menu=mobile_menu),
        ]
        from_menu = [MenuItemDescription(name="From Library", sub_menu=robot_menu)]

        env_menu = [
            MenuItemDescription(
                name="Grid Room",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Grid/gridroom_curved.usd", "/GridRoom"
                ),
            ),
            MenuItemDescription(
                name="Simple Room",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Room/simple_room.usd", "/SimpleRoom"
                ),
            ),
            MenuItemDescription(
                name="Warehouse",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(
                name="Warehouse Multiple Shelves",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd", "/Warehouse"
                ),
            ),
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                glyph="plug.svg",
                sub_menu=[
                    MenuItemDescription(name="Robots", sub_menu=from_menu),
                    MenuItemDescription(name="Environments", sub_menu=env_menu),
                ],
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def create_asset(self, usd_path, stage_path):

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server

        omni.kit.commands.execute(
            "CreateReferenceCommand",
            usd_context=omni.usd.get_context(),
            path_to=stage_path,
            asset_path=self._nucleus_path + usd_path,
            instanceable=False,
        )

        pass

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        gc.collect()
