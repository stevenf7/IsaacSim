import carb
import omni
import math
import omni.kit.commands
import asyncio
import weakref
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from .common import set_drive_parameters
from pxr import UsdLux, Sdf, Gf, UsdPhysics

EXTENSION_NAME = "Import Carter"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._menu_items = [
            MenuItemDescription(
                name="Importing",
                sub_menu=[
                    MenuItemDescription(name="Carter URDF", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Button("Load Robot", clicked_fn=self._on_load_robot)
                ui.Button("Configure Robot", clicked_fn=self._on_config_robot)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_load_robot(self):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_carter(load_stage))

    async def _load_carter(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            status, import_config = omni.kit.commands.execute("CreateURDFImportConfigCommand")

            import_config.merge_fixed_joints = False
            import_config.fix_base = False
            omni.kit.commands.execute(
                "ParseAndImportURDFCommand",
                urdf_path=self._extension_path + "/data/urdf/robots/carter/urdf/carter.urdf",
                import_config=import_config,
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", 300, -350, 113, True)
            viewport.set_camera_target("/OmniverseKit_Persp", -96, 108, -20, True)

    def _on_config_robot(self):
        stage = omni.usd.get_context().get_stage()
        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=stage,
            planePath="/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0, 0, -50),
            color=Gf.Vec3f(0.5),
        )
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        carter_prim = stage.GetPrimAtPath("/carter")

        left_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")

        right_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular")
        # Drive forward
        set_drive_parameters(left_wheel_drive, "velocity", math.degrees(2.5), 0, math.radians(1000000), 1e8)
        set_drive_parameters(right_wheel_drive, "velocity", math.degrees(2.5), 0, math.radians(1000000), 1e8)

        # Remove drive from rear wheel and pivot
        prim = stage.GetPrimAtPath("/carter/chassis_link/rear_pivot")
        omni.kit.commands.execute(
            "UnapplyAPISchemaCommand",
            api=UsdPhysics.DriveAPI,
            prim=prim,
            api_prefix="drive",
            multiple_api_token="angular",
        )

        prim = stage.GetPrimAtPath("/carter/rear_pivot_link/rear_axle")
        omni.kit.commands.execute(
            "UnapplyAPISchemaCommand",
            api=UsdPhysics.DriveAPI,
            prim=prim,
            api_prefix="drive",
            multiple_api_token="angular",
        )
