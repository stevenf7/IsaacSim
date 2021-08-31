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

    def apply_action(self, control_action: dict) -> None:
        """[summary]

        Args:
            control_action (dict): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError


class DOFPDController(DOFArticulationController):
    def __init__(self, articulation_handle: int, dof_handle: int, dof_index: int) -> None:
        """[summary]

        Args:
            articulation_handle (int): [description]
            dof_handle (int): [description]
            dof_index (int): [description]
        """
        super().__init__(articulation_handle, dof_handle, dof_index)
        return

    def set_gains(self, dof_props: np.ndarray, kp: Optional(float) = None, kd: Optional(float) = None) -> None:
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

    def apply_action(self, control_action: dict) -> None:
        """[summary]

        Args:
            control_action (dict): [description]
        """
        # TODO: discuss the naming of torque vs effort vs force ..etc and accelaration too?
        if "torque" in control_action:
            self._dc_interface.apply_dof_effort(self._dof_handle, control_action["torque"])
        if "position" in control_action:
            self._dc_interface.set_dof_position_target(self._dof_handle, control_action["position"])
        if "velocity" in control_action:
            self._dc_interface.set_dof_velocity_target(self._dof_handle, control_action["velocity"])
        return


class ArticulationController(object):
    def __init__(self, articulation_handle: int, dofs_info: dict) -> None:
        """[summary]

        Args:
            articulation_handle (int): [description]
            dofs_info (dict): [description]
        """
        pass

    def apply_action(self, control_actions: ArticulationAction) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError


class PDArticulationController(ArticulationController):
    def __init__(self, articulation_handle: int, dofs_info: dict) -> None:
        """[summary]

        Args:
            articulation_handle (int): [description]
            dofs_info (dict): [description]
        """
        super().__init__(articulation_handle=articulation_handle, dofs_info=dofs_info)
        self._dof_controllers = list()
        self._articulation_handle = articulation_handle
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        for dof_name, dof_info in dofs_info.items():
            self._dof_controllers.append(DOFPDController(articulation_handle, dof_info.handle, dof_info.index))
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        self._default_kps = [dof_props["stiffness"][i] for i in range(len(dofs_info))]
        self._default_kds = [dof_props["damping"][i] for i in range(len(dofs_info))]
        return

    def apply_action(self, control_actions: ArticulationAction) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): [description]
        """
        self._dc_interface.wake_up_articulation(self._articulation_handle)
        for i in range(len(self._dof_controllers)):
            self._dof_controllers[i].apply_action(control_actions.get_dof_action(i))
        return

    def set_gains(self, kps: Optional(np.ndarray) = None, kds: Optional(np.ndarray) = None) -> None:
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

    def switch_control_mode(self, mode: str) -> None:
        """[summary]

        Args:
            mode (str): [description]
        """
        # TODO: add logging and error handling
        if mode == "velocity":
            self.set_gains(kps=None, kds=[0] * len(self._dof_controllers))
        elif mode == "position":
            self.set_gains(kps=self._default_kps, kds=self._default_kds)
        elif mode == "force":
            dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
            for i in range(len(self._dof_controllers)):
                dof_props["driveMode"][i] = _dynamic_control.DRIVE_FORCE
            self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
            self.set_gains(kps=[0] * len(self._dof_controllers), kds=[0] * len(self._dof_controllers))
        elif mode == "accelaration":
            dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
            for i in range(len(self._dof_controllers)):
                dof_props["driveMode"][i] = _dynamic_control.DRIVE_ACCELERATION
            self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
            self.set_gains(kps=[0] * len(self._dof_controllers), kds=[0] * len(self._dof_controllers))
        return

    def switch_dof_control_mode(self, dof_index: int, mode: str) -> None:
        """[summary]

        Args:
            dof_index (int): [description]
            mode (str): [description]
        """
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if mode == "velocity":
            self._dof_controllers[dof_index].set_gains(dof_props=dof_props, kp=None, kd=0)
        elif mode == "position":
            self._dof_controllers[dof_index].set_gains(
                dof_props=dof_props, kp=self._default_kps[dof_index], kd=self._default_kds[dof_index]
            )
        elif mode == "force":
            dof_props["driveMode"][dof_index] = _dynamic_control.DRIVE_FORCE
            self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
            self._dof_controllers[dof_index].set_gains(dof_props=dof_props, kp=0, kd=0)
        elif mode == "accelaration":
            dof_props["driveMode"][dof_index] = _dynamic_control.DRIVE_ACCELERATION
            self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
            self._dof_controllers[dof_index].set_gains(dof_props=dof_props, kp=0, kd=0)
        return
