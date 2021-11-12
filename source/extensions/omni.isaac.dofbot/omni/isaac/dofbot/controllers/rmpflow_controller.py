# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.motion_generation as mg


class RMPFlowController(mg.RMPFlowController):
    """[summary]

        Args:
            name (str): [description]
            robot_prim_path (str): [description]
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """

    def __init__(self, name: str, robot_prim_path: str, physics_dt: float = 1.0 / 60.0) -> None:
        mg.RMPFlowController.__init__(
            self,
            name=name,
            robot_prim_path=robot_prim_path,
            policy_map_path=["DofBot", "RMPflow"],
            physics_dt=physics_dt,
        )
        return
