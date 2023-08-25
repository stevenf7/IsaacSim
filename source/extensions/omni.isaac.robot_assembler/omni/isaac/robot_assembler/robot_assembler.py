from typing import List, Tuple

import carb
import numpy as np
import omni.kit.commands
import omni.timeline
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.numpy.rotations import quats_to_rot_matrices, rot_matrices_to_quats
from omni.isaac.core.utils.prims import delete_prim, get_prim_at_path, get_prim_object_type, is_prim_path_valid
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.utils.string import find_unique_string_name
from pxr import Gf, Sdf, Usd, UsdPhysics


class AssembledBodies:
    def __init__(
        self,
        base_path: str,
        attach_path: str,
        fixed_joint: UsdPhysics.FixedJoint,
        root_joints: List[UsdPhysics.Joint],
        collision_mask=None,
    ):
        self._base_path = base_path
        self._attach_path = attach_path
        self._fixed_joint = fixed_joint

        self._root_joints = root_joints

        self._is_assembled = True
        self._collision_mask = collision_mask

    @property
    def base_path(self) -> str:
        """Prim path of the base body

        Returns:
            str: Prim path of the base body
        """
        return self._base_path

    @property
    def attach_path(self) -> str:
        """Prim path of the floating (attach) body

        Returns:
            str: Prim path of the floating (attach) body
        """
        return self._attach_path

    @property
    def fixed_joint(self) -> UsdPhysics.FixedJoint:
        """USD fixed joint linking base and floating body together

        Returns:
            UsdPhysics.FixedJoint: USD fixed joint linking base and floating body together
        """
        return self._fixed_joint

    @property
    def root_joints(self) -> List[UsdPhysics.Joint]:
        """Root joints that tie the floating body to the USD stage.  These are disabled in an assembled body,
        and will be re-enabled by the disassemble() function.

        Returns:
            List[UsdPhysics.Joint]: Root joints that tie the floating body to the USD stage.
        """
        return self._root_joints

    @property
    def collision_mask(self) -> Usd.Relationship:
        """A Usd Relationship masking collisions between the two assembled bodies

        Returns:
            Usd.Relationship: A Usd Relationship masking collisions between the two assembled bodies
        """
        return self._collision_mask

    def is_assembled(self) -> bool:
        """The composed robots are currently composed together.  I.e. the disassemble() function has not been called.

        Returns:
            bool: The disassemble() function has not been called.
        """
        return self._is_assembled

    def disassemble(self):
        """Disassemble composed robots.  This can only be done one time, and it will result in all non-trivial functions in this class returning immediately."""
        if not self.is_assembled():
            carb.log_warn("Cannot disassemble a robot that has already been disassembled")
            return

        # Reactivate the root joints tying attach robot to stage
        for root_joint in self.root_joints:
            root_joint.GetProperty("physics:jointEnabled").Set(True)

        attach_prim = get_prim_at_path(self.attach_path)
        if attach_prim.HasAttribute("physics:kinematicEnabled"):
            attach_prim.GetAttribute("physics:kinematicEnabled").Set(True)

        # Delete the Fixed Joint and attach_point_transform
        delete_prim(self.fixed_joint.GetPath())

        self._unmask_collisions()

        self._refresh_asset(self.attach_path)
        self._refresh_asset(self.base_path)

        self._is_assembled = False

    def get_fixed_joint_transform(self) -> Tuple[np.array, np.array]:
        """Get the transform between mount frames in composed robot.

        Returns:
            Tuple[np.array, np.array]: translation with shape (3,) and orientation with shape (4,)
        """
        if not self.is_assembled():
            carb.log_warn("Fixed joint no longer exists in composed robot.  Robots have been disassembled.")
            return None, None
        fixed_joint = self.fixed_joint
        translation = np.array(fixed_joint.GetLocalPos0Attr().Get())
        orientation = np.array(fixed_joint.GetLocalRot0Attr().Get())

        return translation, orientation

    def set_fixed_joint_transform(self, translation: np.array, orientation: np.array):
        """Set the transform between mount frames in the composed body.

        Args:
            translation (np.array): Local translation relative to mount frame on base body.
            orientation (np.array): Local quaternion orientation relative to mount frame on base body.
        """
        if not self.is_assembled():
            carb.log_warn("Fixed joint no longer exists in composed robot.  Rigid Bodies have been disassembled.")
            return
        fixed_joint = self.fixed_joint
        fixed_joint.GetLocalPos0Attr().Set(Gf.Vec3f(*translation.astype(float)))
        fixed_joint.GetLocalRot0Attr().Set(Gf.Quatf(*orientation.astype(float)))

        self._refresh_asset(self._attach_path)
        self._refresh_asset(self._base_path)

    def _unmask_collisions(self):
        if self._collision_mask is not None:
            [self._collision_mask.RemoveTarget(target) for target in self._collision_mask.GetTargets()]
            self._collision_mask = None

    def _refresh_asset(self, prim_path):
        # Refreshing payloads manually is a way to get the Articulation to update immediately while the timeline is
        # still playing.  Usd Physics should be doing this automatically, but there is currently a bug.  This function
        # will eventually become unnecessary.
        stage = get_current_stage()
        prim = get_prim_at_path(prim_path)

        composed_payloads = omni.usd.get_composed_payloads_from_prim(prim)
        if len(composed_payloads) != 0:
            payload = Sdf.Payload(prim_path)
            omni.kit.commands.execute("RemovePayload", stage=stage, prim_path=prim_path, payload=payload)
            omni.kit.commands.execute("AddPayload", stage=stage, prim_path=prim_path, payload=payload)

        composed_refs = omni.usd.get_composed_references_from_prim(prim)
        if len(composed_refs) != 0:
            reference = Sdf.Reference(prim_path)
            omni.kit.commands.execute(
                "RemoveReference", stage=stage, prim_path=Sdf.Path(prim_path), reference=reference
            )
            omni.kit.commands.execute("AddReference", stage=stage, prim_path=Sdf.Path(prim_path), reference=reference)


