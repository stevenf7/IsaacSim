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
from pxr import Usd, UsdGeom

# isaac-core
from omni.isaac.core.prims import XFormPrimView
from omni.isaac.core.utils.types import XFormPrimViewState


class ClothPrimView(XFormPrimView):
    """The view class for cloth prims."""

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "cloth_prim_view",
        reset_xform_properties: bool = True,
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor]] = None,
    ):
        """
        Provides high level functions to deal with cloths (1 or more cloths) 
        as well as its attributes/ properties. This object wraps all matching cloths found at the regex provided at the prim_paths_expr.
        This object wraps all matching Cloth Prims found at the regex provided at the prim_paths_expr.

        Note: - if the prim does not already have a rigid body api applied to it before init, it will apply it.
        Args:
            prim_paths_expr(str): Prim paths regex to encapsulate all prims that match it.
            name(str): Shortname to be used as a key by Scene class.
            positions: (Union[np.ndarray, torch.Tensor], optional): Default positions in the world frame of the prim.
                shape is (N, 3).
            translations: (Union[np.ndarray, torch.Tensor], optional): Default translations in the local frame of the
                prims (with respect to its parent prims). shape is (N, 3).
            orientations: (Union[np.ndarray, torch.Tensor], optional): Default quaternion orientations in the world/
                local frame of the prim (depends if translation or position is specified).
                quaternion is scalar-first (w, x, y, z). shape is (N, 4).
            scales: (Union[np.ndarray, torch.Tensor], optional): Local scales to be applied to the prim’s dimensions.
                shape is (N, 3).
            visibilities: (Union[np.ndarray, torch.Tensor], optional): Set to false for an invisible prim in the stage
                while rendering. shape is (N,).
        """

        self._physics_view = None
        self._device = None
        self._count = None
        XFormPrimView.__init__(
            self,
            prim_paths_expr=prim_paths_expr,
            name=name,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            visibilities=visibilities,
            reset_xform_properties=reset_xform_properties,
        )
        self._default_state = XFormPrimViewState(self._default_state.positions, self._default_state.orientations)
        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._invalidate_physics_handle_callback
        )

    """
    Properties.
    """

    @property
    def count(self) -> int:
        """
        Returns:
            int: cloth counts.
        """
        return self._count

    @property
    def max_springs_per_cloth(self) -> int:
        """
        Returns:
            int: maximum number of springs per cloth.
        """
        return self._max_springs_per_cloth

    @property
    def max_particles_per_cloth(self) -> int:
        """
        Returns:
            int: maximum number of particles per cloth.
        """
        return self._max_particles_per_cloth

    def is_physics_handle_valid(self) -> bool:
        """
        Returns:
            bool: True if the physics handle of the view is valid (i.e physics is initialized for the view). Otherwise False.
        """
        return self._physics_view is not None

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
        self._physics_view = self._physics_sim_view.create_particle_cloth_view(
            self._regex_prim_paths.replace(".*", "*")
        )
        self._count = self._physics_view.count
        self._max_springs_per_cloth = self._physics_view.max_springs_per_cloth
        self._max_particles_per_cloth = self._physics_view.max_particles_per_cloth
        carb.log_info("Cloth Prim View Device: {}".format(self._device))
        return

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

    def set_world_positions(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the particle world positions for the cloths indicated by the indices.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor]], optional): particle positions with the shape 
                                                                                (M, max_particles_per_cloth, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_positions = self._backend_utils.move_to_gpu(positions)
            current_positions = self.get_world_positions(clone=False)
            current_positions[indices] = new_positions
            self._physics_view.set_positions(current_positions, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_world_positions")

    def get_world_positions(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the particle world positions for the cloths indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: position tensor with shape (M, max_particles_per_cloth, 3)
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            positions = self._physics_view.get_positions()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return positions[indices].reshape(len(indices), -1, 3)
            else:
                return self._backend_utils.clone_tensor(
                    positions[indices].reshape(len(indices), -1, 3), device=self._device
                )
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_world_positions")
            return None

    def set_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the particle velocities for the cloths indicated by the indices.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor]], optional): particle velocities with the shape 
                                                                                (M, max_particles_per_cloth, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_velocities = self._backend_utils.move_to_gpu(velocities)
            current_velocities = self.get_velocities(clone=False)
            current_velocities[indices] = new_velocities
            self._physics_view.set_velocities(current_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_velocities")

    def get_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the particle velocities for the cloths indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: velocity tensor with shape (M, max_particles_per_cloth, 3)
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return velocities[indices].reshape(len(indices), -1, 3)
            else:
                return self._backend_utils.clone_tensor(
                    velocities[indices].reshape(len(indices), -1, 3), device=self._device
                )
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_velocities")
            return None

    def set_particle_masses(
        self,
        masses: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the particle masses for the cloths indicated by the indices.

        Args:
            masses (Optional[Union[np.ndarray, torch.Tensor]], optional): cloth particle masses with the shape 
                                                                                (M, max_particles_per_cloth, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_masses = self._backend_utils.move_to_gpu(masses)
            current_masses = self.get_masses(clone=False)
            current_masses[indices] = new_masses
            self._physics_view.set_masses(current_masses, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_particle_masses")

    def get_particle_masses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the particle masses for the cloths indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: mass tensor with shape (M, max_particles_per_cloth)
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            masses = self._physics_view.get_masses()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return masses[indices]
            else:
                return self._backend_utils.clone_tensor(masses[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_particle_masses")
            return None

    def set_stretch_stiffnesses(
        self,
        stiffnesses: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the spring stiffnesses for the cloths indicated by the indices.

        Args:
            stiffnesses (Optional[Union[np.ndarray, torch.Tensor]], optional): cloth spring stiffness with the shape 
                                                                                (M, max_springs_per_cloth).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_stiffnesses = self._backend_utils.move_to_gpu(stiffnesses)
            current_stiffnesses = self.get_stretch_stiffnesses(clone=False)
            current_stiffnesses[indices] = new_stiffnesses
            self._physics_view.set_spring_stiffness(current_stiffnesses, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_stretch_stiffnesses")

    def get_stretch_stiffnesses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the spring stiffness for the cloths indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: stiffnesses tensor with shape (M, max_springs_per_cloth)
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            stiffnesses = self._physics_view.get_spring_stiffness()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return stiffnesses[indices]
            else:
                return self._backend_utils.clone_tensor(stiffnesses[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_stretch_stiffnesses")
            return None

    def set_spring_dampings(
        self,
        dampings: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the spring dampings for the cloths indicated by the indices.

        Args:
            dampings (Optional[Union[np.ndarray, torch.Tensor]], optional): cloth spring dampings with the shape 
                                                                            (M, max_springs_per_cloth).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            new_dampings = self._backend_utils.move_to_gpu(dampings)
            current_dampings = self.get_spring_dampings(clone=False)
            current_dampings[indices] = new_dampings
            self._physics_view.set_spring_damping(current_dampings, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_spring_dampings")

    def get_spring_dampings(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the spring dampings for the cloths indicated by the indices.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indices to specify which cloth prims to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: dampings tensor with shape (M, max_springs_per_cloth)
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            dampings = self._physics_view.get_spring_damping()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return dampings[indices]
            else:
                return self._backend_utils.clone_tensor(dampings[indices], device=self._device)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_spring_dampings")
            return None
