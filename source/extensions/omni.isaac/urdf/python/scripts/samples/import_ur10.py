import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._window = omni.kit.ui.Window(
            "Import UR10",
            300,
            200,
            menu_path="Isaac Robotics/URDF/UR10",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        load_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        config_robot_btn = self._window.layout.add_child(omni.kit.ui.Button("Configure Robot"))
        config_robot_btn.set_clicked_fn(self._on_config_robot)

    def on_shutdown(self):
        self._window = None

    def _on_load_robot(self, widget):
        load_stage = asyncio.ensure_future(omni.kit.asyncapi.new_stage())
        asyncio.ensure_future(self._load_robot(load_stage))

    async def _load_robot(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetDefaultPrim()
            prim.SetActive(False)

            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = False
            import_robot(self._urdf_interface, "data/urdf/robots/ur10/urdf/ur10_base.urdf", import_config)

            editor = omni.kit.editor.get_editor_interface()
            editor.set_camera_position("/OmniverseKit_Persp", 122, -124, 113, True)
            editor.set_camera_target("/OmniverseKit_Persp", -96, 108, 0, True)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))

        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        robot_prim = stage.GetDefaultPrim()
        # Set articulation base parameters
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, robot_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(True)

        joint_1 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/base_link/shoulder_pan_joint"), "angular")
        joint_2 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/shoulder_link/shoulder_lift_joint"), "angular")
        joint_3 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/upper_arm_link/elbow_joint"), "angular")
        joint_4 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/forearm_link/wrist_1_joint"), "angular")
        joint_5 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_1_link/wrist_2_joint"), "angular")
        joint_6 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/ur10/wrist_2_link/wrist_3_joint"), "angular")

        # Set the drive mode, target, stiffness, damping and max force for each joint
        set_drive_parameters(joint_1, "position", 0, 20000, 2000, 330000)
        set_drive_parameters(joint_2, "position", 0, 20000, 2000, 330000)
        set_drive_parameters(joint_3, "position", 0, 20000, 2000, 150000)
        set_drive_parameters(joint_4, "position", 0, 20000, 2000, 56000)
        set_drive_parameters(joint_5, "position", 0, 20000, 2000, 56000)
        set_drive_parameters(joint_6, "position", 0, 20000, 2000, 56000)

        # Set Max Joint velocity on all joints

        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/base_link/shoulder_pan_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/shoulder_link/shoulder_lift_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/upper_arm_link/elbow_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/forearm_link/wrist_1_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/wrist_1_link/wrist_2_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/ur10/wrist_2_link/wrist_3_joint"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(1000000.000)
