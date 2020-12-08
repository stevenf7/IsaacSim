import carb
import omni
import math
import omni.kit.commands
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio

# import omni.physx as _physx
from .common import import_robot, set_drive_parameters
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._window = omni.kit.ui.Window(
            "Import Carter",
            300,
            200,
            menu_path="Isaac Robotics/URDF/Carter",
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
        asyncio.ensure_future(self._load_carter(load_stage))

    async def _load_carter(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = True
            import_config.fix_base = False
            import_robot(
                self._urdf_interface, self._extension_path + "/data/urdf/robots/carter/urdf/carter.urdf", import_config
            )

            viewport = omni.kit.viewport.get_default_viewport_window()
            viewport.set_camera_position("/OmniverseKit_Persp", 300, -350, 113, True)
            viewport.set_camera_target("/OmniverseKit_Persp", -96, 108, -20, True)

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
            position=Gf.Vec3f(-50),
            color=Gf.Vec3f(0.5),
        )
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        carter_prim = stage.GetPrimAtPath("/carter")

        left_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")

        right_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular")
        # Drive forward
        set_drive_parameters(left_wheel_drive, "velocity", math.degrees(2.5), 0, 1000000, 1e8)
        set_drive_parameters(right_wheel_drive, "velocity", math.degrees(2.5), 0, 1000000, 1e8)

        # Remove drive from rear wheel and pivot
        prim = stage.GetPrimAtPath("/carter/chassis_link/rear_pivot")
        omni.kit.commands.execute(
            "UnapplyAPISchemaCommand",
            api=UsdPhysics.DriveAPI,
            prim=prim,
            api_prefix="PhysicsDrive",
            multiple_api_token="angular",
        )

        prim = stage.GetPrimAtPath("/carter/rear_pivot_link/rear_axle")
        omni.kit.commands.execute(
            "UnapplyAPISchemaCommand",
            api=UsdPhysics.DriveAPI,
            prim=prim,
            api_prefix="PhysicsDrive",
            multiple_api_token="angular",
        )
