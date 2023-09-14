# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import omni.graph.core as og
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.wheeled_robots.ogn.OgnAckermannDatabase import OgnAckermannDatabase


class OgnAckermannInternalState(BaseResetNode):
    def __init__(self):
        super().__init__(initialize=False)


class OgnAckermann:
    @staticmethod
    def initialize(graph_context, node):
        db = OgnAckermannDatabase(node)
        state = OgnAckermannDatabase.per_node_internal_state(node)
        state.outputs = db.outputs

    @staticmethod
    def internal_state():
        return OgnAckermannInternalState()

    @staticmethod
    def compute(db) -> bool:
        # avoid division by zero
        if db.inputs.turningWheelRadius <= 0:
            db.log_warn("Omnigraph warning: turning wheel radius is 0")
            return False

        # if turning wheel radius is very small (< 1cm)
        elif db.inputs.turningWheelRadius < 1e-2:
            db.log_warn(f"Omnigraph warning: turning wheel radius is very small: {db.inputs.turningWheelRadius}")

        # compute wheel rotation velocity --> (current linear velocity + acceleration adjusted for dt) / turning (driven) wheel radius
        w = (db.inputs.linearVelocity[1] + db.inputs.accel * db.inputs.DT) / db.inputs.turningWheelRadius

        # clamp wheel rotation velocity to max wheel velocity
        w = np.clip(w, -db.inputs.maxWheelVelocity, db.inputs.maxWheelVelocity)

        # output wheel rotation angular velocity
        db.outputs.wheelRotationVelocity = w

        # if curvature is zero or sufficiently small, set wheel angles to zero (avoid divide by zero)
        if np.fabs(db.inputs.curvature) < 1e-3:
            db.outputs.leftWheelAngle = 0
            db.outputs.rightWheelAngle = 0
        else:
            # compute turning radius --> flip sign if curvature is inverted
            R = (1 if db.inputs.invertCurvature else -1) / db.inputs.curvature
            WB = db.inputs.wheelBase
            TW = db.inputs.trackWidth

            # minimum turning radius is the distance from the pivot point of a turning wheel to the center point between the non-turning wheels
            # this signifies the point at which the turning wheels will both point inward, and the robot will be turning in place about the aforementioned center point
            # if the wheels were to turn further past this point, they would be driving "backward"
            # if the robot is correctly configured and the wheels are incapable of pivoting a full 180 degrees, this should never happen
            min_R = WB / (np.sin(np.arctan(WB / (TW / 2))))

            # set turning radius to be greater than min_R or less than negative min_R
            if R < min_R and R > 0:
                R = min_R * 1.01
            elif R > -min_R and R < 0:
                R = -min_R * 1.01

            # delta_ack is the steering angle for the bicycle model --> used to compute the wheel angles
            delta_ack = np.arcsin(WB / R)

            # used https://www.mathworks.com/help/vdynblks/ref/kinematicsteering.html as a reference for the following equations
            # compute the wheel angles by taking into account their offset from the center of the turning axle (where the bicycle model is centered), then computing the angles of each wheel relative to the turning point of the robot
            delta_l = np.arctan((WB * np.tan(delta_ack)) / (WB + 0.5 * TW * np.tan(delta_ack)))
            delta_r = np.arctan((WB * np.tan(delta_ack)) / (WB - 0.5 * TW * np.tan(delta_ack)))

            # convert wheel angles to degrees
            delta_l = np.rad2deg(delta_l)
            delta_r = np.rad2deg(delta_r)

            # clamp wheel angles to max wheel rotation
            delta_l = np.clip(delta_l, -np.fabs(db.inputs.maxWheelRotation), np.fabs(db.inputs.maxWheelRotation))
            delta_r = np.clip(delta_r, -np.fabs(db.inputs.maxWheelRotation), np.fabs(db.inputs.maxWheelRotation))

            # output wheel angles
            db.outputs.leftWheelAngle = delta_l
            db.outputs.rightWheelAngle = delta_r

        # Begin next node execution (if configured)
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED

        return True