class AssembledRobot:
    def __init__(self, assembled_robots: AssembledBodies):
        self.assembled_robots = assembled_robots

    @property
    def base_path(self) -> str:
        """Prim path of the base body

        Returns:
            str: Prim path of the base body
        """
        return self.assembled_robots.base_path

    @property
    def attach_path(self) -> str:
        """Prim path of the floating (attach) body

        Returns:
            str: Prim path of the floating (attach) body
        """
        return self.assembled_robots.attach_path

    @property
    def fixed_joint(self) -> UsdPhysics.FixedJoint:
        """USD fixed joint linking base and floating body together

        Returns:
            UsdPhysics.FixedJoint: USD fixed joint linking base and floating body together
        """
        return self.assembled_robots.fixed_joint

    @property
    def root_joints(self) -> List[UsdPhysics.Joint]:
        """Root joints that tie the floating body to the USD stage.  These are disabled in an assembled body,
        and will be re-enabled by the disassemble() function.

        Returns:
            List[UsdPhysics.Joint]: Root joints that tie the floating body to the USD stage.
        """
        return self.assembled_robots.root_joints

    @property
    def collision_mask(self) -> Usd.Relationship:
        """A Usd Relationship masking collisions between the two assembled robots

        Returns:
            Usd.Relationship: A Usd Relationship masking collisions between the two assembled robots
        """
        return self.assembled_robots.collision_mask

    def is_assembled(self) -> bool:
        """The composed robots are currently composed together.  I.e. the disassemble() function has not been called.

        Returns:
            bool: The disassemble() function has not been called.
        """
        return self.assembled_robots.is_assembled()

    def disassemble(self):
        """Disassemble composed robots.  This can only be done one time, and it will result in all non-trivial functions in this class returning immediately."""
        if not self.assembled_robots.is_assembled():
            carb.log_warn("Cannot disassemble a robot that has already been disassembled")
            return

        # Reactivate the gripper Articulation Root
        art_b_prim = get_prim_at_path(self.attach_path)
        if art_b_prim.HasProperty("physxArticulation:articulationEnabled"):
            art_b_prim.GetProperty("physxArticulation:articulationEnabled").Set(True)

        self.assembled_robots.disassemble()

    def get_fixed_joint_transform(self):
        """Get the transform between mount frames in composed robot.

        Returns:
            Tuple[np.array, np.array]: translation with shape (3,) and orientation with shape (4,)
        """
        return self.assembled_robots.get_fixed_joint_transform()

    def set_fixed_joint_transform(self, translation: np.array, orientation: np.array):
        """Set the transform between mount frames in the composed robot.

        Args:
            translation (np.array): Local translation relative to mount frame on base robot.
            orientation (np.array): Local quaternion orientation relative to mount frame on base robot.
        """
        self.assembled_robots.set_fixed_joint_transform(translation, orientation)


