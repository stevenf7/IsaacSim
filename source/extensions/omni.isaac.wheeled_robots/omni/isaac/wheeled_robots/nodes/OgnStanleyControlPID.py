# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import math
import omni
import numpy as np
from pxr import UsdGeom
import omni.graph.core as og
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.core.utils.rotations import quat_to_euler_angles
from omni.isaac.wheeled_robots.ogn.OgnStanleyControlPIDDatabase import OgnStanleyControlPIDDatabase
from omni.isaac.wheeled_robots.controllers.stanley_control import (
    State,
    pid_control,
    stanley_control,
    normalize_angle,
    Kp,
)


class OgnStanleyControlPIDInternalState(BaseResetNode):
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()
        self.stage_unit = UsdGeom.GetStageMetersPerUnit(self.stage)

        self.state = None
        self.initialized = False
        self.target_idx = 0
        self.target = [0, 0, 0]
        self.rx = []
        self.thresholds = []

        super().__init__(initialize=False)

    def initialize(self, inputs, x, y, rot, v) -> None:
        self.state = State(inputs.wheelBase, x=x, y=y, yaw=rot, v=v)
        self.initialized = True

    def custom_reset(self):
        self.state = None
        self.initialized = False
        self.target_idx = 0
        self.target = [0, 0, 0]
        self.rx = []
        self.thresholds = []


class OgnStanleyControlPID:
    @staticmethod
    def initialize(graph_context, node):
        db = OgnStanleyControlPIDDatabase(node)
        state = OgnStanleyControlPIDDatabase.per_node_internal_state(node)
        state.outputs = db.outputs

    @staticmethod
    def internal_state():
        return OgnStanleyControlPIDInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        state.thresholds = db.inputs.thresholds

        if db.inputs.reachedGoal[0] and db.inputs.reachedGoal[1]:
            db.outputs.linearVelocity = 0
            db.outputs.angularVelocity = 0
            db.outputs.execOut = og.ExecutionAttributeState.ENABLED
            return
        x = db.inputs.currentPosition[0]
        y = db.inputs.currentPosition[1]
        _, _, rot = quatd4_to_euler(db.inputs.currentOrientation)
        v = np.hypot(db.inputs.currentSpeed[0], db.inputs.currentSpeed[1])

        if not state.initialized:
            state.initialize(db.inputs, x, y, rot, v)

        if db.inputs.targetChanged:
            state.target_idx = 0
            state.target = db.inputs.target

            state.rx = db.inputs.rx
            state.ry = db.inputs.ry

            state.sp = calc_speed_profile(np.array(db.inputs.rv), db.inputs.maxVelocity, 0.5, 0.05)
            color = [(0, t / np.max(state.sp), 0) for t in state.sp]
            state.y_color = int.from_bytes(b"\xff\xff\x00\x00", byteorder="big")
            rgb_bytes = [(np.clip(c, 0, 1.0) * 255).astype("uint8").tobytes() for c in color]
            argb_bytes = [b"\xff" + b for b in rgb_bytes]
            state.argb = [int.from_bytes(b, byteorder="big") for b in argb_bytes]

        state.rotate_only = (
            np.hypot(x - state.target[0], y - state.target[1]) <= state.thresholds[0] or db.inputs.reachedGoal[0]
        )

        theta_diff = math.atan2(math.sin(state.target[2] - rot), math.cos(state.target[2] - rot))
        stanley_state = State(db.inputs.wheelBase * Kp, x=x, y=y, yaw=rot % (2 * np.pi), v=v)

        if not state.rotate_only:
            ai = pid_control(state.sp[state.target_idx], stanley_state.v) / db.inputs.step
            di, state.target_idx = stanley_control(
                stanley_state, db.inputs.rx, db.inputs.ry, db.inputs.ryaw, state.target_idx
            )

            stanley_state.update(ai, di, db.inputs.step)
            v = stanley_state.v
            w = stanley_state.w
        else:
            v = 0
            if theta_diff > 0:
                w = min(((theta_diff) * Kp / db.inputs.step), 1)
            else:
                w = max(((theta_diff) * Kp / db.inputs.step), -1)

        kw = 1
        # Allow additional steering to use differential drive (backwards spin on one wheel to tighten the cornering radius)
        if not db.inputs.reachedGoal[0] and v > 0:
            kw = 1 + abs((db.inputs.wheelBase * w) / v) * (1 * Kp / db.inputs.step)

        db.outputs.linearVelocity = v - abs(kw * w * 0.25)
        db.outputs.angularVelocity = kw * w

        db.outputs.execOut = og.ExecutionAttributeState.ENABLED


def quatd4_to_euler(orientation):
    x, y, z, w = tuple(orientation)
    roll, pitch, yaw = quat_to_euler_angles(np.array([w, x, y, z]))

    return normalize_angle(roll), normalize_angle(pitch), normalize_angle(yaw)


def calc_speed_profile(cyaw, max_speed, target_speed, min_speed=1):
    speed_profile = np.array(cyaw) / max([abs(c) for c in cyaw]) * max_speed

    # speed down
    res = min(int(len(cyaw) / 3), int(max_speed * 60))

    for i in range(1, res):
        speed_profile[-i] = min(speed_profile[-i], speed_profile[-i] / (float(res - i)) ** 0.5)  # / (res))
        if speed_profile[-i] <= min_speed:
            speed_profile[-i] = min_speed

    return speed_profile
