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
"""OmniGraph node for reading contact sensor data.

This module provides the OgnIsaacReadContactSensor node which reads contact
state and force from an IsaacContactSensor prim.
"""
import omni.graph.core as og
from isaacsim.core.nodes import BaseResetNode
from isaacsim.sensors.experimental.physics.impl.contact_sensor_backend import ContactSensorBackend
from isaacsim.sensors.physics.nodes.ogn.OgnIsaacReadContactSensorDatabase import (
    OgnIsaacReadContactSensorDatabase,
)


class OgnIsaacReadContactSensorInternalState(BaseResetNode):
    """Internal state for the OgnIsaacReadContactSensor node.

    Maintains the contact sensor backend instance and configuration between
    compute calls. Inherits from BaseResetNode for automatic reset handling.
    """

    def __init__(self):
        super().__init__(initialize=False)
        self.contact_sensor = None
        self.prim_path = ""

    def custom_reset(self):
        """Reset the node state, clearing the sensor backend."""
        self.contact_sensor = None
        self.initialized = False

    def init_compute(self):
        """Initialize the contact sensor backend.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        self.contact_sensor = ContactSensorBackend(self.prim_path)
        self.initialized = self.contact_sensor is not None
        return self.initialized


class OgnIsaacReadContactSensor:
    """OmniGraph node that reads contact sensor data.

    Outputs contact state and force magnitude from an IsaacContactSensor
    prim at each compute step.
    """

    @staticmethod
    def internal_state():
        """Create the node's internal state object.

        Returns:
            New OgnIsaacReadContactSensorInternalState instance.
        """
        return OgnIsaacReadContactSensorInternalState()

    @staticmethod
    def compute(db) -> bool:
        """Execute the node computation.

        Reads contact sensor data and populates output attributes.

        Args:
            db: OmniGraph database containing inputs/outputs.

        Returns:
            True if computation succeeded, False otherwise.
        """
        state = db.per_instance_state

        # Initialize sensor backend on first run
        if not state.initialized:
            if len(db.inputs.csPrim) == 0:
                db.outputs.inContact = False
                db.outputs.value = 0.0
                db.outputs.sensorTime = 0.0
                db.log_error("Invalid contact sensor prim")
                db.outputs.execOut = og.ExecutionAttributeState.DISABLED
                return False
            state.prim_path = db.inputs.csPrim[0].GetString()
            if not state.init_compute():
                db.outputs.execOut = og.ExecutionAttributeState.DISABLED
                return False

        # Validate input prim
        if len(db.inputs.csPrim) == 0:
            db.outputs.inContact = False
            db.outputs.value = 0.0
            db.outputs.sensorTime = 0.0
            db.log_error("Invalid contact sensor prim")
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
            return False

        # Handle prim path changes
        prim_path = db.inputs.csPrim[0].GetString()
        if prim_path != state.prim_path:
            state.prim_path = prim_path
            state.custom_reset()
            return True

        # Read sensor data
        reading = state.contact_sensor.get_sensor_reading()
        if reading.is_valid:
            db.outputs.inContact = bool(reading.in_contact)
            db.outputs.value = float(reading.value)
            db.outputs.sensorTime = float(reading.time)
            db.outputs.execOut = og.ExecutionAttributeState.ENABLED
            return True

        # No valid reading available
        db.outputs.inContact = False
        db.outputs.value = 0.0
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
            state = OgnIsaacReadContactSensorDatabase.per_instance_internal_state(node)
        except Exception:
            state = None
        if state is not None:
            state.reset()
