import os
from typing import Optional

from isaacsim.core.prims import Articulation
from isaacsim.robot_motion.motion_generation import ArticulationKinematicsSolver, LulaKinematicsSolver


class KinematicsSolver(ArticulationKinematicsSolver):
    def __init__(self, robot_articulation: Articulation, end_effector_frame_name: Optional[str] = None) -> None:
        # TODO: change the config path
        self._kinematics = LulaKinematicsSolver(
            robot_description_path=os.path.join(os.path.dirname(__file__), "../rmpflow/robot_descriptor.yaml"),
            urdf_path=os.path.join(os.path.dirname(__file__), "../rmpflow/ur10e.urdf"),
        )
        if end_effector_frame_name is None:
            end_effector_frame_name = "ee_link_robotiq_arg2f_base_link"
        ArticulationKinematicsSolver.__init__(self, robot_articulation, self._kinematics, end_effector_frame_name)
        return
