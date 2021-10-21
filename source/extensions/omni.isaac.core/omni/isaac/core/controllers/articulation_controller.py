# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
import numpy as np
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.types import ArticulationAction


class DOFArticulationController(object):
    def __init__(self, articulation_handle: int, dof_handle: int, dof_index: int) -> None:
        """[summary]

        Args:
            articulation_handle (int): [description]
            dof_handle (int): [description]
            dof_index (int): [description]
        """
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._articulation_handle = articulation_handle
        self._dof_index = dof_index
        self._dof_handle = dof_handle
        return

    def set_gains(self, dof_props: np.ndarray, kp: Optional[float] = None, kd: Optional[float] = None) -> None:
        """[summary]

        Args:
            dof_props (np.ndarray): [description]
            kp (Optional, optional): [description]. Defaults to None.
            kd (Optional, optional): [description]. Defaults to None.
        """
        if kp is not None:
            dof_props["stiffness"][self._dof_index] = kp
        if kp is not None:
            dof_props["damping"][self._dof_index] = kd
        self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
        return

    def get_gains(self, dof_props) -> None:
        """[summary]

        Args:
            dof_props (np.ndarray): [description]
            kp (Optional, optional): [description]. Defaults to None.
            kd (Optional, optional): [description]. Defaults to None.
        """
        return dof_props["stiffness"][self._dof_index], dof_props["damping"][self._dof_index]

    def apply_action(self, control_action: dict) -> None:
        """[summary]

        Args:
            control_action (dict): [description]
        """
        if "effort" in control_action:
            self._dc_interface.apply_dof_effort(self._dof_handle, control_action["effort"])
        if "position" in control_action:
            self._dc_interface.set_dof_position_target(self._dof_handle, control_action["position"])
        if "velocity" in control_action:
            self._dc_interface.set_dof_velocity_target(self._dof_handle, control_action["velocity"])
        return

    def get_applied_action(self):
        # TODO: check pds before returning them
        return {
            "effort": None,
            "position": self._dc_interface.get_dof_position_target(self._dof_handle),
            "velocity": self._dc_interface.get_dof_velocity_target(self._dof_handle),
        }


class ArticulationController(object):
    def __init__(self) -> None:
        """[summary]

        Args:
            articulation_handle (int): [description]
            dofs_info (dict): [description]
        """
        self._dof_controllers = list()
        self._articulation_handle = None
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._default_kps = None
        self._default_kds = None
        return

    def initialize_handles(self, handle, dof_infos):
        self._articulation_handle = handle
        for dof_name, dof_info in dof_infos.items():
            self._dof_controllers.append(DOFArticulationController(handle, dof_info.handle, dof_info.index))
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        self._default_kps = [dof_props["stiffness"][i] for i in range(len(dof_infos))]
        self._default_kds = [dof_props["damping"][i] for i in range(len(dof_infos))]
        return

    def apply_action(self, control_actions: ArticulationAction, indices=None) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): [description]
        """
        self._dc_interface.wake_up_articulation(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        for i in range(len(indices)):
            self._dof_controllers[indices[i]].apply_action(control_actions.get_dof_action(i))
        return

    def set_gains(self, kps: Optional[np.ndarray] = None, kds: Optional[np.ndarray] = None) -> None:
        """[summary]

        Args:
            kps (Optional, optional): [description]. Defaults to None.
            kds (Optional, optional): [description]. Defaults to None.
        """
        if kps is None:
            kps = np.array([None] * len(self._dof_controllers))
        if kds is None:
            kds = np.array([None] * len(self._dof_controllers))
        for i in range(len(self._dof_controllers)):
            dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
            self._dof_controllers[i].set_gains(dof_props, kp=kps[i], kd=kds[i])
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        self._default_kps = [dof_props["stiffness"][i] for i in range(len(self._dof_controllers))]
        self._default_kds = [dof_props["damping"][i] for i in range(len(self._dof_controllers))]
        return

    def get_gains(self):
        kps = np.zeros(len(self._dof_controllers))
        kds = np.zeros(len(self._dof_controllers))
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        for i in range(len(self._dof_controllers)):
            dof_kp, dof_kd = self._dof_controllers[i].get_gains(dof_props)
            kps[i] = dof_kp
            kds[i] = dof_kd
        return kps, kds

    def switch_control_mode(self, mode: str) -> None:
        """[summary]

        Args:
            mode (str): [description]
        """
        # TODO: add logging and error handling
        for i in range(len(self._dof_controllers)):
            self.switch_dof_control_mode(dof_index=i, mode=mode)
        return

    def switch_dof_control_mode(self, dof_index: int, mode: str) -> None:
        """[summary]

        Args:
            dof_index (int): [description]
            mode (str): [description]
        """
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if mode == "velocity":
            self._dof_controllers[dof_index].set_gains(dof_props=dof_props, kp=0, kd=self._default_kds[dof_index])
        elif mode == "position":
            self._dof_controllers[dof_index].set_gains(
                dof_props=dof_props, kp=self._default_kps[dof_index], kd=self._default_kds[dof_index]
            )
        elif mode == "effort":
            self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
            self._dof_controllers[dof_index].set_gains(dof_props=dof_props, kp=0, kd=0)
        return

    def set_max_efforts(self, value=None, indices=None):
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        for i in range(len(indices)):
            dof_props["maxEffort"][indices[i]] = value
        self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
        return

    def get_max_efforts(self):
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        max_forces = np.zeros(len(self._dof_controllers))
        for i in range(len(self._dof_controllers)):
            max_forces[i] = dof_props["maxEffort"][i]
        return max_forces

    def set_effort_modes(self, mode, indices=None):
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        for i in range(len(indices)):
            if mode == "force":
                dof_props["driveMode"][indices[i]] = _dynamic_control.DRIVE_FORCE
            elif mode == "accelaration":
                dof_props["driveMode"][indices[i]] = _dynamic_control.DRIVE_ACCELERATION
            else:
                raise Exception("not recognized effort mode: {}".format(mode))
        self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
        return

    def get_effort_modes(self):
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        effort_modes = [None] * len(self._dof_controllers)
        for i in range(len(self._dof_controllers)):
            if dof_props["driveMode"][i] == _dynamic_control.DRIVE_FORCE:
                effort_modes[i] = "force"
            elif dof_props["driveMode"][i] == _dynamic_control.DRIVE_ACCELERATION:
                effort_modes[i] = "accelaration"
            else:
                raise NotImplementedError
        return effort_modes

    def get_joint_limits(self):
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        upper_limits = [None] * len(self._dof_controllers)
        lower_limits = [None] * len(self._dof_controllers)
        for i in range(len(self._dof_controllers)):
            if dof_props["has_limits"][i]:
                upper_limits[i] = dof_props["upper"][i]
                lower_limits[i] = dof_props["lower"][i]
            else:
                continue
        return lower_limits, upper_limits

    def get_applied_action(self):
        joint_positions = np.zeros(len(self._dof_controllers))
        joint_velocities = np.zeros(len(self._dof_controllers))
        # TODO: waiting on a jira
        joint_efforts = None
        for dof_index in range(len(self._dof_controllers)):
            dof_applied_action = self._dof_controllers[dof_index].get_applied_action()
            joint_positions[dof_index] = dof_applied_action["position"]
            joint_velocities[dof_index] = dof_applied_action["velocity"]

        return ArticulationAction(
            joint_positions=joint_positions, joint_velocities=joint_velocities, joint_efforts=joint_efforts
        )
