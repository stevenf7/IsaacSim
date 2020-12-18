import carb
import omni
import omni.kit.commands
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio
import math

# import omni.physx as _physx
from .common import import_robot, set_drive_parameters
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._window = omni.kit.ui.Window(
            "Import Kaya",
            300,
            200,
            menu_path="Isaac/URDF/Kaya",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        load_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        config_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Configure Robot"))
        config_robot_btn.set_clicked_fn(self._on_config_robot)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)

    def on_shutdown(self):
        self._window = None

    def _on_load_robot(self, widget):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_kaya(load_stage))

    async def _load_kaya(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = True
            import_config.import_inertia_tensor = False
            # import_config.distance_scale = 100
            import_config.fix_base = False
            import_robot(
                self._urdf_interface, self._extension_path + "/data/urdf/robots/kaya/urdf/kaya.urdf", import_config
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", -51, 63, 25, True)
            viewport.set_camera_target("/OmniverseKit_Persp", 220, -218, -160, True)

    def _on_config_robot(self, widget):
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
            position=Gf.Vec3f(0, 0, -25),
            color=Gf.Vec3f(0.5),
        )

        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        kaya_prim = stage.GetPrimAtPath("/kaya")

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

        # set each axis to spin at a rate of 1 rad/s
        axle_0 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_0_joint"), "angular")
        axle_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_1_joint"), "angular")
        axle_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/kaya/base_link/axle_2_joint"), "angular")

        set_drive_parameters(axle_0, "velocity", math.degrees(1), 0, math.radians(1e4), 1e10)
        set_drive_parameters(axle_1, "velocity", math.degrees(1), 0, math.radians(1e4), 1e10)
        set_drive_parameters(axle_2, "velocity", math.degrees(1), 0, math.radians(1e4), 1e10)

        # usd_context = omni.usd.get_context()
        # selection = usd_context.get_selection()
        # selection.set_selected_prim_paths(["/kaya"], True)
