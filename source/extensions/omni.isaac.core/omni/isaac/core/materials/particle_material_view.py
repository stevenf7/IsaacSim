# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import torch
import numpy as np
from typing import Optional, Tuple, Union

# omniverse
import carb
import omni.kit.app

# isaac-core
import omni.kit.app
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import get_prim_at_path, find_matching_prim_paths, is_prim_path_valid


class ParticleMaterialView:
    """The view class to deal with particleMaterial prims.
        Provides high level functions to deal with particle material (1 or more particle materials) 
        as well as its attributes/ properties. This object wraps all matching materials found at the regex provided at the prim_paths_expr.
        This object wraps all matching materials Prims found at the regex provided at the prim_paths_expr.
    """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "particle_material_view",
        friction: Optional[Union[np.ndarray, torch.Tensor]] = None,
        damping: Optional[Union[np.ndarray, torch.Tensor]] = None,
        gravity_scale: Optional[Union[np.ndarray, torch.Tensor]] = None,
        lift: Optional[Union[np.ndarray, torch.Tensor]] = None,
        drag: Optional[Union[np.ndarray, torch.Tensor]] = None,
    ):
        """
        Args:
            prim_paths_expr(str): Prim paths regex to encapsulate all prims that match it.
            name(str): Shortname to be used as a key by Scene class.
            friction: (Union[np.ndarray, torch.Tensor], optional): Default friction tensor of the prims, shape is (N, ).
            damping: (Union[np.ndarray, torch.Tensor], optional): Default damping tensor of the prims, shape is (N, ).
            gravity_scale: (Union[np.ndarray, torch.Tensor], optional): Default gravity_scale tensor of the prims, shape is (N, ).
            lift: (Union[np.ndarray, torch.Tensor], optional): Default lift tensor of the prims, shape is (N, ).
            drag: (Union[np.ndarray, torch.Tensor], optional): Default drag tensor of the prims, shape is (N, ).
        """
        self._name = name
        self._physics_view = None
        self._prim_paths = find_matching_prim_paths(prim_paths_expr)
        if len(self._prim_paths) == 0:
            raise Exception(
                "Prim path expression {} is invalid, a prim matching the expression needs to created before wrapping it as view".format(
                    prim_paths_expr
                )
            )
        self._count = len(self._prim_paths)
        self._prims = []
        self._regex_prim_paths = prim_paths_expr
        for prim_path in self._prim_paths:
            self._prims.append(get_prim_at_path(prim_path))

        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._backend_utils = SimulationContext.instance().backend_utils
        else:
            import omni.isaac.core.utils.numpy as np_utils

            self._backend = "numpy"
            self._backend_utils = np_utils

        # NOTE: particleSystemView is only supported on the host
        self._device = "cpu"

        # set properties
        if friction is not None:
            self.set_friction(friction)
        if damping is not None:
            self.set_damping(damping)
        if gravity_scale is not None:
            self.set_gravity_scale(gravity_scale)
        if lift is not None:
            self.set_lift(lift)
        if drag is not None:
            self.set_drag(drag)

    """
    Properties.
    """

    @property
    def count(self) -> int:
        """
        Returns:
            int: number of rigid shapes for the prims in the view.
        """
        return self._count

    @property
    def name(self) -> str:
        """
        Returns:
            str: name given to the view when instantiating it.
        """
        return self._name

    def is_physics_handle_valid(self) -> bool:
        """
        Returns:
            bool: True if the physics handle of the view is valid (i.e physics is initialized for the view). Otherwise False.
        """
        return self._physics_view is not None

    def is_valid(self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None) -> bool:
        """
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            bool: True if all prim paths specified in the view correspond to a valid prim in stage. False otherwise.
        """

        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = True
        for index in indices:
            result = result and is_prim_path_valid(self._prim_paths[index.tolist()])
        return result

    def post_reset(self) -> None:
        """Resets the particles to their initial states.
        """
        # TODO:
        return

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates a rigid body view in physX.

        Args:
            physics_sim_view (omni.physics.tensors.SimulationView, optional): current physics simulation view. Defaults to None.
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_sim_view = physics_sim_view
        self._physics_view = self._physics_sim_view.create_particle_material_view(
            self._regex_prim_paths.replace(".*", "*")
        )
        self._count = self._physics_view.count
        carb.log_info("Particle material View Device: {}".format(self._device))
        return

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

    def set_friction(
        self,
        values: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the friction for the material prims indicated by the indices.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]], optional): material friction tensor with the shape (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_values = self._backend_utils.move_data(values, self._device)
            current_values = self.get_friction(clone=False)
            current_values[indices] = new_values
            self._physics_view.set_friction(current_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_friction")

    def get_friction(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the friction of materials indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: friction tensor with shape (M, )
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_friction()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return current_values[indices]
            else:
                return self._backend_utils.clone_tensor(current_values[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_friction")
            return None

    def set_dampings(
        self,
        values: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the dampings for the material prims indicated by the indices.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]], optional): material damping tensor with the shape (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_values = self._backend_utils.move_data(values, self._device)
            current_values = self.get_dampings(clone=False)
            current_values[indices] = new_values
            self._physics_view.set_damping(current_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_dampings")

    def get_dampings(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the dampings of materials indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: dampings tensor with shape (M, )
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_damping()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return current_values[indices]
            else:
                return self._backend_utils.clone_tensor(current_values[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_dampings")
            return None

    def set_gravity_scales(
        self,
        values: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the gravity scales for the material prims indicated by the indices.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]], optional): material gravity scale tensor with the shape (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_values = self._backend_utils.move_data(values, self._device)
            current_values = self.get_gravity_scales(clone=False)
            current_values[indices] = new_values
            self._physics_view.set_gravity_scale(current_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_gravity scales")

    def get_gravity_scales(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the gravity scales of materials indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: gravity scale tensor with shape (M, )
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_gravity_scale()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return current_values[indices]
            else:
                return self._backend_utils.clone_tensor(current_values[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_gravity scales")
            return None

    def set_lifts(
        self,
        values: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the lifts for the material prims indicated by the indices.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]], optional): material lift tensor with the shape (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_values = self._backend_utils.move_data(values, self._device)
            current_values = self.get_lifts(clone=False)
            current_values[indices] = new_values
            self._physics_view.set_lift(current_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_lifts")

    def get_lifts(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the lifts of materials indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: lifts tensor with shape (M, )
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_lift()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return current_values[indices]
            else:
                return self._backend_utils.clone_tensor(current_values[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_lifts")
            return None

    def set_drags(
        self,
        values: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the drags for the material prims indicated by the indices.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]], optional): material drag tensor with the shape (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_values = self._backend_utils.move_data(values, self._device)
            current_values = self.get_drags(clone=False)
            current_values[indices] = new_values
            self._physics_view.set_drag(current_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_drag")

    def get_drags(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the drags of materials indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which material prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: drag tensor with shape (M, )
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_drag()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return current_values[indices]
            else:
                return self._backend_utils.clone_tensor(current_values[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_drags")
            return None
