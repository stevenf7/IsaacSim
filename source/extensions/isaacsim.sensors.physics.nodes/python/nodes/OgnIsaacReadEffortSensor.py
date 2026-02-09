# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""OmniGraph node for reading effort sensor data.

This module provides the OgnIsaacReadEffortSensor node which reads joint
effort (torque/force) from an articulated body.
"""
import omni.graph.core as og
from isaacsim.core.nodes import BaseResetNode
from isaacsim.sensors.experimental.physics.impl.effort_sensor import EffortSensor
from isaacsim.sensors.physics.nodes.ogn.OgnIsaacReadEffortSensorDatabase import OgnIsaacReadEffortSensorDatabase


class OgnIsaacReadEffortSensorInternalState(BaseResetNode):
    """Internal state for the OgnIsaacReadEffortSensor node.

    Maintains the effort sensor instance and configuration between
    compute calls. Inherits from BaseResetNode for automatic reset handling.
    """

    def __init__(self):
        super().__init__(initialize=False)
        self.effort_sensor = None

    def custom_reset(self):
        """Reset the node state, clearing the sensor instance.

        Triggers the stage open callback to clean up sensor callbacks
        before releasing the sensor.
        """
        if self.effort_sensor is not None:
            # Reset the effort sensor callbacks
            self.effort_sensor._stage_open_callback_fn()
            self.effort_sensor = None
        self.initialized = False
        pass

    def init_compute(self):
        """Initialize the effort sensor.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        self.effort_sensor = EffortSensor(
            prim_path=self.prim_path,
            enabled=self.enabled,
        )

        if self.effort_sensor is not None:
            self.initialized = True
            return True
        else:
            return False


class OgnIsaacReadEffortSensor:
    """OmniGraph node that reads effort sensor data.

    Outputs joint effort (torque/force) from an articulated body
    at each compute step.
    """

    @staticmethod
    def internal_state():
        """Create the node's internal state object.

        Returns:
            New OgnIsaacReadEffortSensorInternalState instance.
        """
        return OgnIsaacReadEffortSensorInternalState()

    @staticmethod
    def compute(db) -> bool:
        """Execute the node computation.

        Reads effort sensor data and populates output attributes.

        Args:
            db: OmniGraph database containing inputs/outputs.

        Returns:
            True if computation succeeded, False otherwise.
        """
        state = db.per_instance_state
        state.enabled = db.inputs.enabled

        # Initialize sensor on first run
        if not state.initialized:
            if len(db.inputs.prim) > 0:
                state.prim_path = db.inputs.prim[0].GetString()
                state.parent_path = "/".join(state.prim_path.split("/")[:-1])
                state.dof_name = state.prim_path.split("/")[-1]
            else:
                db.log_error(f"Failed to create effort sensor, unable to find prim path")
                return False

            result = state.init_compute()
            if not result:
                db.outputs.sensorTime = 0
                db.outputs.value = 0
                db.log_error(f"Failed to create sensor at {state.prim_path} for joint {state.dof_name}")
                return False

        # Validate input prim
        if not len(db.inputs.prim) > 0:
            db.log_error(f"Failed to create effort sensor, unable to find prim path")
            return False

        state.prim_path = db.inputs.prim[0].GetString()
        parent_path = "/".join(state.prim_path.split("/")[:-1])
        dof_name = state.prim_path.split("/")[-1]

        # Handle articulation path changes (requires full sensor recreation)
        if state.parent_path != parent_path:
            state.parent_path = parent_path
            state.dof_name = dof_name
            state.custom_reset()
            state.initialized = False
            return True

        # Handle DOF name changes (can update in place)
        elif state.dof_name != dof_name:
            state.dof_name = dof_name
            try:
                state.effort_sensor.update_dof_name(state.dof_name)
            except:
                db.outputs.sensorTime = 0
                db.outputs.value = 0
                db.log_warn(f"Effort sensor error, invalid dof name: {state.dof_name}")
                return False

        # Update sensor configuration from inputs
        state.effort_sensor.enabled = state.enabled

        # Read sensor data
        sensor_reading = state.effort_sensor.get_sensor_reading()

        # Output reading if valid, or if still warming up (first 2 steps)
        if sensor_reading.is_valid or state.effort_sensor.physics_num_steps <= 2:
            db.outputs.sensorTime = sensor_reading.time
            db.outputs.value = sensor_reading.value
        else:
            db.outputs.sensorTime = 0
            db.outputs.value = 0
            db.log_warn(
                "Effort Sensor error, no valid sensor reading, is the prim_path valid or is the sensor enabled?"
            )
            return False

        db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        return True

    @staticmethod
    def release_instance(node, graph_instance_id):
        """Release resources when node instance is destroyed.

        Args:
            node: The OmniGraph node being released.
            graph_instance_id: ID of the graph instance.
        """
        try:
            state = OgnIsaacReadEffortSensorDatabase.per_instance_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
