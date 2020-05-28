import carb
import omni
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.urdf import _urdf

# from omni.physx import _physx
from .common import import_robot, set_drive_parameters
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysicsSchemaTools, PhysxSchema


class import_franka:
    def __init__(self, urdf_interface):
        self._urdf_interface = urdf_interface
        self._window = omni.kit.ui.Window(
            "Import Franka",
            300,
            200,
            menu_path="Isaac Robotics/URDF/Franka",
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
        import_config.merge_fixed_joints = False
        import_robot(
            self._urdf_interface, "data/urdf/robots/franka_description/robots/panda_arm_hand.urdf", import_config
        )

    def _on_config_robot(self, widget):
        stage = omni.usd.get_context().get_stage()
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/physicsScene"))
        # scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -981.0))
        # PhysicsSchemaTools.addGroundPlane(stage, "/groundPlane", "Z", 1500.0, Gf.Vec3f(-50), Gf.Vec3f(0.5))
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)
        # TODO:Create a body material
        # float dynamicFriction = 1
        # float restitution = 0.5
        # float staticFriction = 1

        # Create a finger material
        # uniform token physxMaterial:frictionCombineMode = "max"
        # bool physxMaterial:improvePatchFriction
        # uniform token physxMaterial:restitutionCombineMode

        carter_prim = stage.GetPrimAtPath("/panda")
        # Set articulation base parameters
        physicsArticulationAPI = PhysicsSchema.ArticulationAPI.Get(stage, carter_prim.GetPath())
        physicsArticulationAPI.GetFixBaseAttr().Set(True)

        joint_1 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link0/panda_joint1"), "angular")
        joint_2 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link1/panda_joint2"), "angular")
        joint_3 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link2/panda_joint3"), "angular")
        joint_4 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link3/panda_joint4"), "angular")
        joint_5 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link4/panda_joint5"), "angular")
        joint_6 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link5/panda_joint6"), "angular")
        joint_7 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_link6/panda_joint7"), "angular")
        finger_1 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint1"), "linear")
        finger_2 = PhysicsSchema.DriveAPI.Get(stage.GetPrimAtPath("/panda/panda_hand/panda_finger_joint2"), "linear")

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

        # Set the contact offset for fingers
        # float minTorsionalPatchRadius = 0.8
        # float torsionalPatchRadius = 1
