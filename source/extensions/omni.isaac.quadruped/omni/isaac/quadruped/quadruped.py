# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.robots.robot import Robot
import omni.isaac.dynamic_control._dynamic_control as omni_dc

from typing import Optional
import numpy as np
import carb


DOF_DRIVE_MODE = {
    "force": int(omni_dc.DriveMode.DRIVE_FORCE),
    "acceleration": int(omni_dc.DriveMode.DRIVE_ACCELERATION),
}
"""Mapping from drive mode names to  drive mode in DC Toolbox type."""

DOF_CONTROL_MODE = {"position": 0, "velocity": 1, "effort": 2}
"""Mapping between control modes to integers."""


class Quadruped(Robot):
    """Generic Quadruped Class"""

    def __init__(
        self,
        prim_path: str,
        name: str = "quadruped",
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """initialize robot, set up sensors and controller
        
        Args:
            prim_path {str} -- prim path of the robot on the stage
            name {str} -- name of the quadruped
            position {np.ndarray} -- position of the robot
            orientation {np.ndarray} -- orientation of the robot
        
        """
        super().__init__(
            prim_path=prim_path, name=name, position=position, orientation=orientation, articulation_controller=None
        )

    def check_dc_interface(self) -> None:
        """[summary]
        
        Checks the DC interface handle of the robot
        
        Raises:
            RuntimeError: When the DC Toolbox interface has not been configured. 
        """
        if self._handle == omni_dc.INVALID_HANDLE or self._handle is None:
            raise RuntimeError(f"Failed to obtain articulation handle at: '{self._prim_path}'")
        return True

    def set_dof_drive_mode(self, drive) -> None:
        """[summary]
        
        Set drive mode of the quadruped to force or acceleration
        
        Args:
            drive {List[str]} -- drive mode of the robot, can be either "force" or "acceleration"

        """
        self.check_dc_interface()
        dof_props = self._dc_interface.get_articulation_dof_properties(self._handle)
        if not isinstance(drive, list):
            drive = [drive] * self.num_dof
        if not len(drive) == self.num_dof:
            msg = f"Insufficient number of DOF drive modes specified. Expected: {self.num_dof}. Received: {len(drive)}."
            carb.log_error(msg)
        for index, drive_mode in enumerate(drive):
            # set drive mode
            try:
                dof_props["driveMode"][index] = DOF_DRIVE_MODE[drive_mode]
            except AttributeError:
                msg = f"Invalid articulation drive mode '{drive_mode}'. Supported drive types: {DOF_DRIVE_MODE.keys()}"
                raise ValueError(msg)
        # Set the properties into simulator
        self._dc_interface.set_articulation_dof_properties(self._handle, dof_props)

    def set_dof_control(self, control, kp, kd, drive) -> None:
        """[summary]
        
        Set dof control to position, velocity or effort
        
        Args:
            control {int or List[int]}: DOF control mode, can be  {"position": 0, "velocity": 1, "effort": 2}
            kp {float or List[float]}: proportional constant
            kd {float or List[float]}: derivative constant
            drive {int or List[int]}: DOF drive mode, can be "force": int(omni_dc.DriveMode.DRIVE_FORCE) or "acceleration": int(omni_dc.DriveMode.DRIVE_ACCELERATION)
        """
        self.check_dc_interface()
        # Extend to list if values provided
        if not isinstance(control, list):
            control = [control] * self.num_dof
        if not isinstance(kp, list):
            kp = [kp] * self.num_dof
        if not isinstance(kd, list):
            kd = [kd] * self.num_dof

        # Check that lists are of the correct size
        if not len(control) == self.num_dof:
            msg = f"Insufficient number of DOF control modes specified. Expected: {self.num_dof}. Received: {len(control)}."
            raise ValueError(msg)
        if not len(kp) == self.num_dof:
            msg = f"Insufficient number of DOF stiffness specified. Expected: {self.num_dof}. Received: {len(kp)}."
            raise ValueError(msg)
        if not len(kd) == self.num_dof:
            msg = f"Insufficient number of DOF damping specified. Expected: {self.num_dof}. Received: {len(kd)}."
            raise ValueError(msg)

        dof_props = self._dc_interface.get_articulation_dof_properties(self._handle)
        for index, (control_mode, stiffness, damping) in enumerate(zip(control, kp, kd)):
            # set control mode
            try:
                control_value = DOF_CONTROL_MODE[control_mode]
                self._dof_control_modes.append(control_value)
            except AttributeError:
                msg = f"Invalid articulation control mode '{control_mode}'. Supported control types: {DOF_CONTROL_MODE.keys()}"
                raise ValueError(msg)

            # set drive mode
            dof_props["driveMode"][index] = DOF_DRIVE_MODE[drive]
            # set the gains
            if stiffness is not None:
                dof_props["stiffness"][index] = stiffness
            if damping is not None:
                dof_props["damping"][index] = damping

        # Set the properties into simulator
        self._dc_interface.set_articulation_dof_properties(self._handle, dof_props)
        return

    def update(self) -> None:
        """[summary]
        
        Update quadruped's internal variables and environment
        
        Raises:
            NotImplementedError if not implemented
        """
        raise NotImplementedError

    def advance(self) -> None:
        """[summary]
        
        Compute torque applied on each joint

        Raises:
            NotImplementedError if not implemented
        """
        raise NotImplementedError

    def initialize(self, physics_sim_view=None) -> None:
        """[summary]
        
        initialize dc interface
        """
        super().initialize(physics_sim_view=physics_sim_view)

    def post_reset(self) -> None:
        """[summary]
        
        post reset articulation
        """
        super().post_reset()
