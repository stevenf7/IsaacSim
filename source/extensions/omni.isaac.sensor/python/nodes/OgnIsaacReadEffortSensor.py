# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# Array or tuple values are accessed as numpy arrays so you probably need this import
import omni.graph.core as og
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.sensor.ogn.OgnIsaacReadEffortSensorDatabase import OgnIsaacReadEffortSensorDatabase
from omni.isaac.sensor.scripts.effort_sensor import EffortSensor


class OgnIsaacReadEffortSensorInternalState(BaseResetNode):
    def __init__(self):
        self.first = True
        super().__init__(initialize=False)

    def custom_reset(self):
        self.first = True
        if self.effort_sensor is not None:
            # reset the effort sensor callbacks
            self.effort_sensor._stage_open_callback_fn()
            self.effort_sensor = None
        self.initialized = False
        pass

    def init_compute(self):
        self.effort_sensor = EffortSensor(
            prim_path=self.prim_path,
            dof_name=self.dof_name,
            sensor_period=self.sensor_period,
            use_latest_data=self.use_latest_data,
            enabled=self.enabled,
        )

        if self.effort_sensor is not None:
            self.initialized = True
            return True
        else:
            return False


class OgnIsaacReadEffortSensor:
    @staticmethod
    def internal_state():
        return OgnIsaacReadEffortSensorInternalState()

    """
    Node that returns Effort Sensor data
    """

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state
        state.sensor_period = db.inputs.sensorPeriod
        state.use_latest_data = db.inputs.useLatestData
        state.enabled = db.inputs.enabled
        if not state.initialized:
            state.prim_path = db.inputs.primPath
            state.dof_name = db.inputs.dofName
            result = state.init_compute()
            if not result:
                db.outputs.sensorTime = 0
                db.outputs.value = 0
                db.log_warn(f"Failed to create sensor at {state.prim_path} for joint {state.dof_name}")
                return False

        if state.prim_path != db.inputs.primPath:
            state.prim_path = db.inputs.primPath
            state.dof_name = db.inputs.dofName
            try:
                # if change prim path, need to delete, and recreate the effort sensor
                state.custom_reset
                state.initialized = False
                return True
            except:
                db.outputs.sensorTime = 0
                db.outputs.value = 0
                db.log_warn(f"Effort sensor error, invalid art: {state.prim_path} or dof name: {state.dof_name}")
                return False

        elif state.dof_name != db.inputs.dofName:
            state.dof_name = db.inputs.dofName
            try:
                state.effort_sensor.update_dof_name(state.dof_name)
            except:
                db.outputs.sensorTime = 0
                db.outputs.value = 0
                db.log_warn(f"Effort sensor error, invalid dof name: {state.dof_name}")
                return False

        state.effort_sensor.enabled = state.enabled

        sensor_reading = state.effort_sensor.get_sensor_reading()

        # valid, or the sensor is warming up
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
    def release(node):
        try:
            state = OgnIsaacReadEffortSensorDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