class RobotAssembler:
    def __init__(self):
        self._timeline = omni.timeline.get_timeline_interface()

    def mask_collisions(self, prim_path_a: str, prim_path_b: str) -> Usd.Relationship:
        """Mask collisions between two prims.  All nested prims will also be included.

        Args:
            prim_path_a (str): Path to a prim
            prim_path_b (str): Path to a prim

        Returns:
            Usd.Relationship: A relationship filtering collisions between prim_path_a and prim_path_b
        """
        filteringPairsAPI = UsdPhysics.FilteredPairsAPI.Apply(get_prim_at_path(prim_path_a))
        rel = filteringPairsAPI.CreateFilteredPairsRel()
        rel.AddTarget(Sdf.Path(prim_path_b))
        return rel

    def assemble_rigid_bodies(
        self,
        base_path: str,
        attach_path: str,
        base_mount_frame: str,
        attach_mount_frame: str,
        fixed_joint_offset: np.array = np.zeros(3),
        fixed_joint_orient: np.array = np.array([1, 0, 0, 0]),
        mask_all_collisions: bool = True,
    ) -> AssembledBodies:
        """Assemble two rigid bodies into one physical structure

        Args:
            base_robot_path (str): Path to base robot.
            attach_robot_path (str): Path to attach robot.  The attach robot will be unrooted from the stage and attached only to the base robot
            base_robot_mount_frame (str): Relative path to frame in base robot where there is the desired attach point.
            attach_robot_mount_frame (str): Relative path to frame in the attach robot where there is the desired attach point.
            fixed_joint_offset (np.array, optional): Fixed offset between attach points. Defaults to np.zeros(3).
            fixed_joint_orient (np.array, optional): Fixed orientation between attach points. Defaults to np.array([1, 0, 0, 0]).
            mask_all_collisions (bool, optional): Mask all collisions between attach robot and base robot.  This is necessary when setting single_robot=False to prevent Physics constraint
                violations from the new fixed joint.  Advanced users may set this flag to False and use the mask_collisions() function separately for more customizable behavior.  Defaults to True.

        Returns:
            AssembledBodies: An object representing the assembled bodies. This object can detach the composed robots and edit the fixed joint transform.
        """
        # Make mount_frames if they are not specified
        if base_mount_frame == "":
            base_mount_path = base_path + "/assembler_mount_frame"
            find_unique_string_name(base_mount_path, lambda x: not is_prim_path_valid(x))
            XFormPrim(base_mount_path, translation=np.array([0, 0, 0]))
        else:
            base_mount_path = base_path + base_mount_frame

        if attach_mount_frame == "":
            attach_mount_path = attach_path + "/assembler_mount_frame"
            find_unique_string_name(attach_mount_path, lambda x: not is_prim_path_valid(x))
            XFormPrim(attach_mount_path, translation=np.array([0, 0, 0]))
        else:
            attach_mount_path = attach_path + attach_mount_frame

        self._move_obj_b_to_local_pos(base_mount_path, attach_path, fixed_joint_offset, fixed_joint_orient)

        # Find and Disable Fixed Joints that Tie Object B to the Stage
        root_joints = [
            p
            for p in Usd.PrimRange(get_prim_at_path(attach_path))
            if UsdPhysics.Joint(p)
            and (
                len(p.GetProperty("physics:body0").GetTargets()) == 0
                or len(p.GetProperty("physics:body1").GetTargets()) == 0
            )
        ]

        for root_joint in root_joints:
            root_joint.GetProperty("physics:jointEnabled").Set(False)

        attach_prim = get_prim_at_path(attach_path)
        if attach_prim.HasAttribute("physics:kinematicEnabled"):
            attach_prim.GetAttribute("physics:kinematicEnabled").Set(False)

        # Create fixed Joint between attach frames
        fixed_joint = self.create_fixed_joint(
            attach_mount_path, base_mount_path, attach_mount_path, fixed_joint_offset, fixed_joint_orient
        )

        # Disable Articulation Root on Articulation B so that A is always the prim path for the composed robot
        fixed_joint.GetExcludeFromArticulationAttr().Set(True)

        collision_mask = None
        if mask_all_collisions:
            collision_mask = self.mask_collisions(base_path, attach_path)

        self._refresh_asset(base_path)
        self._refresh_asset(attach_path)

        return AssembledBodies(base_path, attach_path, fixed_joint, root_joints, collision_mask)

    def assemble_articulations(
        self,
        base_robot_path: str,
        attach_robot_path: str,
        base_robot_mount_frame: str,
        attach_robot_mount_frame: str,
        fixed_joint_offset: np.array = np.zeros(3),
        fixed_joint_orient: np.array = np.array([1, 0, 0, 0]),
        mask_all_collisions=True,
        single_robot=False,
    ) -> AssembledRobot:
        """Compose two robots into one physical structure

        Args:
            base_robot_path (str): Path to base robot.
            attach_robot_path (str): Path to attach robot.  The attach robot will be unrooted from the stage and attached only to the base robot
            base_robot_mount_frame (str): Relative path to frame in base robot where there is the desired attach point.
            attach_robot_mount_frame (str): Relative path to frame in the attach robot where there is the desired attach point.
            fixed_joint_offset (np.array, optional): Fixed offset between attach points. Defaults to np.zeros(3).
            fixed_joint_orient (np.array, optional): Fixed orientation between attach points. Defaults to np.array([1, 0, 0, 0]).
            mask_all_collisions (bool, optional): Mask all collisions between attach robot and base robot.  This is necessary when setting single_robot=False to prevent Physics constraint
                violations from the new fixed joint.  Advanced users may set this flag to False and use the mask_collisions() function separately for more customizable behavior.  Defaults to True.
            single_robot (bool, optional): If True: control the resulting composed robots as a single robot Articulation at base_robot_path.
                Setting this flag to True may resolve unstable physics behavior when teleporting the robot base.  Defaults to False.

        Returns:
            AssembledRobot: An object representing the assembled robot.  This object can detach the composed robots and edit the fixed joint transform.
        """
        assemblage = self.assemble_rigid_bodies(
            base_robot_path,
            attach_robot_path,
            base_robot_mount_frame,
            attach_robot_mount_frame,
            fixed_joint_offset,
            fixed_joint_orient,
            mask_all_collisions,
        )

        # Disable Articulation Root on Articulation B so that A is always the prim path for the composed robot
        if single_robot:
            art_b_prim = get_prim_at_path(attach_robot_path)
            if art_b_prim.HasProperty("physxArticulation:articulationEnabled"):
                art_b_prim.GetProperty("physxArticulation:articulationEnabled").Set(False)

            assemblage.fixed_joint.GetExcludeFromArticulationAttr().Set(False)

            self._refresh_asset(base_robot_path)
            self._refresh_asset(attach_robot_path)

        return AssembledRobot(assemblage)

    def create_fixed_joint(
        self,
        prim_path: str,
        target0: str = None,
        target1: str = None,
        fixed_joint_offset: np.array = np.zeros(3),
        fixed_joint_orient: np.array = np.array([1, 0, 0, 0]),
    ) -> UsdPhysics.FixedJoint:
        """Create a fixed joint between two bodies

        Args:
            prim_path (str): Prim path at which to place new fixed joint.
            target0 (str, optional): Prim path of frame at which to attach fixed joint. Defaults to None.
            target1 (str, optional): Prim path of frame at which to attach fixed joint. Defaults to None.
            fixed_joint_offset (np.array, optional): Translational offset of fixed joint between frames. Defaults to np.zeros(3).
            fixed_joint_orient (np.array, optional): Rotational offset of fixed joint between frames (quaternion). Defaults to np.array([1, 0, 0, 0]).

        Returns:
            UsdPhysics.FixedJoint: A USD fixed joint
        """
        fixed_joint_path = prim_path + "/AssemblerFixedJoint"
        fixed_joint_path = find_unique_string_name(fixed_joint_path, lambda x: not is_prim_path_valid(x))

        stage = get_current_stage()
        fixed_joint = UsdPhysics.FixedJoint.Define(stage, fixed_joint_path)
        if target0 is not None:
            fixed_joint.GetBody0Rel().SetTargets([target0])
        if target1 is not None:
            fixed_joint.GetBody1Rel().SetTargets([target1])

        fixed_joint.GetLocalPos0Attr().Set(Gf.Vec3f(*fixed_joint_offset.astype(float)))
        fixed_joint.GetLocalRot0Attr().Set(Gf.Quatf(*fixed_joint_orient.astype(float)))
        fixed_joint.GetLocalPos1Attr().Set(Gf.Vec3f(*np.zeros(3).astype(float)))
        fixed_joint.GetLocalRot1Attr().Set(Gf.Quatf(*np.array([1, 0, 0, 0]).astype(float)))

        return fixed_joint

    def convert_prim_to_rigid_body(self, prim_path: str) -> None:
        """Convert a prim to a rigid body by applying the UsdPhysics.RigidBodyAPI
        Also sets physics:kinematicEnabled property to true to prevent falling from gravity without needing a fixed joint.

        Args:
            prim_path (str): Path to prim to convert.
        """
        prim_to_convert = get_prim_at_path(prim_path)
        if get_prim_object_type(prim_path) == "articulation":
            carb.log_warn("Cannot convert Articulation to Rigid Body")
            return False
        if not prim_to_convert.IsValid():
            carb.log_warn(f"No prim can be found at path {prim_path}")
            return False
        else:
            if not prim_to_convert.HasAPI(UsdPhysics.RigidBodyAPI):
                UsdPhysics.RigidBodyAPI.Apply(prim_to_convert)

        if prim_to_convert.HasAttribute("physics:kinematicEnabled"):
            prim_to_convert.GetAttribute("physics:kinematicEnabled").Set(True)

        return True

    def _refresh_asset(self, prim_path):
        # Refreshing payloads manually is a way to get the Articulation to update immediately while the timeline is
        # still playing.  Usd Physics should be doing this automatically, but there is currently a bug.  This function
        # will eventually become unnecessary.
        stage = get_current_stage()
        prim = get_prim_at_path(prim_path)

        composed_payloads = omni.usd.get_composed_payloads_from_prim(prim)
        if len(composed_payloads) != 0:
            payload = Sdf.Payload(prim_path)
            omni.kit.commands.execute("RemovePayload", stage=stage, prim_path=prim_path, payload=payload)
            omni.kit.commands.execute("AddPayload", stage=stage, prim_path=prim_path, payload=payload)

        composed_refs = omni.usd.get_composed_references_from_prim(prim)
        if len(composed_refs) != 0:
            reference = Sdf.Reference(prim_path)
            omni.kit.commands.execute(
                "RemoveReference", stage=stage, prim_path=Sdf.Path(prim_path), reference=reference
            )
            omni.kit.commands.execute("AddReference", stage=stage, prim_path=Sdf.Path(prim_path), reference=reference)

    def _move_obj_b_to_local_pos(self, base_mount_path, attach_path, rel_offset, rel_orient):
        a_trans, a_orient = XFormPrim(base_mount_path).get_world_pose()

        a_rot = quats_to_rot_matrices(a_orient)
        rel_rot = quats_to_rot_matrices(rel_orient)

        b_translation = a_rot @ rel_offset + a_trans
        b_rot = a_rot @ rel_rot
        b_orient = rot_matrices_to_quats(b_rot)

        XFormPrim(attach_path).set_world_pose(b_translation, b_orient)
