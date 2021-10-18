from abc import abstractmethod
from omni.isaac.core.controllers import BaseController


class BaseGripperController(BaseController):
    def __init__(self, name: str, gripper_dof_indices) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        self._name = name
        self._grippers_dof_indices = gripper_dof_indices
        return

    @property
    def grippers_dof_indices(self):
        return self._grippers_dof_indices

    # TODO: pass other args down
    def forward(self, action, current_joint_positions):
        if action == "open":
            return self.open(current_joint_positions)
        elif action == "close":
            return self.close(current_joint_positions)
        else:
            raise Exception("The action is not recognized, it has to be either open or close")

    @abstractmethod
    def open(self, current_joint_positions):
        raise NotImplementedError

    @abstractmethod
    def close(self, current_joint_positions):
        raise NotImplementedError

    def reset(self) -> None:
        """[summary]
        """
        return
