# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple, Union, List, Sequence
import numpy as np
from pxr import Usd
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils.types import JointsState, ArticulationAction
from omni.isaac.core.articulations.articulation_view import ArticulationView
from omni.isaac.core.controllers.articulation_controller import ArticulationController
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
import carb
from omni.isaac.core.utils.types import XFormPrimState
from omni.isaac.core.materials import VisualMaterial


class Articulation(object):
    """     
            Provides high level functions to deal with an articulation prim and its attributes/ properties.
        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "articulation".
            position (Optional[Sequence[float]], optional): [description]. Defaults to None.
            translation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            orientation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            scale (Optional[Sequence[float]], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            articulation_controller (Optional[ArticulationController], optional): a custom ArticulationController which
                                                                                  inherits from it. Defaults to creating the
                                                                                  basic ArticulationController.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "articulation",
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: Optional[bool] = None,
        articulation_controller: Optional[ArticulationController] = None,
    ) -> None:
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._device = SimulationContext.instance().device
            self._backend_utils = SimulationContext.instance().backend_utils
        else:
            import omni.isaac.core.utils.numpy as np_utils

            self._backend = "numpy"
            self._device = None
            self._backend_utils = np_utils
        if position is not None:
            position = self._backend_utils.expand_dims(position, 0)
        if translation is not None:
            translation = self._backend_utils.expand_dims(translation, 0)
        if orientation is not None:
            orientation = self._backend_utils.expand_dims(orientation, 0)
        if scale is not None:
            scale = self._backend_utils.expand_dims(scale, 0)
        if visible is not None:
            visible = self._backend_utils.create_tensor_from_list([visible], dtype="bool", device=self._device)
        self._articulation_view = ArticulationView(
            prim_paths_expr=prim_path,
            name=name,
            positions=position,
            translations=translation,
            orientations=orientation,
            scales=scale,
            visibilities=visible,
        )
        self._articulation_controller = articulation_controller
        if self._articulation_controller is None:
            self._articulation_controller = ArticulationController()
        self._handles_initialized = False
        self._handle = None
        return

    @property
    def prim_path(self) -> str:
        """
        Returns:
            str: prim path in the stage.
        """
        return self._articulation_view.prim_paths[0]

    @property
    def name(self) -> Optional[str]:
        """
        Returns:
            str: name given to the prim when instantiating it. Otherwise None.
        """
        return self._articulation_view.name

    @property
    def prim(self) -> Usd.Prim:
        """
        Returns:
            Usd.Prim: USD Prim object that this object holds.
        """
        return self._articulation_view.prims[0]

    @property
    def non_root_articulation_link(self) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        return self._articulation_view._non_root_link

    @property
    def articulation_handle(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._handle

    @property
    def handles_initialized(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return self._handles_initialized

    @property
    def num_dof(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._articulation_view.num_dof

    @property
    def dof_properties(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._dc_interface.get_articulation_dof_properties(self._handle)

    @property
    def dof_names(self) -> List[str]:
        """List of prim names for each DOF.

        Returns:
            list(string): prim names
        """
        return self._articulation_view.dof_names

    def initialize(self, physics_sim_view=None):
        """[summary]
        """
        carb.log_info("initializing handles for {}".format(self.prim_path))
        self._handle = self._dc_interface.get_articulation(self.prim_path)
        self._root_handle = self._dc_interface.get_articulation_root_body(self._handle)
        self._articulation_controller.initialize(self._handle, self._articulation_view)
        self._articulation_view.initialize(physics_sim_view=physics_sim_view)
        self._handles_initialized = True
        return

    def get_dof_index(self, dof_name: str) -> int:
        """[summary]

        Args:
            dof_name (str): [description]

        Returns:
            int: [description]
        """
        return self._articulation_view.get_dof_index(dof_name=dof_name)

    def get_articulation_body_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._articulation_view.get_articulation_body_count()

    def disable_gravity(self) -> None:
        """Keep gravity from affecting the robot
        """
        for body_index in range(self._dc_interface.get_articulation_body_count(self._handle)):
            body = self._dc_interface.get_articulation_body(self._handle, body_index)
            self._dc_interface.set_rigid_body_disable_gravity(body, True)
        return

    def enable_gravity(self) -> None:
        """Gravity will affect the robot
        """
        for body_index in range(self._dc_interface.get_articulation_body_count(self._handle)):
            body = self._dc_interface.get_articulation_body(self._handle, body_index)
            self._dc_interface.set_rigid_body_disable_gravity(body, False)
        return

    def set_visibility(self, visible: bool) -> None:
        """Sets the visibility of the prim in stage.

        Args:
            visible (bool): flag to set the visibility of the usd prim in stage.
        """
        self._articulation_view.set_visibilities(
            self._backend_utils.create_tensor_from_list([visible], dtype="bool", device=self._device)
        )
        return

    def get_visibility(self) -> bool:
        """
        Returns:
            bool: true if the prim is visible in stage. false otherwise.
        """
        return self._articulation_view.get_visibilities()

    def set_joint_positions(
        self, positions: np.ndarray, joint_indices: Optional[Union[List, np.ndarray]] = None
    ) -> None:
        """[summary]

        Args:
            positions (np.ndarray): [description]
            indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        positions = self._backend_utils.expand_dims(positions, 0)
        if joint_indices is not None:
            joint_indices = self._backend_utils.expand_dims(joint_indices, 0)
        self._articulation_view.set_joint_positions(positions=positions, joint_indices=joint_indices)
        return

    def get_joint_positions(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        return self._articulation_view.get_joint_positions()[0]

    def set_joint_velocities(
        self, velocities: np.ndarray, joint_indices: Optional[Union[List, np.ndarray]] = None
    ) -> None:
        """[summary]

        Args:
            velocities (np.ndarray): [description]
            indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        velocities = self._backend_utils.expand_dims(velocities, 0)
        if joint_indices is not None:
            joint_indices = self._backend_utils.expand_dims(joint_indices, 0)
        self._articulation_view.set_joint_velocities(velocities=velocities, joint_indices=joint_indices)
        return

    def set_joint_efforts(self, efforts: np.ndarray, joint_indices: Optional[Union[List, np.ndarray]] = None) -> None:
        """[summary]

        Args:
            efforts (np.ndarray): [description]
            joint_indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        efforts = self._backend_utils.expand_dims(efforts, 0)
        if joint_indices is not None:
            joint_indices = self._backend_utils.expand_dims(joint_indices, 0)
        self._articulation_view.set_joint_efforts(efforts=efforts, joint_indices=joint_indices)
        return

    def get_joint_velocities(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        return self._articulation_view.get_joint_velocities()[0]

    def get_joint_efforts(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        joint_efforts = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        joint_efforts = [joint_efforts[i][2] for i in range(len(joint_efforts))]
        return np.array(joint_efforts)

    def get_joints_default_state(self) -> JointsState:
        """ Accessor for the default joints state.

        Returns:
            JointsState: The defaults that the robot is reset to when post_reset() is called (often
            automatically called during world.reset()).
        """
        joints_state = self._articulation_view.get_joints_default_state()
        return JointsState(positions=joints_state.positions[0], velocities=joints_state.velocities[0], efforts=None)

    def set_joints_default_state(
        self,
        positions: Optional[np.ndarray] = None,
        velocities: Optional[np.ndarray] = None,
        efforts: Optional[np.ndarray] = None,
    ) -> None:
        """[summary]

        Args:
            positions (Optional[np.ndarray], optional): [description]. Defaults to None.
            velocities (Optional[np.ndarray], optional): [description]. Defaults to None.
            efforts (Optional[np.ndarray], optional): [description]. Defaults to None.
        """
        if positions is not None:
            positions = self._backend_utils.expand_dims(positions, 0)
        if velocities is not None:
            velocities = self._backend_utils.expand_dims(velocities, 0)
        if efforts is not None:
            efforts = self._backend_utils.expand_dims(efforts, 0)
        self._articulation_view.set_joints_default_state(positions=positions, velocities=velocities, efforts=efforts)
        return

    def get_joints_state(self) -> JointsState:
        """[summary]

        Returns:
            JointsState: [description]
        """
        joints_state = self._articulation_view.get_joints_state()
        return JointsState(positions=joints_state.positions[0], velocities=joints_state.velocities[0], efforts=None)

    def get_default_state(self) -> XFormPrimState:
        """
        Returns:
            XFormPrimState: returns the default state of the prim (position and orientation) that is used after each reset.
        """
        view_default_state = self._articulation_view.get_default_state()
        default_state = self._view_state_conversion(view_default_state)
        return default_state

    def set_default_state(
        self, position: Optional[Sequence[float]] = None, orientation: Optional[Sequence[float]] = None
    ) -> None:
        """Sets the default state of the prim (position and orientation), that will be used after each reset.

        Args:
            position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[Sequence[float]], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if position is not None:
            position = self._backend_utils.convert(position, device=self._device)
            position = self._backend_utils.expand_dims(position, 0)
        if orientation is not None:
            orientation = self._backend_utils.convert(orientation, device=self._device)
            orientation = self._backend_utils.expand_dims(orientation, 0)
        self._articulation_view.set_default_state(positions=position, orientations=orientation)
        return

    def post_reset(self) -> None:
        """[summary]
        """
        self._articulation_view.post_reset()
        return

    def get_articulation_controller(self) -> ArticulationController:
        """
        Returns:
            ArticulationController: PD Controller of all degrees of freedom of an articulation, can apply position targets, velocity targets and efforts.
        """
        return self._articulation_controller

    def set_linear_velocity(self, velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage.

        Args:
            velocity (np.ndarray):linear velocity to set the rigid prim to. Shape (3,).
        """
        if velocity is not None:
            velocity = self._backend_utils.expand_dims(velocity, 0)
        return self._articulation_view.set_linear_velocities(velocities=velocity)

    def get_linear_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._articulation_view.get_linear_velocities()[0]

    def set_angular_velocity(self, velocity: np.ndarray) -> None:
        """[summary]

        Args:
            velocity (np.ndarray): [description]
        """
        if velocity is not None:
            velocity = self._backend_utils.expand_dims(velocity, 0)
        self._articulation_view.set_angular_velocities(velocities=velocity)

    def get_angular_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._articulation_view.get_angular_velocities()[0]

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets prim's pose with respect to the world's frame.

        Args:
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if position is not None:
            position = self._backend_utils.expand_dims(position, 0)
        if orientation is not None:
            orientation = self._backend_utils.expand_dims(orientation, 0)
        self._articulation_view.set_world_poses(positions=position, orientations=orientation)
        return

    def get_world_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the world's frame.

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the world frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        positions, orientations = self._articulation_view.get_world_poses()
        return positions[0], orientations[0]

    def set_local_pose(
        self, translation: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets prim's pose with respect to the local frame (the prim's parent frame).

        Args:
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if translation is not None:
            translation = self._backend_utils.expand_dims(translation, 0)
        if orientation is not None:
            orientation = self._backend_utils.expand_dims(orientation, 0)
        self._articulation_view.set_local_poses(translations=translation, orientations=orientation)

    def get_local_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the local frame (the prim's parent frame).

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the local frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the local frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        translations, orientations = self._articulation_view.get_local_poses()
        return translations[0], orientations[0]

    def apply_action(self, control_actions: ArticulationAction) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): actions to be applied for next physics step.
            indices (Optional[Union[list, np.ndarray]], optional): degree of freedom indices to apply actions to. 
                                                                   Defaults to all degrees of freedom.

        Raises:
            Exception: [description]
        """
        self._articulation_controller.apply_action(control_actions=control_actions)
        return

    def get_applied_action(self) -> ArticulationAction:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            ArticulationAction: [description]
        """
        return self._articulation_controller.get_applied_action()

    def set_solver_position_iteration_count(self, count: int) -> None:
        """[summary]

        Args:
            count (int): [description]
        """
        count = self._backend_utils.create_tensor_from_list([count], dtype="int32")
        self._articulation_view.set_solver_position_iteration_counts(count)
        return

    def get_solver_position_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._articulation_view.get_solver_position_iteration_counts()[0]

    def set_solver_velocity_iteration_count(self, count: int):
        """[summary]

        Args:
            count (int): [description]
        """
        count = self._backend_utils.create_tensor_from_list([count], dtype="int32")
        self._articulation_view.set_solver_velocity_iteration_counts(count)
        return

    def get_solver_velocity_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._articulation_view.get_solver_velocity_iteration_counts()[0]

    def set_stabilization_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        threshold = self._backend_utils.create_tensor_from_list([threshold], dtype="float32")
        self._articulation_view.set_stabilization_thresholds(threshold)
        return

    def get_stabilization_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self._articulation_view.get_stabilization_thresholds()[0]

    def set_enabled_self_collisions(self, flag: bool) -> None:
        """[summary]

        Args:
            flag (bool): [description]
        """
        flag = self._backend_utils.create_tensor_from_list([flag], dtype="bool")
        self._articulation_view.set_enabled_self_collisions(flag)
        return

    def get_enabled_self_collisions(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return self._articulation_view.get_enabled_self_collisions()[0]

    def set_sleep_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        threshold = self._backend_utils.create_tensor_from_list([threshold], dtype="float32")
        self._articulation_view.set_sleep_thresholds(threshold)
        return

    def get_sleep_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self._articulation_view.get_sleep_thresholds()[0]

    def apply_visual_material(self, visual_material: VisualMaterial, weaker_than_descendants: bool = False) -> None:
        """Used to apply visual material to the held prim and optionally its descendants.

        Args:
            visual_material (VisualMaterial): visual material to be applied to the held prim. Currently supports
                                              PreviewSurface, OmniPBR and OmniGlass.
            weaker_than_descendants (bool, optional): True if the material shouldn't override the descendants  
                                                      materials, otherwise False. Defaults to False.
        """
        self._articulation_view.apply_visual_materials(
            visual_materials=[visual_material], weaker_than_descendants=[weaker_than_descendants]
        )
        return

    def get_applied_visual_material(self) -> VisualMaterial:
        """Returns the current applied visual material in case it was applied using apply_visual_material OR
           it's one of the following materials that was already applied before: PreviewSurface, OmniPBR and OmniGlass.

        Returns:
            VisualMaterial: the current applied visual material if its type is currently supported.
        """
        return self._articulation_view.get_applied_visual_materials()[0]

    def is_visual_material_applied(self) -> bool:
        """
        Returns:
            bool: True if there is a visual material applied. False otherwise.
        """
        return self._articulation_view.is_visual_material_applied()[0]

    def get_world_scale(self) -> np.ndarray:
        """Gets prim's scale with respect to the world's frame.

        Returns:
            np.ndarray: scale applied to the prim's dimensions in the world frame. shape is (3, ).
        """
        return self._articulation_view.get_world_scales()[0]

    def set_local_scale(self, scale: Optional[Sequence[float]]) -> None:
        """Sets prim's scale with respect to the local frame (the prim's parent frame).

        Args:
            scale (Optional[Sequence[float]]): scale to be applied to the prim's dimensions. shape is (3, ).
                                          Defaults to None, which means left unchanged.
        """
        scale = self._backend_utils.convert(scale, device=self._device)
        scale = self._backend_utils.expand_dims(scale, 0)
        self._articulation_view.set_local_scales(scales=scale)
        return

    def get_local_scale(self) -> np.ndarray:
        """Gets prim's scale with respect to the local frame (the parent's frame).

        Returns:
            np.ndarray: scale applied to the prim's dimensions in the local frame. shape is (3, ).
        """
        return self._articulation_view.get_local_scales()[0]

    def is_valid(self) -> bool:
        """
        Returns:
            bool: True is the current prim path corresponds to a valid prim in stage. False otherwise.
        """
        return self._articulation_view.is_valid()
