import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf

# from omni.physx import _physx
from .common import import_robot
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysicsSchemaTools, PhysxSchema


class import_carter:
    def __init__(self, urdf_interface):
        self._urdf_interface = urdf_interface
        self._window = omni.kit.ui.Window(
            "Import Carter",
            300,
            200,
            menu_path="Isaac Samples/URDF/Carter",
            open=False,
            dock=omni.kit.ui.DockPreference.DISABLED,
        )
        load_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        config_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Configure Robot"))
        config_robot_btn.set_clicked_fn(self._on_config_robot)
        # self._physxIFace = _physx.acquire_physx_interface()

    def _on_load_robot(self, widget):
        # TODO: fix this workaround to clear stage
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetDefaultPrim()
        prim.SetActive(False)

        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = True
        import_robot(self._urdf_interface, "data/urdf/robots/carter/urdf/carter.urdf", import_config)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        # scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))
        PhysicsSchemaTools.addGroundPlane(stage, "/groundPlane", "Z", 1500.0, Gf.Vec3f(-50), Gf.Vec3f(0.5))
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        carter_prim = stage.GetPrimAtPath("/carter")
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, carter_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(False)

        left_wheel_drive = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")
        if not left_wheel_drive.GetTargetTypeAttr():
            left_wheel_drive.CreateTargetTypeAttr("velocity")
        else:
            left_wheel_drive.GetTargetTypeAttr().Set("velocity")

        if not left_wheel_drive.GetTargetAttr():
            left_wheel_drive.CreateTargetAttr(2.5)
        else:
            left_wheel_drive.GetTargetAttr().Set(2.5)

        if not left_wheel_drive.GetStiffnessAttr():
            left_wheel_drive.CreateStiffnessAttr(0)
        else:
            left_wheel_drive.GetStiffnessAttr().Set(0)

        if not left_wheel_drive.GetDampingAttr():
            left_wheel_drive.CreateDampingAttr(100000)
        else:
            left_wheel_drive.GetDampingAttr().Set(100000)

        right_wheel_drive = PhysicsSchema.DriveAPI.Get(
            stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular"
        )
        if not right_wheel_drive.GetTargetTypeAttr():
            right_wheel_drive.CreateTargetTypeAttr("velocity")
        else:
            right_wheel_drive.GetTargetTypeAttr().Set("velocity")

        if not right_wheel_drive.GetTargetAttr():
            right_wheel_drive.CreateTargetAttr(2.5)
        else:
            right_wheel_drive.GetTargetAttr().Set(2.5)

        if not right_wheel_drive.GetStiffnessAttr():
            right_wheel_drive.CreateStiffnessAttr(0)
        else:
            right_wheel_drive.GetStiffnessAttr().Set(0)

        if not right_wheel_drive.GetDampingAttr():
            right_wheel_drive.CreateDampingAttr(100000)
        else:
            right_wheel_drive.GetDampingAttr().Set(100000)
