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


class LulaMotionPolicy(MotionPolicy):

    """
    Motion policies that use lula motion planning methods with a lula world
    """

    def __init__(self, _stage, policy_type, robot_description_path, urdf_path, robot_prim):
        super().__init__(_stage, policy_type)
        self._world = lula.create_world()
        self._dynamic_obstacles = dict()
        self._static_obstacles = dict()

        self._robot_description = lula.load_robot(robot_description_path, urdf_path)
        self._kinematics = self._robot_description.kinematics()
        self._robot_prim = robot_prim
        self._robot_pos, self._robot_rot = self.get_prim_pose(
            robot_prim, default_trans=np.zeros(3), default_rot=np.eye(3)
        )

    def update_world(self, updated_obstacles=None, robot_base_moved=False):
        if updated_obstacles is None or robot_base_moved:
            # assume that all obstacle poses need to be updated
            updated_obstacles = self._dynamic_obstacles.keys()

        inv_rob_rot = np.linalg.inv(self._robot_rot)

        for obstacle_prim in updated_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
            trans, rot = self.get_prim_pose(obstacle_prim)

            # transform obstacle poses reltive to robot base position
            rot_rel = inv_rob_rot @ rot
            trans_rel = inv_rob_rot @ (trans - self._robot_pos)

            pose = self.get_pose3(trans_rel, rot_rel)
            self._world.set_pose(obstacle_handle, pose)

        if robot_base_moved:
            # update static obstacles
            for (obstacle_prim, obstacle_handle) in self._static_obstacles.items():
                trans, rot = self.get_prim_pose(obstacle_prim)

                # transform obstacle poses reltive to robot base position
                rot_rel = inv_rob_rot @ rot
                trans_rel = inv_rob_rot @ (trans - self._robot_pos)

                pose = self.get_pose3(trans_rel, rot_rel)
                self._world.set_pose(obstacle_handle, pose)

    def get_active_joints(self):
        return [
            self._robot_description.c_space_coord_name(i) for i in range(self._robot_description.num_c_space_coords())
        ]

    def update_robot_base_pose(self):
        # all object poses are relative to the position of the robot base
        pos, rot = self.get_prim_pose(self._robot_prim, default_trans=np.zeros(3), default_rot=np.eye(3))
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
        return translation, rotation

    def get_pose_rel_robot_base(self, trans, rot):
        """
        Args:
            trans: translation in world coordinates
            rot: rotation in world coordinates
        Return:
            trans_rel: translation relative to the robot base
            rot_rel: rotation relative to the robot base

        """
        inv_rob_rot = np.linalg.inv(self._robot_rot)

        if trans is not None:
            trans_rel = inv_rob_rot @ (trans - self._robot_pos)
        else:
            trans_rel = None

        if rot is not None:
            rot_rel = inv_rob_rot @ rot
        else:
            rot_rel = None

        return trans_rel, rot_rel

    def get_prim_pose_rel_robot_base(self, prim, default_trans=np.zeros(3), default_rot=np.eye(3)):
        # returns the position of a prim relative to the position of the robot
        trans, rot = self.get_prim_pose(prim, default_trans=default_trans, default_rot=default_rot)
        return self.get_pose_rel_robot_base(trans, rot)

    def create_cube(self, block_prim, side_length=None, static=False):
        if not block_prim.HasProperty("size") and side_length is None:
            return False
        if side_length is None:
            side_length = block_prim.GetProperty("size").Get()
        side_length *= self._meters_per_unit
        trans, rot = self.get_prim_pose(block_prim)

        box_obstacle = lula.create_obstacle(lula.Obstacle.Type.CUBE)
        box_obstacle.set_attribute(lula.Obstacle.Attribute.SIDE_LENGTHS, side_length * np.ones(3))
        box_obstacle_pose = self.get_pose3(trans, rot)
        cube = self._world.add_obstacle(box_obstacle, box_obstacle_pose)

        if static:
            self._static_obstacles[block_prim] = cube
        else:
            self._dynamic_obstacles[block_prim] = cube

        return True

    def create_block(self, block_prim, dimensions=None, static=False):
        if dimensions is None and not (block_prim.HasAttribute("xformOp:scale") and block_prim.HasAttribute("size")):
            return False
        elif dimensions is None:
            size = block_prim.GetAttribute("size").Get()
            scale = block_prim.GetAttribute("xformOp:scale").Get()
            dimensions = size * np.array(scale)

        dimensions = np.array(dimensions, dtype=np.float64)

        side_lengths = self._meters_per_unit * dimensions
        trans, rot = self.get_prim_pose(block_prim)

        box_obstacle = lula.create_obstacle(lula.Obstacle.Type.CUBE)
        box_obstacle.set_attribute(lula.Obstacle.Attribute.SIDE_LENGTHS, side_lengths)
        box_obstacle_pose = self.get_pose3(trans, rot)
        block = self._world.add_obstacle(box_obstacle, box_obstacle_pose)

        if static:
            self._static_obstacles[block_prim] = block
        else:
            self._dynamic_obstacles[block_prim] = block

        return True

    def create_sphere(self, sphere_prim, radius=None, static=False):
        if not sphere_prim.HasProperty("radius") and radius is None:
            return False
        if radius is None:
            radius = sphere_prim.GetProperty("radius").Get()
        radius *= self._meters_per_unit
        trans, rot = self.get_prim_pose(sphere_prim)

        sphere_obstacle = lula.create_obstacle(lula.Obstacle.Type.SPHERE)
        sphere_obstacle.set_attribute(lula.Obstacle.Attribute.RADIUS, radius)
        sphere_obstacle_pose = self.get_pose3(trans, rot)
        sphere = self._world.add_obstacle(sphere_obstacle, sphere_obstacle_pose)

        if static:
            self._static_obstacles[sphere_prim] = sphere
        else:
            self._dynamic_obstacles[sphere_prim] = sphere

        return True

    def create_capsule(self, capsule_prim, radius=None, height=None, static=False):
        # As of Lula 0.5.0, what Lula calls a "cylinder" is actually a capsule (i.e., the surface
        # defined by the set of all points a fixed distance from a line segment).  This will be
        # corrected in a future release of Lula.

        if (not capsule_prim.HasProperty("radius") and radius is None) or (
            not capsule_prim.HasProperty("height") and height is None
        ):
            return False

        if radius is None:
            radius = capsule_prim.GetProperty("radius").Get() * self._meters_per_unit
        if height is None:
            height = capsule_prim.GetProperty("height").Get() * self._meters_per_unit

        trans, rot = self.get_prim_pose(capsule_prim)

        capsule_obstacle = lula.create_obstacle(lula.Obstacle.Type.CYLINDER)
        capsule_obstacle.set_attribute(lula.Obstacle.Attribute.RADIUS, radius)
        capsule_obstacle.set_attribute(lula.Obstacle.Attribute.HEIGHT, height)

        capsule_obstacle_pose = self.get_pose3(trans, rot)
        capsule = self._world.add_obstacle(capsule_obstacle, capsule_obstacle_pose)

        if static:
            self._static_obstacles[capsule_prim] = capsule
        else:
            self._dynamic_obstacles[capsule_prim] = capsule

        return True

    def disable_obstacle(self, obstacle_prim):
        if obstacle_prim in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
        elif obstacle_prim in self._static_obstacles[obstacle_prim]:
            obstacle_handle = self._static_obstacles[obstacle_prim]
        else:
            return False
        self._world.disable_obstacle(obstacle_handle)
        return True

    def enable_obstacle(self, obstacle_prim):
        if obstacle_prim in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
        elif obstacle_prim in self._static_obstacles[obstacle_prim]:
            obstacle_handle = self._static_obstacles[obstacle_prim]
        else:
            return False
        self._world.enable_obstacle(obstacle_handle)
        return True

    def remove_obstacle(self, obstacle_prim):
        if obstacle_prim in self._dynamic_obstacles:
            obstacle_handle = self._dynamic_obstacles[obstacle_prim]
            del self._dynamic_obstacles[obstacle_prim]
        elif obstacle_prim in self._static_obstacles[obstacle_prim]:
            obstacle_handle = self._static_obstacles[obstacle_prim]
            del self._static_obstacles[obstacle_prim]
        else:
            return False
        self._world.remove_obstacle(obstacle_handle)
        return True

    def set_static(self, obstacle_prim, is_static):
        if is_static:
            if obstacle_prim in self._dynamic_obstacles:
                self._static_obstacles[obstacle_prim] = self._dynamic_obstacles[obstacle_prim]
                del self._dynamic_obstacles[obstacle_prim]
        else:
            if obstacle_prim in self._static_obstacles:
                self._dynamic_obstacles[obstacle_prim] = self._static_obstacles[obstacle_prim]
                del self._static_obstacles[obstacle_prim]

    def get_pose3(self, trans=None, rot=None):
        if trans is None and rot is None:
            return lula.Pose3()

        if trans is None:
            return lula.Pose3.from_rotation(rot)

        if rot is None:
            return lula.Pose3.from_translation(trans)

        return lula.Pose3(lula.Rotation3(rot), trans)


