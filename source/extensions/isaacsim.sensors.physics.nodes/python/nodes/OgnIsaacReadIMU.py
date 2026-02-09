# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""OmniGraph node for reading IMU sensor data.

This module provides the OgnIsaacReadIMU node which reads linear acceleration,
angular velocity, and orientation from an IsaacImuSensor prim.
"""
import omni.graph.core as og
from isaacsim.core.nodes import BaseResetNode
from isaacsim.sensors.experimental.physics.impl.imu_sensor_backend import ImuSensorBackend
from isaacsim.sensors.physics.nodes.ogn.OgnIsaacReadIMUDatabase import OgnIsaacReadIMUDatabase


class OgnIsaacReadIMUInternalState(BaseResetNode):
    """Internal state for the OgnIsaacReadIMU node.

    Maintains the IMU sensor backend instance and configuration between
    compute calls. Inherits from BaseResetNode for automatic reset handling.
    """

    def __init__(self):
        super().__init__(initialize=False)
        self.imu_sensor = None
        self.prim_path = ""
        self.read_gravity = True

    def custom_reset(self):
        """Reset the node state, clearing the sensor backend."""
        self.imu_sensor = None
        self.initialized = False

    def init_compute(self):
        """Initialize the IMU sensor backend.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        self.imu_sensor = ImuSensorBackend(self.prim_path)
        self.initialized = self.imu_sensor is not None
        return self.initialized


class OgnIsaacReadIMU:
    """OmniGraph node that reads IMU sensor data.

    Outputs linear acceleration, angular velocity, and orientation from
    an IsaacImuSensor prim at each compute step.
    """

    @staticmethod
    def internal_state():
        """Create the node's internal state object.

        Returns:
            New OgnIsaacReadIMUInternalState instance.
        """
        return OgnIsaacReadIMUInternalState()

    @staticmethod
    def compute(db) -> bool:
        """Execute the node computation.

        Reads IMU sensor data and populates output attributes.

        Args:
            db: OmniGraph database containing inputs/outputs.

        Returns:
            True if computation succeeded, False otherwise.
        """
        state = db.per_instance_state
        state.read_gravity = db.inputs.readGravity

        # Initialize sensor backend on first run
        if not state.initialized:
            if len(db.inputs.imuPrim) == 0:
                db.outputs.linAcc = [0.0, 0.0, 0.0]
                db.outputs.angVel = [0.0, 0.0, 0.0]
                db.outputs.orientation = [0.0, 0.0, 0.0, 1.0]  # Identity quaternion in [x, y, z, w] format
                db.outputs.sensorTime = 0.0
                db.log_error("Invalid Imu sensor prim")
                db.outputs.execOut = og.ExecutionAttributeState.DISABLED
                return False
            state.prim_path = db.inputs.imuPrim[0].GetString()
            if not state.init_compute():
                db.outputs.execOut = og.ExecutionAttributeState.DISABLED
                return False

        # Validate input prim
        if len(db.inputs.imuPrim) == 0:
            db.outputs.linAcc = [0.0, 0.0, 0.0]
            db.outputs.angVel = [0.0, 0.0, 0.0]
            db.outputs.orientation = [0.0, 0.0, 0.0, 1.0]  # Identity quaternion in [x, y, z, w] format
            db.outputs.sensorTime = 0.0
            db.log_error("Invalid Imu sensor prim")
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
            return False

        # Handle prim path changes
        prim_path = db.inputs.imuPrim[0].GetString()
        if prim_path != state.prim_path:
            state.prim_path = prim_path
            state.custom_reset()
            return True

        # Read sensor data
        reading = state.imu_sensor.get_sensor_reading(read_gravity=state.read_gravity)
        if reading.is_valid:
            db.outputs.linAcc = [
                reading.linear_acceleration_x,
                reading.linear_acceleration_y,
                reading.linear_acceleration_z,
            ]
            db.outputs.angVel = [
                reading.angular_velocity_x,
                reading.angular_velocity_y,
                reading.angular_velocity_z,
            ]
            db.outputs.orientation = list(reading.orientation)
            db.outputs.sensorTime = float(reading.time)
            db.outputs.execOut = og.ExecutionAttributeState.ENABLED
            return True

        # No valid reading available
        db.outputs.linAcc = [0.0, 0.0, 0.0]
        db.outputs.angVel = [0.0, 0.0, 0.0]
        db.outputs.orientation = [0.0, 0.0, 0.0, 1.0]  # Identity quaternion in [x, y, z, w] format
        db.outputs.sensorTime = 0.0
        db.log_warn("no valid sensor reading, is the sensor enabled?")
        db.outputs.execOut = og.ExecutionAttributeState.DISABLED
        return False

    @staticmethod
    def release_instance(node, graph_instance_id):
        """Release resources when node instance is destroyed.

        Args:
            node: The OmniGraph node being released.
            graph_instance_id: ID of the graph instance.
        """
        try:
            state = OgnIsaacReadIMUDatabase.per_instance_internal_state(node)
        except Exception:
            state = None
        if state is not None:
            state.reset()
