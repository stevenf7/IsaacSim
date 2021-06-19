# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import math

from pxr import Gf
from . import math_utils
from omni.isaac.dynamic_control import _dynamic_control


class RobotController:
    def __init__(
        self,
        stage,
        timeline,
        dc,
        articulation_path,
        odom_prim_path,
        wheel_joint_names,
        wheel_speed,
        goal_offset_threshold,
    ):
        self._stage = stage
        self._timeline = timeline
        self._dc = dc
        self._articulation_path = articulation_path
        self._odom_prim_path = odom_prim_path
        self._wheel_joint_names = wheel_joint_names
        self._wheel_speed = wheel_speed
        self._goal_offset_threshold = goal_offset_threshold
        self._reached_goal = [False, False]
        self._enable_navigation = False
        self._goal = [400, 400, 0]
        self._go_forward = False

    def _get_odom_data(self):
        self.imu = self._dc.get_rigid_body(self._odom_prim_path)
        imu_pose = self._dc.get_rigid_body_pose(self.imu)
        roll, pitch, yaw = math_utils.quaternionToEulerAngles(
            Gf.Quaternion(imu_pose.r.w, Gf.Vec3d(imu_pose.r.x, imu_pose.r.y, imu_pose.r.z))
        )
        self.current_robot_translation = [imu_pose.p.x, imu_pose.p.y, imu_pose.p.z]
        self.current_robot_orientation = [roll, pitch, yaw]

    def update(self, step):
        if self._enable_navigation and self._timeline.is_playing():
            self._get_odom_data()
            inc_x = float(self._goal[0]) - self.current_robot_translation[0]
            inc_y = float(self._goal[1]) - self.current_robot_translation[1]
            angle_to_goal = math.atan2(inc_y, inc_x)

            # Check if translation goal is reached
            if abs(inc_x) <= self._goal_offset_threshold[0] and abs(inc_y) <= self._goal_offset_threshold[0]:
                self._reached_goal[0] = True

            # If translation goal is not reached, point towards it and then move forward
            if self._reached_goal[0] == False:
                # Check if robot point towards goal before moving forward
                delta_orientation = angle_to_goal - self.current_robot_orientation[2]
                speed_multiplier = abs(delta_orientation) / (2 * math.pi)
                if delta_orientation > self._goal_offset_threshold[1] and self._go_forward == False:
                    # Rotate in-place anti-clockwise
                    self.control_command(
                        -speed_multiplier * self._wheel_speed[0], speed_multiplier * self._wheel_speed[1]
                    )
                elif delta_orientation < -self._goal_offset_threshold[1] and self._go_forward == False:
                    # Rotate in-place clockwise
                    self.control_command(
                        speed_multiplier * self._wheel_speed[0], -speed_multiplier * self._wheel_speed[1]
                    )
                else:
                    # Move forward and turn if it deviates
                    self._go_forward = True
                    if delta_orientation > self._goal_offset_threshold[1] and delta_orientation < math.pi:
                        self.control_command(-self._wheel_speed[0], self._wheel_speed[1])
                    elif delta_orientation < -self._goal_offset_threshold[1] and delta_orientation > -math.pi:
                        self.control_command(self._wheel_speed[0], -self._wheel_speed[1])
                    elif (
                        delta_orientation > (-2 * math.pi + self._goal_offset_threshold[1])
                        and delta_orientation < -math.pi
                    ):
                        self.control_command(-self._wheel_speed[0], self._wheel_speed[1])
                    elif (
                        delta_orientation < (2 * math.pi - self._goal_offset_threshold[1])
                        and delta_orientation > math.pi
                    ):
                        self.control_command(self._wheel_speed[0], -self._wheel_speed[1])
                    else:
                        self.control_command(self._wheel_speed[0], self._wheel_speed[1])

            # Translation goal reached but not rotational goal
            if self._reached_goal[0] == True and self._reached_goal[1] == False:
                angle_to_goal_orientation = math.radians(self._goal[2]) - self.current_robot_orientation[2]
                speed_multiplier = abs(angle_to_goal_orientation) / (2 * math.pi)
                if angle_to_goal_orientation > self._goal_offset_threshold[1]:
                    # Rotate in-place anti-clockwise
                    self.control_command(
                        -speed_multiplier * self._wheel_speed[0], speed_multiplier * self._wheel_speed[1]
                    )
                elif angle_to_goal_orientation < -self._goal_offset_threshold[1]:
                    # Rotate in-place clockwise
                    self.control_command(
                        speed_multiplier * self._wheel_speed[0], -speed_multiplier * self._wheel_speed[1]
                    )
                else:
                    self._reached_goal[1] = True

            # Both goals reached
            if self._reached_goal[0] == True and self._reached_goal[1] == True:
                self.control_command(0, 0)
                self._reached_goal = [False, False]
                self._enable_navigation = False
                self._go_forward = False

    def control_setup(self):
        self.ar = self._dc.get_articulation(self._articulation_path)
        self.wheel_left = self._dc.find_articulation_dof(self.ar, self._wheel_joint_names[0])
        self.wheel_right = self._dc.find_articulation_dof(self.ar, self._wheel_joint_names[1])

        self.vel_props = _dynamic_control.DofProperties()
        self.vel_props.drive_mode = _dynamic_control.DRIVE_VEL
        self.vel_props.damping = 1e7
        self.vel_props.stiffness = 0
        self._dc.set_dof_properties(self.wheel_left, self.vel_props)
        self._dc.set_dof_properties(self.wheel_right, self.vel_props)

    def control_command(self, left_wheel_speed, right_wheel_speed):
        # Wake up articulation every move command to ensure commands are applied
        self._dc.wake_up_articulation(self.ar)
        self._dc.set_dof_velocity_target(self.wheel_left, left_wheel_speed)
        self._dc.set_dof_velocity_target(self.wheel_right, right_wheel_speed)

    def set_goal(self, x, y, theta):
        self._goal = [x, y, theta]

    def get_goal(self):
        return self._goal

    def enable_navigation(self, flag):
        self._enable_navigation = flag

    def reached_goal(self):
        if self._reached_goal[0] is True and self._reached_goal[1] is True:
            return True
        else:
            return False
