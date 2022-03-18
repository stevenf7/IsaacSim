# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.jetbot import Jetbot
import numpy as np
from omni.isaac.jetbot.controllers import DifferentialController


class InternalState:
    def __init__(self):
        self.robot = None
        pass

    def first_run(self):
        self.robot = Jetbot(prim_path="/jetbot", name="my_robot", position=np.array([0, 0, 2.0]))
        self._controller = DifferentialController(name="differential_controller")
        self.robot.initialize()

    def move(self, dx, dz):
        self.robot.apply_wheel_actions(self._controller.forward(command=[dx, dz]))


class OgnJetbotController:
    """
         move the jetbot robot
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
                dz = db.inputs.rotationVelocity

                db.internal_state.move(dx, dz)

            except Exception as error:
                db.log_error(str(error))
                return False

        return True
