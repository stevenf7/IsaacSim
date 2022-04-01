# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.motion_generation as mg


class RMPFlowController(mg.MotionPolicyController):
    """[summary]

        Args:
            name (str): [description]
            robot_prim_path (str): [description]
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """

    def __init__(self, name: str, robot_prim_path: str, physics_dt: float = 1.0 / 60.0) -> None:
        self.rmp_flow_config = mg.interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        self.rmp_flow = mg.lula.motion_policies.RmpFlow(**self.rmp_flow_config)

        mg.MotionPolicyController.__init__(
            self, name=name, robot_prim_path=robot_prim_path, motion_policy=self.rmp_flow, physics_dt=physics_dt
        )
        return
