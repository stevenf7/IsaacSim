from omni.isaac.motion_generation import MotionGenerator
import carb
import json
import os
import omni
import franka
import math

import rospy
from std_msgs.msg import Bool, Header
from lula_ros.msg import JointPosVelAccCommand, LulaCommandAck


class CycleTime:
    def __init__(self, time, period=None):
        self.time = time
        self.period = period
        if period is None:
            self.is_period_available = False
        else:
            self.is_period_available = True


class SynchronizedTime:
    def __init__(self):
        self.sub = rospy.Subscriber("/rmpflow/commands/joint_command/ack", LulaCommandAck, self.callback)
        self.latest_message = LulaCommandAck()
        self.is_first = True
        self.cycle_start_time = rospy.Time.now()
        self.current_offset = rospy.Duration(0)

    def __del__(self):
        self.sub.unregister()

    def callback(self, data):
        self.latest_message = data

    def next_adaptive_cycle_time(self):
        now = self.now_nonblocking()

        if self.is_first:
            self.is_first = False
            ret = CycleTime(now)
        else:
            command_period = now - self.cycle_start_time
            ret = CycleTime(now, command_period)

            new_offset_measurement = self.latest_message.time_offset.to_sec()
            nominal_eps = math.pow(0.9999, 250.0)
            reg_decay = math.pow(nominal_eps, command_period.to_sec())
            ss = command_period.to_sec()
            self.current_offset = rospy.Duration(reg_decay * self.current_offset.to_sec() + ss * new_offset_measurement)

        self.cycle_start_time = now
        return ret

    def now_nonblocking(self):
        return rospy.Time.now() + self.current_offset


class ROSJointCommander:
    def __init__(self, stage, dc):
        self.mg = MotionGenerator(dc, stage)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.motion_generation")
        mg_extension_path = ext_manager.get_extension_path(ext_id)

        polciy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(polciy_config_dir, "policy_map.json")) as policy_map:
            policy_map = json.load(policy_map)

        config_path = os.path.join(polciy_config_dir, policy_map["Franka"]["RMPflow"])
        self.config = self.process_policy_config(config_path)
        self.robot = None
        self.next_id = 0
        self.frame = 0
        self.start_time = rospy.Time.now()
        self.synced_time = SynchronizedTime()
        self.command_time = rospy.Time.now()
        self.controller_time_offset = rospy.Time.now()
        self.prev_t = rospy.Time.now()
        self.is_suppressed = False
        self.interpolated_state = None
        self.suppression_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/suppress", Bool, self.suppression_callback
        )
        self.interpolated_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/interpolated", JointPosVelAccCommand, self.interpolated_command_callback
        )
        self.joint_command_pub = rospy.Publisher(
            "/rmpflow/commands/joint_command", JointPosVelAccCommand, queue_size=10
        )

    def __del__(self):
        self.suppression_sub.unregister()
        self.interpolated_sub.unregister()
        self.joint_command_pub.unregister()

    def register(self, robot: franka.Panda, target_prim):
        self.mg.initialize(self.config, robot.prim, 60)
        self.mg.set_end_effector_target(target_prim)
        self.robot = robot
        self.dof_states = robot.joint_states

    def process_policy_config(self, mp_path):
        with open(os.path.join(mp_path, "config.json")) as mp_config_file:
            config = json.load(mp_config_file)

        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_path, v)

        return config

    def suppression_callback(self, data):
        self.is_suppressed = data.data

    def interpolated_command_callback(self, data):
        self.interpolated_state = data

    def get_latest_interpolated_dof_states(self):
        if self.interpolated_state is not None:
            for j in range(self.robot.num_joints):
                index = self.robot.joint_indices[j]
                self.dof_states["pos"][index] = self.interpolated_state.q[j]
                self.dof_states["vel"][index] = self.interpolated_state.qd[j]
            return self.dof_states
        else:
            return None

    def update(self):
        if self.is_suppressed:
            # interpolator is telling us to ignore RMPs and instead set the internal state to the "physical" robot
            states = self.get_latest_interpolated_dof_states()  # return None until we get the first message
            if states is not None:
                self.robot.joint_states = states
            self.joint_positions, self.joint_velocities, self.joint_accel = self.mg.get_joint_states()
            carb.log_warn("rmp's suppressed by interpolator")
        else:
            # Step the RMPs forward based on timing from the interpolator rosnode
            adaptive_cycle = self.synced_time.next_adaptive_cycle_time()
            self.command_time = adaptive_cycle.time
            integration_dt = self.mg.sim_timestep / self.mg.policy_evals_per_frame
            if adaptive_cycle.is_period_available:
                integration_dt = adaptive_cycle.period.to_sec() / self.mg.policy_evals_per_frame

            self.mg._motion_policy.update()

            self.joint_positions, self.joint_velocities, self.joint_accel = self.mg.get_joint_states()

            dji = self.mg._active_joint_inds

            for i in range(self.mg.policy_evals_per_frame):
                self.joint_accel[dji] = self.mg._motion_policy.evaluate_acceleration(
                    self.joint_positions[dji], self.joint_velocities[dji]
                )
                self.joint_positions[dji] += integration_dt * self.joint_velocities[dji]
                self.joint_velocities[dji] += integration_dt * self.joint_accel[dji]

            self.robot.set_velocity_targets(self.joint_velocities)
            self.joint_command_pub.publish(self.get_joint_pos_vel_acc_command())
        self.frame = self.frame + 1

    def get_joint_pos_vel_acc_command(self):
        message = JointPosVelAccCommand()
        if self.next_id == 0:
            message.period = rospy.Duration(0)
        else:
            message.period = self.command_time - self.prev_t

        message.id = self.next_id

        message.header = Header()
        message.header.seq = self.next_id

        stamp_header_with_controller_time = True
        if stamp_header_with_controller_time:
            message.header.stamp = self.command_time
        else:
            if self.next_id == 0:
                self.controller_time_offset = rospy.Time.now() - self.command_time
            message.header.stamp = self.command_time + self.controller_time_offset

        message.q = self.joint_positions
        message.qd = self.joint_velocities
        message.qdd = self.joint_accel
        message.names = self.robot.joint_names
        message.t = self.command_time

        self.next_id = self.next_id + 1
        self.prev_t = self.command_time
        return message
