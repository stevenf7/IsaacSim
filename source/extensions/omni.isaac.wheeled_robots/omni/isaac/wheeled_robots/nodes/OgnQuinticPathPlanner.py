# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import numpy as np
import omni.graph.core as og
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.core.utils.rotations import quat_to_euler_angles
from omni.isaac.wheeled_robots.controllers.stanley_control import normalize_angle
from omni.isaac.wheeled_robots.ogn.OgnQuinticPathPlannerDatabase import OgnQuinticPathPlannerDatabase
from omni.isaac.wheeled_robots.controllers.quintic_path_planner import quintic_polynomials_planner


class OgnQuinticPathPlannerInternalState(BaseResetNode):
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()
        self.target = []
        self.rx = []
        self.ry = []
        self.ryaw = []
        self.rv = []
        super().__init__(initialize=False)

    def custom_reset(self):
        self.target = []
        self.rx = []
        self.ry = []
        self.ryaw = []
        self.rv = []


class OgnQuinticPathPlanner:
    @staticmethod
    def initialize(graph_context, node):
        db = OgnQuinticPathPlannerDatabase(node)
        state = OgnQuinticPathPlannerDatabase.per_node_internal_state(node)
        state.outputs = db.outputs

    @staticmethod
    def internal_state():
        return OgnQuinticPathPlannerInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        goal = get_target_pos(db.inputs, state)

        x = db.inputs.currentPosition[0]
        y = db.inputs.currentPosition[1]
        _, _, rot = quatd4_to_euler(db.inputs.currentOrientation)

        if goal is not None:
            state.target = goal

            _, state.rx, state.ry, state.ryaw, state.rv, _, _ = quintic_polynomials_planner(
                x,
                y,
                rot,
                db.inputs.initialVelocity,
                db.inputs.initialAccel,
                state.target[0],
                state.target[1],
                state.target[2],
                db.inputs.goalVelocity,
                db.inputs.goalAccel,
                db.inputs.maxAccel,
                db.inputs.maxJerk,
                db.inputs.step,
            )

        state.rx = np.array(state.rx)
        state.ry = np.array(state.ry)
        state.rv = np.array(state.rv)
        state.ryaw = np.array(state.ryaw)
        state.target = np.array(state.target)

        db.outputs.rx = state.rx
        db.outputs.ry = state.ry
        db.outputs.ryaw = state.ryaw
        db.outputs.rv = state.rv
        db.outputs.target = state.target
        db.outputs.targetChanged = goal is not None
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED

        return True


def get_target_pos(inputs, state):
    g = []
    if not inputs.targetPrim or not inputs.targetPrim.path:
        pos = inputs.targetPosition
        _, _, rot = quatd4_to_euler(inputs.targetOrientation)
        g = [pos[0], pos[1], rot]
    else:
        prim = state.stage.GetPrimAtPath(inputs.targetPrim.path)
        m = omni.usd.utils.get_world_transform_matrix(prim)
        m.Orthonormalize()
        pos = list(m.ExtractTranslation())
        rot = normalize_angle(np.radians(m.ExtractRotation().angle))
        g = [pos[0], pos[1], rot]

    if (
        len(state.target) > 0
        and abs(g[0] - state.target[0]) < 0.1
        and abs(g[1] - state.target[1]) < 0.1
        and abs(g[2] - state.target[2]) < 0.05
    ):
        return None
    else:
        return g


def quatd4_to_euler(orientation):
    x, y, z, w = tuple(orientation)
    roll, pitch, yaw = quat_to_euler_angles(np.array([w, x, y, z]))

    return normalize_angle(roll), normalize_angle(pitch), normalize_angle(yaw)
