import carb
import omni
import omni.kit.commands
import asyncio
import math
import weakref
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from .common import set_drive_parameters
from pxr import UsdLux, Sdf, Gf, UsdPhysics


EXTENSION_NAME = "Import Kaya"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._window = omni.ui.Window(EXTENSION_NAME, width=200, height=125, visible=False)
        self._menu_items = [
            MenuItemDescription(
                name="Importing",
                sub_menu=[
                    MenuItemDescription(name="Kaya URDF", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Button("Load Robot", clicked_fn=self._on_load_robot)
                ui.Button("Configure Joint Drives", clicked_fn=self._on_config_robot)
                ui.Button("Spin in place", clicked_fn=self._on_config_drives)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_load_robot(self):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_kaya(load_stage))

    async def _load_kaya(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            status, import_config = omni.kit.commands.execute("URDFCreateImportConfig")
            import_config.merge_fixed_joints = True
            import_config.import_inertia_tensor = False
            # import_config.distance_scale = 100
            import_config.fix_base = False
            omni.kit.commands.execute(
                "URDFParseAndImportFile",
                urdf_path=self._extension_path + "/data/urdf/robots/kaya/urdf/kaya.urdf",
                import_config=import_config,
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", -51, 63, 25, True)
            viewport.set_camera_target("/OmniverseKit_Persp", 220, -218, -160, True)
            stage = omni.usd.get_context().get_stage()
            scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
            scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
            scene.CreateGravityMagnitudeAttr().Set(981.0)

            result, plane_path = omni.kit.commands.execute(
                "AddGroundPlaneCommand",
                stage=stage,
                planePath="/groundPlane",
                axis="Z",
                size=1500.0,
                position=Gf.Vec3f(0, 0, -25),
                color=Gf.Vec3f(0.5),
            )
            # make sure the ground plane is under root prim and not robot
            omni.kit.commands.execute(
                "MovePrimCommand", path_from=plane_path, path_to="/groundPlane", keep_world_transform=True
            )

            distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(500)

    def _on_config_robot(self):
        stage = omni.usd.get_context().get_stage()
        # Make all rollers spin freely by removing extra drive API
        for axle in range(0, 2 + 1):
            for ring in range(0, 1 + 1):
                for roller in range(0, 4 + 1):
                    prim_path = (
                        "/kaya/axle_"
                        + str(axle)
                        + "/roller_"
                        + str(axle)
                        + "_"
                        + str(ring)
                        + "_"
                        + str(roller)
                        + "_joint"
                    )
                    prim = stage.GetPrimAtPath(prim_path)
                    omni.kit.commands.execute(
                        "UnapplyAPISchemaCommand",
                        api=UsdPhysics.DriveAPI,
                        prim=prim,
                        api_prefix="drive",
                        multiple_api_token="angular",
                    )

    def _on_config_drives(self):
        self._on_config_robot()  # make sure drives are configured first
        stage = omni.usd.get_context().get_stage()
        # set each axis to spin at a rate of 1 rad/s
        axle_0 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_0_joint"), "angular")
        axle_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_1_joint"), "angular")
        axle_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_2_joint"), "angular")

        set_drive_parameters(axle_0, "velocity", math.degrees(1), 0, math.radians(1e5), 1e10)
        set_drive_parameters(axle_1, "velocity", math.degrees(1), 0, math.radians(1e5), 1e10)
        set_drive_parameters(axle_2, "velocity", math.degrees(1), 0, math.radians(1e5), 1e10)
