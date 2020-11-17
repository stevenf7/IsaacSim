import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf
import asyncio

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics, PhysxSchema


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._window = omni.kit.ui.Window(
            "Import Franka",
            300,
            200,
            menu_path="Isaac Robotics/URDF/Franka",
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
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_franka(load_stage))

    async def _load_franka(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetDefaultPrim()
            prim.SetActive(False)

            import_config = _urdf.ImportConfig()
            import_config.merge_fixed_joints = False
            import_robot(
                self._urdf_interface, "data/urdf/robots/franka_description/robots/panda_arm_hand.urdf", import_config
            )

            editor = omni.kit.editor.get_editor_interface()
            editor.set_camera_position("/OmniverseKit_Persp", 122, -124, 113, True)
            editor.set_camera_target("/OmniverseKit_Persp", -96, 108, 0, True)

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=stage,
            planePath="/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0),
            color=Gf.Vec3f(0.5),
        )
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        franka_prim = stage.GetDefaultPrim()
        # Set articulation base parameters
        physicsArticulationAPI = UsdPhysics.ArticulationAPI.Get(stage, franka_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(True)

        joint_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link0/panda_joint1"), "angular")
        joint_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link1/panda_joint2"), "angular")
        joint_3 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link2/panda_joint3"), "angular")
        joint_4 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link3/panda_joint4"), "angular")
        joint_5 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link4/panda_joint5"), "angular")
        joint_6 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link5/panda_joint6"), "angular")
        joint_7 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link6/panda_joint7"), "angular")
        finger_1 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint1"), "linear")
        finger_2 = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint2"), "linear")

        # Set the drive mode, target, stiffness, damping and max force for each joint
        set_drive_parameters(joint_1, "position", 0.012, 60000, 3000, 8700)
        set_drive_parameters(joint_2, "position", -0.57, 60000, 3000, 8700)
        set_drive_parameters(joint_3, "position", 0, 60000, 3000, 8700)
        set_drive_parameters(joint_4, "position", -2.81, 60000, 3000, 8700)
        set_drive_parameters(joint_5, "position", 0, 25000, 3000, 1200)
        set_drive_parameters(joint_6, "position", 3.037, 15000, 3000, 1200)
        set_drive_parameters(joint_7, "position", 0.741, 5000, 3000, 1200)
        set_drive_parameters(finger_1, "position", 4, 6000, 1000, 1200)
        set_drive_parameters(finger_2, "position", 4, 6000, 1000, 1200)

        # Set Max Joint velocity on all joints

        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link0/panda_joint1"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link1/panda_joint2"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link2/panda_joint3"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link3/panda_joint4"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link4/panda_joint5"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link5/panda_joint6"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_link6/panda_joint7"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_hand/panda_finger_joint1"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
        PhysxSchema.PhysxArticulationJointAPI.Get(
            stage, "/panda/panda_hand/panda_finger_joint2"
        ).CreatePhysxArticulationJointMaxJointVelocityAttr(10.0)
