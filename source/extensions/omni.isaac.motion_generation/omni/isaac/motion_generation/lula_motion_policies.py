# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import lula
import time
import numpy as np
from pxr import UsdGeom
from enum import Enum
import carb
from .motion_policy_interface import *
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core import objects


class LulaMotionPolicy(MotionPolicy):

    """
    Motion policies that use lula motion planning methods with a lula world
    """

    def __init__(self, policy_type, robot_description_path, urdf_path, robot_articulation):
        super().__init__(policy_type)
        self._world = lula.create_world()
        self._dynamic_obstacles = dict()
        self._static_obstacles = dict()

        self._meters_per_unit = get_stage_units()

        self._robot_description = lula.load_robot(robot_description_path, urdf_path)
        self._kinematics = self._robot_description.kinematics()
        self._robot_articulation = robot_articulation
        self._robot_pos, self._robot_rot = self._get_prim_pose(robot_articulation)

        self._end_effector_translation_target = None
        self._end_effector_rotation_target = None

        self._end_effector_translation_target = None
        self._end_effector_rotation_target = None

    def update_world(self, updated_obstacles=None, robot_base_moved=False):
        if updated_obstacles is None or robot_base_moved:
            # assume that all obstacle poses need to be updated
            updated_obstacles = self._dynamic_obstacles.keys()

        for obstacle_prim in updated_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
            trans, rot = self._get_prim_pose_rel_robot_base(obstacle_prim)

            pose = self._get_pose3(trans, rot)
            self._world.set_pose(obstacle_handle, pose)

        if robot_base_moved:
            # update static obstacles
            for (obstacle_prim, obstacle_handle) in self._static_obstacles.items():
                trans, rot = self._get_prim_pose_rel_robot_base(obstacle_prim)

                pose = self._get_pose3(trans, rot)
                self._world.set_pose(obstacle_handle, pose)

    def get_active_joints(self):
        return [
            self._robot_description.c_space_coord_name(i) for i in range(self._robot_description.num_c_space_coords())
        ]

    def update_robot_base_pose(self):
        # all object poses are relative to the position of the robot base
        pos, rot = self._get_prim_pose(self._robot_articulation)

        if np.any(self._robot_pos - pos) or np.any(self._robot_rot - rot):
            base_moved = True
        else:
            base_moved = False

        self._robot_pos = pos
        self._robot_rot = rot

        return base_moved

    def get_end_effector_pose(self, joint_positions):
        # returns pose of end effector in world coordinates
        pose = self._kinematics.pose(np.expand_dims(joint_positions, 1), self.end_effector_frame_name)

        translation = self._robot_rot @ (pose.translation) + self._robot_pos
        rotation = self._robot_rot @ pose.rotation.matrix()
        return translation / self._meters_per_unit, rotation

    def get_pose_rel_robot_base(self, trans, rot):
        """
        Args:
            trans: translation in world coordinates
            rot: rotation in world coordinates
        Return:
            trans_rel: translation relative to the robot base
            rot_rel: rotation relative to the robot base

        """
        inv_rob_rot = self._robot_rot.T

        if trans is not None:
            trans_rel = inv_rob_rot @ (trans - self._robot_pos)
        else:
            trans_rel = None

        if rot is not None:
            rot_rel = inv_rob_rot @ rot
        else:
            rot_rel = None

        return trans_rel, rot_rel

    def set_end_effector_target(self, target_translation=None, target_orientation=None) -> None:
        if target_orientation is not None:
            target_rotation = quat_to_rot_matrix(target_orientation)
        else:
            target_rotation = None

        if target_translation is not None:
            self._end_effector_translation_target = target_translation * self._meters_per_unit
        self._end_effector_rotation_target = target_rotation

    def add_cuboid(self, cuboid, static=False):
        side_lengths = cuboid.get_size() * self._meters_per_unit

        trans, rot = self._get_prim_pose(cuboid)

        box_obstacle = lula.create_obstacle(lula.Obstacle.Type.CUBE)
        box_obstacle.set_attribute(lula.Obstacle.Attribute.SIDE_LENGTHS, side_lengths.astype(np.float64))
        box_obstacle_pose = self._get_pose3(trans, rot)
        block = self._world.add_obstacle(box_obstacle, box_obstacle_pose)

        if static:
            self._static_obstacles[cuboid] = block
        else:
            self._dynamic_obstacles[cuboid] = block

        return True

    def add_sphere(self, sphere, static=False):
        radius = capsule.get_radius() * self._meters_per_unit
        trans, rot = self._get_prim_pose(sphere)

        sphere_obstacle = lula.create_obstacle(lula.Obstacle.Type.SPHERE)
        sphere_obstacle.set_attribute(lula.Obstacle.Attribute.RADIUS, radius.astype(np.float64))
        sphere_obstacle_pose = self._get_pose3(trans, rot)
        sphere = self._world.add_obstacle(sphere_obstacle, sphere_obstacle_pose)

        if static:
            self._static_obstacles[sphere] = sphere
        else:
            self._dynamic_obstacles[sphere] = sphere

        return True

    def add_capsule(self, capsule, static=False):
        # As of Lula 0.5.0, what Lula calls a "cylinder" is actually a capsule (i.e., the surface
        # defined by the set of all points a fixed distance from a line segment).  This will be
        # corrected in a future release of Lula.

        radius = capsule.get_radius() * self._meters_per_unit
        height = capsule.get_height() * self._meters_per_unit

        trans, rot = self._get_prim_pose(capsule)

        capsule_obstacle = lula.create_obstacle(lula.Obstacle.Type.CYLINDER)
        capsule_obstacle.set_attribute(lula.Obstacle.Attribute.RADIUS, radius.astype(np.float64))
        capsule_obstacle.set_attribute(lula.Obstacle.Attribute.HEIGHT, height.astype(np.float64))

        capsule_obstacle_pose = self._get_pose3(trans, rot)
        capsule = self._world.add_obstacle(capsule_obstacle, capsule_obstacle_pose)

        if static:
            self._static_obstacles[capsule] = capsule
        else:
            self._dynamic_obstacles[capsule] = capsule

        return True

    def add_ground_plane(self, ground_plane):
        # ignore the ground plane and make a block instead, as lula doesn't support ground planes

        cuboid = objects.cuboid.VisualCuboid("/lula/ground_plane", size=np.array([200, 200, 1]))
        cuboid.set_world_pose(np.array([0, 0, -0.5]))
        cuboid.set_visibility(False)
        self.add_cuboid(cuboid, static=True)

    def disable_obstacle(self, obstacle):
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles[obstacle]:
            obstacle_handle = self._static_obstacles[obstacle]
        else:
            return False
        self._world.disable_obstacle(obstacle_handle)
        return True

    def enable_obstacle(self, obstacle):
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles[obstacle]:
            obstacle_handle = self._static_obstacles[obstacle]
        else:
            return False
        self._world.enable_obstacle(obstacle_handle)
        return True

    def remove_obstacle(self, obstacle):
        if obstacle in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle]
            del self._dynamic_obstacles[obstacle]
        elif obstacle in self._static_obstacles[obstacle]:
            obstacle_handle = self._static_obstacles[obstacle]
            del self._static_obstacles[obstacle]
        else:
            return False
        self._world.remove_obstacle(obstacle_handle)
        return True

    def _get_prim_pose(self, prim: XFormPrim):
        pos, quat_rot = prim.get_world_pose()
        rot = quat_to_rot_matrix(quat_rot)
        pos *= self._meters_per_unit
        return pos, rot

    def _get_prim_pose_rel_robot_base(self, prim):
        # returns the position of a prim relative to the position of the robot
        trans, rot = self._get_prim_pose(prim)
        return self.get_pose_rel_robot_base(trans, rot)

    def _get_pose3(self, trans=None, rot=None):
        if trans is None and rot is None:
            return lula.Pose3()

        if trans is None:
            return lula.Pose3.from_rotation(lula.Rotation3(rot))

        if rot is None:
            return lula.Pose3.from_translation(trans)

        return lula.Pose3(lula.Rotation3(rot), trans)


