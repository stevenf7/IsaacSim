# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# Array or tuple values are accessed as numpy arrays so you probably need this import
import numpy as np
import omni.graph.core as og
import omni.timeline
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.sensor import _sensor
from omni.isaac.sensor.ogn.OgnIsaacReadIMUDatabase import OgnIsaacReadIMUDatabase


class OgnIsaacReadIMUInternalState(BaseResetNode):
    def __init__(self):
        self._is = _sensor.acquire_imu_sensor_interface()
        self.imu_path = ""
        super().__init__(initialize=False)

    def custom_reset(self):
        self.imu_path = ""
        pass


class OgnIsaacReadIMU:
    """
    Node that returns IMU Sensor data
    """

    @staticmethod
    def internal_state():
        return OgnIsaacReadIMUInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        if len(db.inputs.imuPrim) > 0:
            state.imu_path = db.inputs.imuPrim[0].GetString()

        else:
            db.outputs.linAcc = [0.0, 0.0, 0.0]
            db.outputs.angVel = [0.0, 0.0, 0.0]
            db.outputs.orientation = [0.0, 0.0, 0.0, 1.0]
            db.outputs.sensorTime = 0.0
            db.log_error("Invalid Imu sensor prim")
            return False

        reading = state._is.get_sensor_reading(state.imu_path, None, db.inputs.useLatestData, db.inputs.readGravity)
        if reading.is_valid:
            db.outputs.orientation = reading.orientation
            lin_acc = [reading.lin_acc_x, reading.lin_acc_y, reading.lin_acc_z]
            ang_vel = [reading.ang_vel_x, reading.ang_vel_y, reading.ang_vel_z]
            db.outputs.sensorTime = reading.time
            db.outputs.linAcc = lin_acc
            db.outputs.angVel = ang_vel

        else:
            db.outputs.linAcc = [0.0, 0.0, 0.0]
            db.outputs.angVel = [0.0, 0.0, 0.0]
            db.outputs.orientation = [0.0, 0.0, 0.0, 1.0]
            db.outputs.sensorTime = 0.0
            db.log_warn("no valid sensor reading, is the sensor enabled?")
            return False
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED

        return True

    @staticmethod
    def release(node):
        try:
            state = OgnIsaacReadIMUDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
