# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import numpy as np
import omni.graph.core as og
from omni.isaac.wheeled_robots.robots.holonomic_robot_usd_setup import HolonomicRobotUsdSetup


class InternalState:
    def __init__(self):
        self.robot_prim_path = ""
        self.com_prim_path = ""
        self.wheel_radius = 0.0
        self.wheel_positions = np.array([])
        self.wheel_orientations = np.array([])
        self.mecanum_angles = 0.0
        self.wheel_dof_names = []
        self.robot_params = None
        self.initialized = False

    def initialize(self) -> None:
        print("getting robot parameters")
        self.robot_params = HolonomicRobotUsdSetup(
            robot_prim_path=self.robot_prim_path, com_prim_path=self.com_prim_path
        )
        self.initialized = True


class OgnHolonomicRobotUsdSetup:
    """
        nodes for bundling robot parameters for any robot to be used by differential and articulation controller
    """

    @staticmethod
    def internal_state():
        return InternalState()

    @staticmethod
    def compute(db) -> bool:
        try:
            # check about the using path vs bundle thing
            state = db.internal_state

            if db.inputs.usePath:
                robot_prim_path = db.inputs.robotPrimPath
                com_prim_path = db.inputs.comPrimPath
            else:
                if db.inputs.robotPrim.attributes == []:
                    return False
                else:
                    robot_prim_path = db.inputs.robotPrim.path
                    com_prim_path = db.inputs.comPrim.path

            if (robot_prim_path != state.robot_prim_path) or (com_prim_path != state.com_prim_path):
                state.robot_prim_path = robot_prim_path
                state.com_prim_path = com_prim_path
                state.initialized = False

            if not state.initialized:
                state.initialize()

            db.outputs.wheelRadius = state.robot_params.wheel_radius
            db.outputs.wheelPositions = state.robot_params.wheel_positions
            db.outputs.wheelOrientations = state.robot_params.wheel_orientations
            db.outputs.mecanumAngles = state.robot_params.mecanum_angles
            db.outputs.wheelDofNames = state.robot_params.wheel_dof_names

        except Exception as error:
            db.log_error(str(error))
            return False

        return True
