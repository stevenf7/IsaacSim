from omni.isaac.motion_generation import MotionGenerator
import carb
import json
import os
import omni
import franka
import math
import copy
import numpy as np

import rospy
from std_msgs.msg import Bool, Header
from sensor_msgs.msg import JointState
from lula_ros.msg import JointPosVelAccCommand, LulaCommandAck

from pxr import Gf


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
        self.joint_state = None
        self.states_from_suppress = None

        self.suppression_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/suppress", Bool, self.suppression_callback
        )
        self.joint_state_sub = rospy.Subscriber("/robot/joint_state", JointState, self.joint_state_callback)
        self.joint_command_pub = rospy.Publisher(
            "/rmpflow/commands/joint_command", JointPosVelAccCommand, queue_size=10
        )

    def __del__(self):
        self.suppression_sub.unregister()
        self.joint_command_pub.unregister()

    def register(self, robot: franka.Panda, target_prim, obs_prim):
        self.mg.initialize(self.config, robot.prim, 60)

        self.mg.set_end_effector_target(target_prim, position_only=True)
        self.target_prim = target_prim

        self.mg.create_cube(obs_prim.GetPrim())
        self.obs_prim = obs_prim

        self.policy = self.mg._motion_policy._policy
        self.robot = robot
        self.dof_states = robot.joint_states
        self.q, self.qd, _ = self.mg.get_active_joint_states()
        self.qdd = None
        print("q:", self.q)
        print("qd:", self.qd)
        print("qdd:", self.qdd)

        self.target_translation_handle = self.target_prim.AddTranslateOp()
        self.target_prim.AddRotateXYZOp().Set(Gf.Vec3d(180.0, 0.0, 180.0))
        self.set_target_to_end_effector_location()

    def set_target_to_end_effector_location(self):
        translation, rotation = self.mg.get_end_effector_pose()
        translation *= 100.0  # Turn it from meters to centimeters.
        trans = Gf.Vec3d(translation[0], translation[1], translation[2])
        self.target_translation_handle.Set(trans)

    def process_policy_config(self, mp_config_file):
        mp_config_dir = os.path.dirname(mp_config_file)  # path to directory containing mp_config_file

        with open(mp_config_file) as config_file:
            config = json.load(config_file)

        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_config_dir, v)

        return config

    def suppression_callback(self, data):
        self.is_suppressed = data.data

    def joint_state_callback(self, msg):
        # Reorganize the message into a map from name -> (q, qd). The message
        # may have more than the required joints or entirely the wrong joints.,
        joint_values = {}
        for i, (name, (q, qd)) in enumerate(zip(msg.name, zip(msg.position, msg.velocity))):
            joint_values[name] = (q, qd)

        joint_names = self.robot.joint_names
        joint_state = copy.deepcopy(self.dof_states)
        for i, name in enumerate(joint_names):
            index = self.robot.joint_indices[i]
            if name not in joint_values.keys():
                # Skip this message if we can't find a required name
                return

            joint_state["pos"][index] = joint_values[name][0]
            joint_state["vel"][index] = joint_values[name][1]

        self.joint_state = joint_state

    def update(self):
        if self.is_suppressed:
            # Interpolator is telling us to ignore RMPs and instead set the internal state to the
            # "physical" robot.
            self.states_from_suppress = self.joint_state
            carb.log_warn("rmp's suppressed by interpolator")
        else:
            # Perform this reset to the true robot state only one time once the suppression has
            # stopped.
            if self.states_from_suppress is not None:
                self.robot.joint_states = self.states_from_suppress
                self.q, self.qd, _ = self.mg.get_active_joint_states()
                self.set_target_to_end_effector_location()
                self.states_from_suppress = None

            # Step the RMPs forward based on timing from the interpolator rosnode
            adaptive_cycle = self.synced_time.next_adaptive_cycle_time()
            self.command_time = adaptive_cycle.time
            integration_dt = self.mg.sim_timestep
            if adaptive_cycle.is_period_available:
                integration_dt = adaptive_cycle.period.to_sec()

            self.mg._motion_policy.update()

            # Perform some integration steps.
            aji = self.mg._active_joint_inds
            num_steps = self.mg._motion_policy.evaluations_per_frame
            step_dt = integration_dt / num_steps
            for i in range(num_steps):
                self.qdd = np.zeros_like(self.q)
                self.policy.eval_accel(self.q, self.qd, self.qdd)

                self.q += step_dt * self.qd
                self.qd += step_dt * self.qdd

            # Set the robot to the desired.
            joint_positions = self.robot.get_position_targets()
            if joint_positions is None:
                carb.log_warn("Latest robot joint positions is None")
                return

            joint_positions[aji] = self.q
            self.robot.set_position_targets(joint_positions)

            msg = self._get_joint_pos_vel_acc_command()
            self.joint_command_pub.publish(msg)
        self.frame = self.frame + 1

    def _get_joint_pos_vel_acc_command(self):
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

        message.q = self.q
        message.qd = self.qd
        message.qdd = self.qdd
        message.names = self.robot.joint_names
        message.t = self.command_time

        self.next_id = self.next_id + 1
        self.prev_t = self.command_time
        return message
