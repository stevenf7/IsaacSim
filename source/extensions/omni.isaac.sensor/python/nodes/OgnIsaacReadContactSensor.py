# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# Array or tuple values are accessed as numpy arrays so you probably need this import
import numpy
import omni.graph.core as og
import omni.timeline
import usdrt.Sdf
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.sensor import _sensor
from omni.isaac.sensor.ogn.OgnIsaacReadContactSensorDatabase import OgnIsaacReadContactSensorDatabase


class OgnIsaacReadContactSensorInternalState(BaseResetNode):
    def __init__(self):
        self._cs = _sensor.acquire_contact_sensor_interface()
        self.cs_path = ""
        super().__init__(initialize=False)

    def custom_reset(self):
        self.cs_path = ""
        pass


class OgnIsaacReadContactSensor:
    """
    Node that returns Contact Sensor data
    """

    @staticmethod
    def internal_state():
        return OgnIsaacReadContactSensorInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        if len(db.inputs.csPrim) > 0:
            state.cs_path = db.inputs.csPrim[0].GetString()

        else:
            db.outputs.inContact = False
            db.outputs.value = 0
            db.outputs.sensorTime = 0
            db.log_error("Invalid contact sensor prim")
            return False

        reading = state._cs.get_sensor_reading(state.cs_path)
        if reading.is_valid:
            db.outputs.inContact = reading.in_contact
            db.outputs.value = reading.value
            db.outputs.sensorTime = reading.time
        else:
            db.outputs.inContact = False
            db.outputs.value = 0
            db.outputs.sensorTime = 0
            db.log_warn("Invalid contact sensor measurement, is it enabled?")
            return False

        db.outputs.execOut = og.ExecutionAttributeState.ENABLED

        return True

    @staticmethod
    def release(node):
        try:
            state = OgnIsaacReadContactSensorDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