class RmpFlow(LulaMotionPolicy):
    def __init__(self, policy_config, _stage, robot_prim):
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

        super().__init__(_stage, policy_type, robot_description_path, urdf_path, robot_prim)

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

    def set_end_effector_target(self, target_prim, position_only=False):
        self._target_prim = target_prim
        self._target_prim_is_position_only = position_only

        self.update_target()

    def update_target(self):
        if self._target_prim is None:
            self._policy.clear_end_effector_position_attractor()
            self._policy.clear_end_effector_orientation_attractor()
            return

        trans, rot = self.get_prim_pose_rel_robot_base(self._target_prim, default_trans=None, default_rot=None)

        if self._target_prim_is_position_only:
            self._policy.set_end_effector_position_attractor(trans)
            self._policy.clear_end_effector_orientation_attractor()
        else:
            if rot is not None:
                self._policy.set_end_effector_orientation_attractor(lula.Rotation3(rot))
            else:
                self._policy.clear_end_effector_orientation_attractor()
            self._policy.set_end_effector_position_attractor(trans)

    def update_world(self, updated_obstacles=None, robot_pose_changed=False):
        super().update_world(updated_obstacles, robot_pose_changed)
        self._policy.update_world_view()

    def update(self, updated_obstacles=None):
        robot_pose_changed = self.update_robot_base_pose()  # base pose of robot
        self.update_target()
        self.update_world(updated_obstacles, robot_pose_changed)

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
        joint_accel = np.zeros_like(joint_positions)
        self._policy.eval_accel(joint_positions, joint_velocities, joint_accel)
        return joint_accel
