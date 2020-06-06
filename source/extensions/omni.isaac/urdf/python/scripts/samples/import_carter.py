import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters, remove_all_schema_multiple_attributes
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysicsSchemaTools, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self):
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

    def on_shutdown(self):
        _urdf.release_urdf_interface(self._urdf_interface)
        self._window = None

    def _on_load_robot(self, widget):
        load_stage = asyncio.ensure_future(omni.kit.asyncapi.new_stage())
        asyncio.ensure_future(self._load_carter(load_stage))

    async def _load_carter(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetDefaultPrim()
            prim.SetActive(False)

            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = True
            import_robot(self._urdf_interface, "data/urdf/robots/carter/urdf/carter.urdf", import_config)

            editor = omni.kit.editor.get_editor_interface()
            editor.set_camera_position("/OmniverseKit_Persp", 300, -350, 113, True)
            editor.set_camera_target("/OmniverseKit_Persp", -96, 108, -20, True)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))
        PhysicsSchemaTools.addGroundPlane(stage, "/groundPlane", "Z", 1500.0, Gf.Vec3f(-50), Gf.Vec3f(0.5))
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        carter_prim = stage.GetPrimAtPath("/carter")
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, carter_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(False)

        left_wheel_drive = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")

        right_wheel_drive = PhysicsSchema.DriveAPI.Get(
            stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular"
        )
        # Drive forward
        set_drive_parameters(left_wheel_drive, "velocity", 2.5, 0, 1000000, 1e8)
        set_drive_parameters(right_wheel_drive, "velocity", 2.5, 0, 1000000, 1e8)

        # Remove drive from rear wheel and pivot
        prim = stage.GetPrimAtPath("/carter/chassis_link/rear_pivot")
        remove_all_schema_multiple_attributes(PhysicsSchema.DriveAPI, prim, "drive", "angular")
        PhysicsSchema.PhysicsSchemaMultipleAPI.UnapplyAPISchema(prim, "DriveAPI:angular")

        prim = stage.GetPrimAtPath("/carter/rear_pivot_link/rear_axle")
        remove_all_schema_multiple_attributes(PhysicsSchema.DriveAPI, prim, "drive", "angular")
        PhysicsSchema.PhysicsSchemaMultipleAPI.UnapplyAPISchema(prim, "DriveAPI:angular")
