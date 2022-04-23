# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.wheeled_robots.controllers.holonomic_controller import HolonomicController
from omni.isaac.kaya import Kaya
import numpy as np


class InternalState:
    def __init__(self):
        self.robot = None
        pass

    def first_run(self):
        self.robot = Kaya(prim_path="/kaya", name="my_robot", position=np.array([0, 0, 0.0]))
        self._controller = HolonomicController(
            name="holonomic_controller",
            robot=self.robot,
            com_prim=XFormPrim("/kaya/base_link/control_offset"),
            angular_gain=1,
        )
        self.robot.initialize()

    def move(self, dx, dy, dz):
        self.robot.apply_wheel_actions(self._controller.forward(command=[dx, dy, dz]))


class OgnKayaController:
    """
         move the kaya robot
    """

    @staticmethod
    def internal_state():
        return InternalState()

    @staticmethod
    def compute(db) -> bool:
        """Compute the outputs from the current input"""

        if db.internal_state.robot is None:
            if db.inputs.execIn:
                db.internal_state.first_run()
            return True
        else:
            try:
                dx = db.inputs.forwardVelocity
                dy = db.inputs.lateralVelocity
                dz = db.inputs.rotationVelocity

                db.internal_state.move(dx, dy, dz)

            except Exception as error:
                db.log_error(str(error))
                return False

        return True
