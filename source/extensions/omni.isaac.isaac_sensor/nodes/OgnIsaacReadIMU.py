# Array or tuple values are accessed as numpy arrays so you probably need this import
import numpy as np

import omni.timeline
import omni.graph.core as og

from omni.isaac.isaac_sensor import BaseResetNode
from omni.isaac.isaac_sensor import _isaac_sensor
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.isaac_sensor.ogn.OgnIsaacReadIMUDatabase import OgnIsaacReadIMUDatabase


class OgnIsaacReadIMUInternalState(BaseResetNode):
    def __init__(self):
        self.run = 0
        self.init_rot = [0, 0, 0, 1]
        self.imu_path = ""
        super().__init__(initialize=False)

    def custom_reset(self):
        self.run = 0
        self.init_rot = [0, 0, 0, 1]
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
        _is = _isaac_sensor.acquire_imu_sensor_interface()
        dc = _dynamic_control.acquire_dynamic_control_interface()

        if db.inputs.imuPrim.valid:
            state.imu_path = db.inputs.imuPrim.path
            if (
                _is.is_imu_sensor(state.imu_path)
                and dc.peek_object_type(state.imu_path[:-11]) != _dynamic_control.OBJECT_NONE
            ):
                if state.run > 0:

                    readings = _is.get_sensor_readings(state.imu_path)

                    # next pass
                    if state.run == 1:
                        state.init_rot = readings[-1]["orientation"]
                        state.run += 1

                    else:
                        b = readings[-1]["orientation"]

                        # compute quaternion inverse + multiplication
                        a = [-state.init_rot[i] for i in range(3)]
                        a.append(state.init_rot[3])

                        db.outputs.orientation = [
                            a[3] * b[0] + b[3] * a[0] + a[1] * b[2] - b[1] * a[2],
                            a[3] * b[1] + b[3] * a[1] + a[2] * b[0] - b[2] * a[0],
                            a[3] * b[2] + b[3] * a[2] + a[0] * b[1] - b[0] * a[1],
                            a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
                        ]

                    lin_acc_l = ["lin_acc_x", "lin_acc_y", "lin_acc_z"]
                    ang_vel_l = ["ang_vel_x", "ang_vel_y", "ang_vel_z"]

                    lin_acc_l = [float(readings[-1][x]) for x in lin_acc_l]
                    ang_vel_l = [float(readings[-1][x]) for x in ang_vel_l]

                    db.outputs.linAcc = lin_acc_l
                    db.outputs.angVel = ang_vel_l

                else:
                    state.run += 1

            return True
        return False

    @staticmethod
    def release(node):
        try:
            state = OgnIsaacReadIMUDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
