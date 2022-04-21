# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple, Union, List
import numpy as np
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import UsdPhysics


class DOFArticulationController(object):
    """PD Controller of one degree of freedom, can apply position targets, velocity targets and efforts.

        Args:
            articulation_handle (int): [description]
            dof_handle (int): [description]
            dof_index (int): [description]
        """

    def __init__(self, articulation_handle: int, dof_handle: int, dof_index: int) -> None:
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._articulation_handle = articulation_handle
        self._dof_index = dof_index
        self._dof_handle = dof_handle
        return

    def set_gains(
        self, dof_props: np.ndarray, kp: Optional[float] = None, kd: Optional[float] = None, save_to_usd: bool = False
    ) -> None:
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
        if save_to_usd:
            dof_prim_path = self._dc_interface.get_dof_path(self._dof_handle)
            dof_type = dof_props["type"][self._dof_index]
            prim = get_prim_at_path(dof_prim_path)
            drive_type = "angular" if dof_type == 1 else "linear"
            if prim.HasAPI(UsdPhysics.DriveAPI):
                drive = UsdPhysics.DriveAPI(prim, drive_type)
            else:
                drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
            if kp is not None:
                # We need to convert physx (1/rad) to usd (1/deg)
                kp = 1.0 / np.rad2deg(float(1.0 / kp))
                if not drive.GetStiffnessAttr():
                    drive.CreateStiffnessAttr(kp)
                else:
                    drive.GetStiffnessAttr().Set(kp)
            if kd is not None:
                # We need to convert physx (1/rad) to usd (1/deg)
                kd = 1.0 / np.rad2deg(float(1.0 / kd))
                if not drive.GetDampingAttr():
                    drive.CreateDampingAttr(kd)
                else:
                    drive.GetDampingAttr().Set(kd)
        return

    def get_gains(self, dof_props) -> Tuple[float, float]:
        """[summary]

        Args:
            dof_props ([type]): [description]

        Returns:
            Tuple[float, float]: [description]
        """
        return dof_props["stiffness"][self._dof_index], dof_props["damping"][self._dof_index]

    def apply_action(self, control_action: dict) -> None:
        """[summary]

        Args:
            control_action (dict): [description]
        """
        if "effort" in control_action:
            self._dc_interface.set_dof_effort(self._dof_handle, control_action["effort"])
        if "position" in control_action:
            self._dc_interface.set_dof_position_target(self._dof_handle, control_action["position"])
        if "velocity" in control_action:
            self._dc_interface.set_dof_velocity_target(self._dof_handle, control_action["velocity"])
        return

    def get_applied_action(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return {
            "effort": None,
            "position": self._dc_interface.get_dof_position_target(self._dof_handle),
            "velocity": self._dc_interface.get_dof_velocity_target(self._dof_handle),
        }


class ArticulationController(object):
    """PD Controller of all degrees of freedom of an articulation, can apply position targets, velocity targets and efforts.

        Checkout the required tutorials at 
         https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html   
        """

    def __init__(self) -> None:
        self._dof_controllers = list()
        self._articulation_handle = None
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._default_kps = None
        self._default_kds = None
        return

    def initialize(self, handle, dof_infos) -> None:
        """[summary]

        Args:
            handle ([type]): [description]
            dof_infos ([type]): [description]
        """
        self._articulation_handle = handle
        for dof_name, dof_info in dof_infos.items():
            self._dof_controllers.append(DOFArticulationController(handle, dof_info.handle, dof_info.index))
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        self._default_kps = [dof_props["stiffness"][i] for i in range(len(dof_infos))]
        self._default_kds = [dof_props["damping"][i] for i in range(len(dof_infos))]
        return

    def apply_action(
        self, control_actions: ArticulationAction, indices: Optional[Union[List, np.ndarray]] = None
    ) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): actions to be applied for next physics step.
            indices (Optional[Union[list, np.ndarray]], optional): degree of freedom indices to apply actions to.
                                                                   Defaults to all degrees of freedom.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        self._dc_interface.wake_up_articulation(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        actions_length = control_actions.get_length()
        if actions_length is not None and (actions_length != len(indices)):
            raise Exception("ArticulationAction passed should be equal to the number of dofs")
        for i in range(len(indices)):
            self._dof_controllers[indices[i]].apply_action(control_actions.get_dof_action(i))
        return

    def set_gains(
        self, kps: Optional[np.ndarray] = None, kds: Optional[np.ndarray] = None, save_to_usd: bool = False
    ) -> None:
        """[summary]

        Args:
            kps (Optional[np.ndarray], optional): [description]. Defaults to None.
            kds (Optional[np.ndarray], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        if kps is None:
            kps = np.array([None] * len(self._dof_controllers))
        if kds is None:
            kds = np.array([None] * len(self._dof_controllers))
        for i in range(len(self._dof_controllers)):
            dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
            self._dof_controllers[i].set_gains(dof_props, kp=kps[i], kd=kds[i], save_to_usd=save_to_usd)
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        self._default_kps = [dof_props["stiffness"][i] for i in range(len(self._dof_controllers))]
        self._default_kds = [dof_props["damping"][i] for i in range(len(self._dof_controllers))]
        return

    def get_gains(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
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

        Raises:
            Exception: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        for i in range(len(self._dof_controllers)):
            self.switch_dof_control_mode(dof_index=i, mode=mode)
        return

    def switch_dof_control_mode(self, dof_index: int, mode: str) -> None:
        """[summary]

        Args:
            dof_index (int): [description]
            mode (str): [description]

        Raises:
            Exception: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
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

    def set_max_efforts(self, value: float = None, indices: Optional[Union[np.ndarray, list]] = None) -> None:
        """[summary]

        Args:
            value (float, optional): [description]. Defaults to None.
            indices (Optional[Union[np.ndarray, list]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        for i in range(len(indices)):
            dof_props["maxEffort"][indices[i]] = value
        self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
        return

    def get_max_efforts(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        max_forces = np.zeros(len(self._dof_controllers))
        for i in range(len(self._dof_controllers)):
            max_forces[i] = dof_props["maxEffort"][i]
        return max_forces

    def set_effort_modes(self, mode: str, indices: Optional[Union[np.ndarray, list]] = None) -> None:
        """[summary]

        Args:
            mode (str): [description]
            indices (Optional[Union[np.ndarray, list]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        if indices is None:
            indices = list(range(len(self._dof_controllers)))
        for i in range(len(indices)):
            if mode == "force":
                dof_props["driveMode"][indices[i]] = _dynamic_control.DRIVE_FORCE
            elif mode == "acceleration":
                dof_props["driveMode"][indices[i]] = _dynamic_control.DRIVE_ACCELERATION
            else:
                raise Exception("not recognized effort mode: {}".format(mode))
        self._dc_interface.set_articulation_dof_properties(self._articulation_handle, dof_props)
        return

    def get_effort_modes(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]
            NotImplementedError: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
        dof_props = self._dc_interface.get_articulation_dof_properties(self._articulation_handle)
        effort_modes = [None] * len(self._dof_controllers)
        for i in range(len(self._dof_controllers)):
            if dof_props["driveMode"][i] == _dynamic_control.DRIVE_FORCE:
                effort_modes[i] = "force"
            elif dof_props["driveMode"][i] == _dynamic_control.DRIVE_ACCELERATION:
                effort_modes[i] = "acceleration"
            else:
                raise NotImplementedError
        return effort_modes

    def get_joint_limits(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
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

    def get_applied_action(self) -> ArticulationAction:
        """

        Raises:
            Exception: [description]

        Returns:
            ArticulationAction: Gets last applied action.
        """
        if self._articulation_handle is None:
            raise Exception("controller handles are not initialized yet")
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