class RmpFlow(LulaMotionPolicy):
    def __init__(self, policy_config, robot_articulation):
        if "robot_description_path" not in policy_config:
            carb.log_error("robot_description_path is missing in RMPflow config")
            return
        if "urdf_path" not in policy_config:
            carb.log_error("urdf_path is missing in RMPflow config")
            return
        if "rmpflow_config_path" not in policy_config:
            carb.log_error("rmpflow_config_path is missing in RMPflow config")
            return
        if "end_effector_frame_name" not in policy_config:
            carb.log_error("end_effector_frame_name is missing in RMPflow config")
            return

        """
        evaluations_per_frame (int) sets the number of times that RMPflow is evaluated to produce a target
        for the controller once per frame.  The RMPflow acceleration policy is converted to a velocity
        policy through integration with sub_frame timesteps
        """
        if "evaluations_per_frame" not in policy_config:
            carb.log_error("evaluations_per_frame is missing in RMPflow config")
            return

        self.evaluations_per_frame = policy_config["evaluations_per_frame"]

        if self.evaluations_per_frame // 1 != self.evaluations_per_frame or self.evaluations_per_frame < 1:
            carb.log_error("evaluations_per_frame must be a positive integer in the RMPflow config file")
            return

        """
        ignore_robot_state_updates (bool) toggles whether RMPflow updates the robot position during
            rollouts based on the feedback from _dynamic_control.  
        If False: At every frame, the RMPflow internal robot state will be set to the current robot
            state returned by _dynamic_control.  In this case, RMPflow will return velocity targets
            because setting position targets very close to the current position causes slow movement
            in _dynamic_control.
        If True: The internal robot state will only be updated when set_target() is called.  While following
            a given target, RMPflow will maintain its own robot state using forward integration.  In this case
            RMPflow will return position targets to ensure that the error between its internal robot state and 
            the real robot state remains low (as _dynamic_control will follow the targets with PD control).
        """
        if "ignore_robot_state_updates" not in policy_config:
            carb.log_error("ignore_robot_state is missing in RMPflow config")
            return

        self.ignore_robot_state_updates = policy_config["ignore_robot_state_updates"]
        if self.ignore_robot_state_updates:
            policy_type = PolicyType.POSITION
        else:
            policy_type = PolicyType.VELOCITY

        robot_description_path = policy_config["robot_description_path"]
        urdf_path = policy_config["urdf_path"]

        self.end_effector_frame_name = policy_config["end_effector_frame_name"]

        super().__init__(policy_type, robot_description_path, urdf_path, robot_articulation)

        rmpflow_config_path = policy_config["rmpflow_config_path"]

        # Create RMPflow configuration.
        rmpflow_config = lula.create_rmpflow_config(
            rmpflow_config_path, self._robot_description, self.end_effector_frame_name, self._world.add_world_view()
        )

        # Create RMPflow policy.
        self._policy = lula.create_rmpflow(rmpflow_config)

        self._robot_joint_positions = None
        self._robot_joint_velocities = None

        self.set_initialized()

    def set_cspace_target(self, target):
        self._policy.set_cspace_target(target.astype(np.float64))

    def _set_end_effector_target(self):
        target_translation = self._end_effector_translation_target
        target_rotation = self._end_effector_rotation_target

        if target_translation is None and target_rotation is None:
            self._policy.clear_end_effector_position_attractor()
            self._policy.clear_end_effector_orientation_attractor()
            return

        trans, rot = self.get_pose_rel_robot_base(target_translation, target_rotation)

        if trans is not None:
            self._policy.set_end_effector_position_attractor(trans)
        else:
            self._policy.clear_end_effector_position_attractor()

        if rot is not None:
            self._policy.set_end_effector_orientation_attractor(lula.Rotation3(rot))
        else:
            self._policy.clear_end_effector_orientation_attractor()

    def update_world(self, updated_obstacles=None, robot_pose_changed=False):
        super().update_world(updated_obstacles, robot_pose_changed)
        self._policy.update_world_view()

    def update(self, updated_obstacles=None):
        robot_pose_changed = self.update_robot_base_pose()  # pose of robot base
        self.update_world(updated_obstacles, robot_pose_changed)
        self._set_end_effector_target()

    def get_joint_velocity_targets(self, joint_positions, joint_velocities, frame_duration):
        self._update_robot_joint_states(joint_positions, joint_velocities, frame_duration)
        return self._robot_joint_velocities

    def get_joint_position_targets(self, joint_positions, joint_velocities, frame_duration):
        self._update_robot_joint_states(joint_positions, joint_velocities, frame_duration)
        return self._robot_joint_positions

    def _update_robot_joint_states(self, joint_positions, joint_velocities, frame_duration):
        """
        Args:
            joint_positions: queried from _dynamic_control
            joint_velocities: queried from _dynamic_control
            frame_duration: duration of one simulation frame (sec)

        The internal robot joint states are either updated based on the previous internal states
        or the state passed in by _dynamic_control.
        """
        if (
            self._robot_joint_positions is None
            or self._robot_joint_velocities is None
            or not self.ignore_robot_state_updates
        ):
            self._robot_joint_positions, self._robot_joint_velocities = self._euler_integration(
                joint_positions, joint_velocities, frame_duration
            )
        else:
            self._robot_joint_positions, self._robot_joint_velocities = self._euler_integration(
                self._robot_joint_positions, self._robot_joint_velocities, frame_duration
            )

    def _euler_integration(self, joint_positions, joint_velocities, frame_duration):
        policy_timestep = frame_duration / self.evaluations_per_frame

        for i in range(self.evaluations_per_frame):
            joint_accel = self._evaluate_acceleration(joint_positions, joint_velocities)
            joint_positions += policy_timestep * joint_velocities
            joint_velocities += policy_timestep * joint_accel

        return joint_positions, joint_velocities

    def _evaluate_acceleration(self, joint_positions, joint_velocities):
        joint_positions = joint_positions.astype(np.float64)
        joint_velocities = joint_velocities.astype(np.float64)
        joint_accel = np.zeros_like(joint_positions)
        self._policy.eval_accel(joint_positions, joint_velocities, joint_accel)
        return joint_accel
