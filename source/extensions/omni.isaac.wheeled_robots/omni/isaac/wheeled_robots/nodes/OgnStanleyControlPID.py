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

        self.target_idx = 0
        self.target = [0, 0, 0]
        self.rv = []
        self.rx = []
        self.ry = []
        self.ryaw = []
        self.argb = []
        self.thresholds = []

        super().__init__(initialize=False)

    def custom_reset(self):
        self.target_idx = 0
        self.target = [0, 0, 0]
        self.rv = []
        self.rx = []
        self.ry = []
        self.ryaw = []
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

        reachedGoal = db.inputs.reachedGoal
        if reachedGoal[0] and reachedGoal[1]:
            db.outputs.linearVelocity = 0
            db.outputs.angularVelocity = 0
            db.outputs.execOut = og.ExecutionAttributeState.ENABLED
            return True

        pos = db.inputs.currentPosition
        x = pos[0]
        y = pos[1]
        _, _, rot = quatd4_to_euler(db.inputs.currentOrientation)
        cs = db.inputs.currentSpeed
        v = np.hypot(cs[0], cs[1])

        if db.inputs.targetChanged:
            state.target_idx = 0
            state.target = db.inputs.target

            pathArrays = db.inputs.pathArrays
            arr_length = int(len(pathArrays) / 4)

            state.rv = np.array(pathArrays[0:arr_length])
            state.rx = np.array(pathArrays[arr_length : arr_length * 2])
            state.ry = np.array(pathArrays[arr_length * 2 : arr_length * 3])
            state.ryaw = np.array(pathArrays[arr_length * 3 : arr_length * 4])

            state.sp = calc_speed_profile(np.array(state.rv), db.inputs.maxVelocity, 0.5, 0.05)

            state.argb = draw_path_setup(state.sp)

        state.rotate_only = np.hypot(x - state.target[0], y - state.target[1]) <= state.thresholds[0] or reachedGoal[0]

        theta_diff = math.atan2(math.sin(state.target[2] - rot), math.cos(state.target[2] - rot))

        wb = db.inputs.wheelBase
        s = db.inputs.step

        if wb == 0:
            print("Error: wheel base is 0!")
            return False
        elif s == 0:
            print("Error: step is 0!")
            return False

        stanley_state = State(wb * Kp, x=x, y=y, yaw=rot % (2 * np.pi), v=v)

        if not state.rotate_only:
            ai = pid_control(state.sp[state.target_idx], stanley_state.v) / s
            di, state.target_idx = stanley_control(stanley_state, state.rx, state.ry, state.ryaw, state.target_idx)

            stanley_state.update(ai, di, s)
            v = stanley_state.v
            w = stanley_state.w

        else:
            v = 0
            if theta_diff > 0:
                w = min(((theta_diff) * Kp / s), 1)
            else:
                w = max(((theta_diff) * Kp / s), -1)

        kw = 1
        # Allow additional steering to use differential drive (backwards spin on one wheel to tighten the cornering radius)
        if not reachedGoal[0] and v > 0:
            kw = 1 + abs((wb * w) / v) * (1 * Kp / s)

        db.outputs.linearVelocity = v
        db.outputs.angularVelocity = kw * w

        db.outputs.execOut = og.ExecutionAttributeState.ENABLED

        if db.inputs.drawPath:
            draw_path(state.rx, state.ry, state.argb)

        return True


def quatd4_to_euler(orientation):
    x, y, z, w = tuple(orientation)
    roll, pitch, yaw = quat_to_euler_angles(np.array([w, x, y, z]))

    return normalize_angle(roll), normalize_angle(pitch), normalize_angle(yaw)


def calc_speed_profile(cyaw, max_speed, target_speed, min_speed=1):
    max_c = max([abs(c) for c in cyaw])
    if max_c == 0:
        print("Error: max yaw is 0!")
        return False

    speed_profile = np.array(cyaw) / max_c * max_speed

    # speed down
    res = min(int(len(cyaw) / 3), int(max_speed * 60))

    for i in range(1, res):
        speed_profile[-i] = min(speed_profile[-i], speed_profile[-i] / (float(res - i)) ** 0.5)  # / (res))
        if speed_profile[-i] <= min_speed:
            speed_profile[-i] = min_speed

    return speed_profile


def draw_path_setup(sp):
    color = [(0, t / np.max(sp), 0) for t in sp]
    rgb_bytes = [(np.clip(c, 0, 1.0) * 255).astype("uint8").tobytes() for c in color]
    argb_bytes = [b"\xff" + b for b in rgb_bytes]
    argb = [int.from_bytes(b, byteorder="big") for b in argb_bytes]

    return argb


def draw_path(rx, ry, argb):
    from omni.debugdraw import _debugDraw
    import carb
    from pxr import UsdGeom

    stage = omni.usd.get_context().get_stage()
    stage_unit = UsdGeom.GetStageMetersPerUnit(stage)

    for i in range(len(rx) - 1):
        _debugDraw.acquire_debug_draw_interface().draw_line(
            carb.Float3(rx[i] / stage_unit, ry[i] / stage_unit, 0.14 / stage_unit),
            argb[i],
            carb.Float3(rx[i + 1] / stage_unit, ry[i + 1] / stage_unit, 0.14 / stage_unit),
            argb[i - 1],
        )
