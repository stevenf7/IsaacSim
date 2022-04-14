import lula
import carb
import numpy as np
from typing import List, Tuple, Union, Optional
from omni.isaac.core.utils.numpy.rotations import quats_to_rot_matrices
from omni.isaac.core.utils.string import find_unique_string_name
from omni.isaac.core.utils.prims import is_prim_path_valid, delete_prim
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core import objects


class LulaInterfaceHelper:
    """
    Class containing functions common in Lula based algorithms
    """

    def __init__(self, robot_description_path, urdf_path):
        self._world = lula.create_world()
        self._dynamic_obstacles = dict()
        self._static_obstacles = dict()

        self._meters_per_unit = get_stage_units()

        self._robot_description = lula.load_robot(robot_description_path, urdf_path)
        self._kinematics = self._robot_description.kinematics()

        self._robot_base_moved = False
        self._robot_trans, self._robot_rot = np.zeros(3), np.eye(3)

        self._end_effector_translation_target = None
        self._end_effector_rotation_target = None

        self._ground_plane_map = (
            dict()
        )  # maintain a map of core.objects.ground_plane to ground-like cuboids that lula made to support the ground plane add function

    def update_world(self, updated_obstacles: Optional[List] = None) -> None:
        """Update the internal world state of Lula.
        This function automatically tracks the positions of obstacles that have been added with add_obstacle()

        Args:
            updated_obstacles (List[core.objects], optional): Obstacles that have been added by add_obstacle() that need to be updated.
                If not specified, all non-static obstacle positions will be updated.
                If specified, only the obstacles that have been listed will have their positions updated
        """
        if updated_obstacles is None or self._robot_base_moved:
            # assume that all obstacle poses need to be updated
            updated_obstacles = self._dynamic_obstacles.keys()

        for obstacle_prim in updated_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
            trans, rot = self._get_prim_pose_rel_robot_base(obstacle_prim)

            pose = self._get_pose3(trans, rot)
            self._world.set_pose(obstacle_handle, pose)

        if self._robot_base_moved:
            # update static obstacles
            for (obstacle_prim, obstacle_handle) in self._static_obstacles.items():
                trans, rot = self._get_prim_pose_rel_robot_base(obstacle_prim)

                pose = self._get_pose3(trans, rot)
                self._world.set_pose(obstacle_handle, pose)

        self._robot_base_moved = False

    def set_robot_base_pose(self, robot_translation: np.array, robot_orientation: np.array) -> None:
        """Update position of the robot base. Until this function is called, Lula will assume the base pose
        to be at the origin with identity rotation.

        Args:
            robot_translation (np.array): (3 x 1) translation vector describing the translation of the robot base relative to the USD stage origin.
                The translation vector should be specified in the units of the USD stage
            robot_orientation (np.array): (4 x 1) quaternion describing the orientation of the robot base relative to the USD stage global frame
        """
        # all object poses are relative to the position of the robot base
        robot_translation = robot_translation * self._meters_per_unit
        robot_rot = quats_to_rot_matrices(robot_orientation)

        if np.any(self._robot_trans - robot_translation) or np.any(self._robot_rot - robot_rot):
            self._robot_base_moved = True
        else:
            self._robot_base_moved = False

        self._robot_trans = robot_translation
        self._robot_rot = robot_rot

        self._set_end_effector_target()

    def get_active_joints(self):
        return [
            self._robot_description.c_space_coord_name(i) for i in range(self._robot_description.num_c_space_coords())
        ]

    def get_watched_joints(self) -> List:
        """Lula does not currently support watching joint states that are not controllable

        Returns:
            (List): Always returns an empty list.
        """
        return []

    def get_end_effector_pose(self, active_joint_positions: np.array) -> Tuple[np.array, np.array]:
        """Return pose of robot end effector given current joint positions.
        The end effector position will be transformed into world coordinates based
        on the believed position of the robot base.  See set_robot_base_pose()

        Args:
            active_joint_positions (np.array): positions of the active joints in the robot

        Returns:
            Tuple[np.array,np.array]:
            end_effector_translation: (3x1) translation vector for the robot end effector
                 relative to the USD stage origin \n
            end_effector_rotation: (3x3) rotation matrix describing the orientation of the
                robot end effector relative to the USD global frame \n
        """
        # returns pose of end effector in world coordinates
        pose = self._kinematics.pose(np.expand_dims(active_joint_positions, 1), self.end_effector_frame_name)

        translation = self._robot_rot @ (pose.translation) + self._robot_trans
        rotation = self._robot_rot @ pose.rotation.matrix()
        return translation / self._meters_per_unit, rotation

    def set_end_effector_target(self, target_translation=None, target_orientation=None) -> None:
        if target_orientation is not None:
            target_rotation = quats_to_rot_matrices(target_orientation)
        else:
            target_rotation = None

        if target_translation is not None:
            self._end_effector_translation_target = target_translation * self._meters_per_unit
        else:
            self._end_effector_translation_target = None

        self._end_effector_rotation_target = target_rotation

        self._set_end_effector_target()

    def add_cuboid(
        self,
        cuboid: Union[objects.cuboid.DynamicCuboid, objects.cuboid.FixedCuboid, objects.cuboid.VisualCuboid],
        static: Optional[bool] = False,
    ):
        """Add a block obstacle.

        Args:
            cuboid (core.objects.cuboid): Wrapper object for handling rectangular prism Usd Prims.
            static (bool, optional): If True, indicate that cuboid will never change pose, and may be ignored in internal 
                world updates. Since Lula specifies object positions relative to the robot's frame 
                of reference, static obstacles will have their positions queried any time that 
                set_robot_base_pose() is called.  Defaults to False.


        Returns:
            bool: Always True, indicating that this adder has been implemented
        """

        if cuboid in self._static_obstacles or cuboid in self._dynamic_obstacles:
            carb.log_warn(
                "A cuboid was added twice to a Lula based MotionPolicy.  This has no effect beyond adding the cuboid once."
            )
            return False

        side_lengths = cuboid.get_size() * self._meters_per_unit

        trans, rot = self._get_prim_pose_rel_robot_base(cuboid)

        lula_cuboid = lula.create_obstacle(lula.Obstacle.Type.CUBE)
        lula_cuboid.set_attribute(lula.Obstacle.Attribute.SIDE_LENGTHS, side_lengths.astype(np.float64))
        lula_cuboid_pose = self._get_pose3(trans, rot)
        lula_cuboid_handle = self._world.add_obstacle(lula_cuboid, lula_cuboid_pose)

        if static:
            self._static_obstacles[cuboid] = lula_cuboid_handle
        else:
            self._dynamic_obstacles[cuboid] = lula_cuboid_handle

        return True

    def add_sphere(
        self, sphere: Union[objects.sphere.DynamicSphere, objects.sphere.VisualSphere], static: bool = False
    ) -> bool:
        """Add a sphere obstacle.

        Args:
            sphere (core.objects.sphere): Wrapper object for handling sphere Usd Prims.
            static (bool, optional): If True, indicate that sphere will never change pose, and may be ignored in internal 
                world updates. Since Lula specifies object positions relative to the robot's frame 
                of reference, static obstacles will have their positions queried any time that 
                set_robot_base_pose() is called.  Defaults to False.


        Returns:
            bool: Always True, indicating that this adder has been implemented
        """
        if sphere in self._static_obstacles or sphere in self._dynamic_obstacles:
            carb.log_warn(
                "A sphere was added twice to a Lula based MotionPolicy.  This has no effect beyond adding the sphere once."
            )
            return False

        radius = sphere.get_radius() * self._meters_per_unit
        trans, rot = self._get_prim_pose_rel_robot_base(sphere)

        lula_sphere = lula.create_obstacle(lula.Obstacle.Type.SPHERE)
        lula_sphere.set_attribute(lula.Obstacle.Attribute.RADIUS, radius)
        lula_sphere_pose = self._get_pose3(trans, rot)
        lula_sphere_handle = self._world.add_obstacle(lula_sphere, lula_sphere_pose)

        if static:
            self._static_obstacles[sphere] = lula_sphere_handle
        else:
            self._dynamic_obstacles[sphere] = lula_sphere_handle

        return True

    def add_capsule(
        self, capsule: Union[objects.capsule.DynamicCapsule, objects.capsule.VisualCapsule], static: bool = False
    ) -> bool:
        """Add a capsule obstacle.

        Args:
            capsule (core.objects.capsule): Wrapper object for handling capsule Usd Prims.
            static (bool, optional): If True, indicate that capsule will never change pose, and may be ignored in internal 
                world updates. Since Lula specifies object positions relative to the robot's frame 
                of reference, static obstacles will have their positions queried any time that 
                set_robot_base_pose() is called.  Defaults to False.

        Returns:
            bool: Always True, indicating that this function has been implemented
        """

        # As of Lula 0.5.0, what Lula calls a "cylinder" is actually a capsule (i.e., the surface
        # defined by the set of all points a fixed distance from a line segment).  This will be
        # corrected in a future release of Lula.

        if capsule in self._static_obstacles or capsule in self._dynamic_obstacles:
            carb.log_warn(
                "A capsule was added twice to a Lula based MotionPolicy.  This has no effect beyond adding the capsule once."
            )
            return False

        radius = capsule.get_radius() * self._meters_per_unit
        height = capsule.get_height() * self._meters_per_unit

        trans, rot = self._get_prim_pose_rel_robot_base(capsule)

        lula_capsule = lula.create_obstacle(lula.Obstacle.Type.CYLINDER)
        lula_capsule.set_attribute(lula.Obstacle.Attribute.RADIUS, radius)
        lula_capsule.set_attribute(lula.Obstacle.Attribute.HEIGHT, height)

        lula_capsule_pose = self._get_pose3(trans, rot)
        lula_capsule_handle = self._world.add_obstacle(lula_capsule, lula_capsule_pose)

        if static:
            self._static_obstacles[capsule] = lula_capsule_handle
        else:
            self._dynamic_obstacles[capsule] = lula_capsule_handle

        return True

    def add_ground_plane(
        self, ground_plane: objects.ground_plane.GroundPlane, plane_width: Optional[float] = 5000.0
    ) -> bool:
        """Add a ground_plane.  
        Lula does not support ground planes directly, and instead internally creates a cuboid with an
        expansive face (dimensions 200x200 stage units) coplanar to the ground_plane.

        Args:
            ground_plane (core.objects.ground_plane.GroundPlane): Wrapper object for handling ground_plane Usd Prims.
            plane_width (Optional[float]): The width of the ground plane that Lula creates to constrain this robot 

        Returns:
            bool: Always True, indicating that this adder has been implemented
        """
        if ground_plane in self._ground_plane_map:
            carb.log_warn(
                "A ground plane was added twice to a Lula based MotionPolicy.  This has no effect beyond adding the ground plane once."
            )
            return False

        # ignore the ground plane and make a block instead, as lula doesn't support ground planes

        prim_path = find_unique_string_name("/lula/ground_plane", lambda x: not is_prim_path_valid(x))
        lula_ground_plane_cuboid = objects.cuboid.VisualCuboid(prim_path, size=np.array([plane_width, plane_width, 1]))
        lula_ground_plane_cuboid.set_world_pose(*ground_plane.get_world_pose())
        lula_ground_plane_cuboid.set_visibility(False)

        self._ground_plane_map[ground_plane] = lula_ground_plane_cuboid
        self.add_cuboid(lula_ground_plane_cuboid, static=True)

        return True

    def disable_obstacle(self, obstacle: objects) -> bool:
        """Disable collision avoidance for obstacle.

        Args:
            obstacle (core.objects): obstacle to be disabled.

        Returns:
            bool: Return True if obstacle was identified and successfully disabled.
        """
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles:
            obstacle_handle = self._static_obstacles[obstacle]
        elif obstacle in self._ground_plane_map:
            obstacle_handle = self._static_obstacles[self._ground_plane_map[obstacle]]
        else:
            return False
        self._world.disable_obstacle(obstacle_handle)
        return True

    def enable_obstacle(self, obstacle: objects) -> bool:
        """Enable collision avoidance for obstacle.

        Args:
            obstacle (core.objects): obstacle to be enabled.

        Returns:
            bool: Return True if obstacle was identified and successfully enabled.
        """
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles:
            obstacle_handle = self._static_obstacles[obstacle]
        elif obstacle in self._ground_plane_map:
            obstacle_handle = self._static_obstacles[self._ground_plane_map[obstacle]]
        else:
            return False
        self._world.enable_obstacle(obstacle_handle)
        return True

    def remove_obstacle(self, obstacle: objects) -> bool:
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle (core.objects): obstacle to be removed.

        Returns:
            bool: Return True if obstacle was identified and successfully removed.
        """
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
            del self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles:
            obstacle_handle = self._static_obstacles[obstacle]
            del self._static_obstacles[obstacle]
        elif obstacle in self._ground_plane_map:
            lula_ground_plane_cuboid = self._ground_plane_map[obstacle]
            obstacle_handle = self._static_obstacles[lula_ground_plane_cuboid]
            delete_prim(lula_ground_plane_cuboid.prim_path)
            del self._static_obstacles[lula_ground_plane_cuboid]
            del self._ground_plane_map[obstacle]
        else:
            return False
        self._world.remove_obstacle(obstacle_handle)
        return True

    def reset(self):
        self._world = lula.create_world()
        self._dynamic_obstacles = dict()
        self._static_obstacles = dict()

        self._robot_base_moved = False
        self._robot_trans, self._robot_rot = np.zeros(3), np.eye(3)

        self._end_effector_translation_target = None
        self._end_effector_rotation_target = None

        self._end_effector_translation_target = None
        self._end_effector_rotation_target = None

        for lula_ground_plane_cuboid in self._ground_plane_map.values():
            delete_prim(lula_ground_plane_cuboid.prim_path)
        self._ground_plane_map = dict()

    def _get_prim_pose(self, prim: XFormPrim):
        pos, quat_rot = prim.get_world_pose()
        rot = quats_to_rot_matrices(quat_rot)
        pos *= self._meters_per_unit
        return pos, rot

    def _get_prim_pose_rel_robot_base(self, prim):
        # returns the position of a prim relative to the position of the robot
        trans, rot = self._get_prim_pose(prim)
        return self._get_pose_rel_robot_base(trans, rot)

    def _get_pose_rel_robot_base(self, trans, rot):
        inv_rob_rot = self._robot_rot.T

        if trans is not None:
            trans_rel = inv_rob_rot @ (trans - self._robot_trans)
        else:
            trans_rel = None

        if rot is not None:
            rot_rel = inv_rob_rot @ rot
        else:
            rot_rel = None

        return trans_rel, rot_rel

    def _get_pose3(self, trans=None, rot=None):
        if trans is None and rot is None:
            return lula.Pose3()

        if trans is None:
            return lula.Pose3.from_rotation(lula.Rotation3(rot))

        if rot is None:
            return lula.Pose3.from_translation(trans)

        return lula.Pose3(lula.Rotation3(rot), trans)

    def _set_end_effector_target(self):
        """
        This function exists to be overwritten by a child class because
        self.set_end_effector_target() is a public function that calls this internal function at the end
        so that, for example, the RMPflow object can call its set_target function at the right time
        """
        carb.log_error("Unimplemented _set_end_effector_target() function was never supposed to be called")
        return True
