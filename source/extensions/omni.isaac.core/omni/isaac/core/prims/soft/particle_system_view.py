# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from typing import Optional, Sequence, Tuple, Union, List

# omniverse
from pxr import PhysxSchema, Usd
import carb

# isaac-core
import omni.kit.app
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import get_prim_at_path, find_matching_prim_paths, is_prim_path_valid

import numpy as np
import torch


class ParticleSystemView:
    """Provides high level functions to deal with particle systems (1 or more particle systems) as well as its attributes/ properties.
    This object wraps all matching particle systems found at the regex provided at the prim_paths_expr.
    Note: not all the attributes of the PhysxSchema.PhysxParticleSystem is currently controlled with this view class
    Tensor API support will be added in the future to extend the functionality of this class to applications beyond cloth.
    """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "particle_system_view",
        particle_contact_offset: Optional[Union[np.ndarray, torch.Tensor]] = None,
        solid_rest_offset: Optional[Union[np.ndarray, torch.Tensor]] = None,
        fluid_rest_offset: Optional[Union[np.ndarray, torch.Tensor]] = None,
        wind: Optional[Union[np.ndarray, torch.Tensor]] = None,
    ):
        """high level functions to deal with one or more particleSystems.
        Args:
            prim_path (str): The path to the particle system.
            contact_offset (Optional[Union[np.ndarray, torch.Tensor]], optional): Contact offset used for collisions with non-particle
                objects such as rigid or deformable bodies.
            particle_contact_offset (Optional[Union[np.ndarray, torch.Tensor]], optional): Contact offset used for interactions
                between particles. Must be larger than solid and fluid rest offsets.
            solid_rest_offset (Optional[Union[np.ndarray, torch.Tensor]], optional): Rest offset used for solid-solid or solid-fluid
                particle interactions. Must be smaller than particle contact offset.
            fluid_rest_offset (Optional[Union[np.ndarray, torch.Tensor]], optional): Rest offset used for fluid-fluid particle interactions.
                Must be smaller than particle contact offset.
            wind (Optional[Union[np.ndarray, torch.Tensor]], optional):The wind applied to the current particle system.
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

        # TODO: particleSystemView is currently supported only on the host
        self._device = "cpu"

        # set properties
        if particle_contact_offset is not None:
            self.set_particle_contact_offsets(particle_contact_offset)
        if solid_rest_offset is not None:
            self.set_solid_rest_offsets(solid_rest_offset)
        if fluid_rest_offset is not None:
            self.set_fluid_rest_offsets(fluid_rest_offset)
        if wind is not None:
            self.set_wind(wind)

        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._invalidate_physics_handle_callback
        )
        return

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

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates a Particle System View.

        Args:
            physics_sim_view (omni.physics.tensors.SimulationView, optional): current physics simulation view. Defaults to None.
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_sim_view = physics_sim_view
        self._physics_view = physics_sim_view.create_particle_system_view(self._regex_prim_paths.replace(".*", "*"))
        self._count = self._physics_view.count
        carb.log_info("Particle System View Device: {}".format(self._device))
        return

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

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

    """
    Operations - Setters.
    """

    def set_particle_contact_offsets(
        self, values: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None
    ) -> None:
        """Set the contact offset used for interactions between particles.

        Note: Must be larger than solid and fluid rest offsets.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]]): The contact offset.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_values = self._backend_utils.clone_tensor(
                self._physics_view.get_particle_contact_offsets(), device=self._device
            )
            new_values[indices] = self._backend_utils.move_data(values, self._device)
            self._physics_view.set_particle_contact_offsets(new_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet to use set_particle_contact_offset")

    def set_solid_rest_offsets(
        self, values: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None
    ) -> None:
        """Set the rest offset used for solid-solid or solid-fluid particle interactions.

        Note: Must be smaller than particle contact offset.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]]): solid rest offset to set particle systems to. shape is (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_values = self._backend_utils.clone_tensor(
                self._physics_view.get_solid_rest_offsets(), device=self._device
            )
            new_values[indices] = self._backend_utils.move_data(values, self._device)
            self._physics_view.set_solid_rest_offsets(new_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet to use set_solid_rest_offset")

    def set_fluid_rest_offsets(
        self, values: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None
    ) -> None:
        """Set the rest offset used for fluid-fluid particle interactions.

        Note: Must be smaller than particle contact offset.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]]): fluid rest offset to set particle systems to. shape is (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).              
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_values = self._backend_utils.clone_tensor(
                self._physics_view.get_fluid_rest_offsets(), device=self._device
            )
            new_values[indices] = self._backend_utils.move_data(values, self._device)
            self._physics_view.set_fluid_rest_offsets(new_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet to use set_fluid_rest_offset")

    def set_winds(
        self, values: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None
    ) -> None:
        """Set the winds velocity applied to the current particle system.

        Args:
            values (Optional[Union[np.ndarray, torch.Tensor]]): The winds applied to the current particle system. shape is (M, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view). 
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_values = self._backend_utils.clone_tensor(self._physics_view.get_wind(), device=self._device)
            new_values[indices] = self._backend_utils.move_data(values, self._device)
            self._physics_view.set_wind(new_values, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet to use set_winds")

    """
    Operations - Getters.
    """

    def get_particle_contact_offsets(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor]: The contact offset used for interactions between particles in the view concatenated. shape is (M, ).  
        
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            self._physics_sim_view.enable_warnings(False)
            results = self._physics_view.get_particle_contact_offsets()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return results[indices]
            else:
                return self._backend_utils.clone_tensor(results, device=self._device)[indices]
        return None

    def get_solid_rest_offsets(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor]: The rest offset used for solid-solid or solid-fluid particle interactions. shape is (M, ).  
        
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            self._physics_sim_view.enable_warnings(False)
            results = self._physics_view.get_solid_rest_offsets()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return results[indices]
            else:
                return self._backend_utils.clone_tensor(results, device=self._device)[indices]
        return None

    def get_fluid_rest_offsets(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor]: The rest offset used for fluid-fluid particle interactions. shape is (M, ).  
        
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            self._physics_sim_view.enable_warnings(False)
            results = self._physics_view.get_fluid_rest_offsets()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return results[indices]
            else:
                return self._backend_utils.clone_tensor(results, device=self._device)[indices]
        return None

    def get_winds(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor]: The winds applied to the current particle system. shape is (M, 3).  
        
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            self._physics_sim_view.enable_warnings(False)
            results = self._physics_view.get_wind()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return results[indices]
            else:
                return self._backend_utils.clone_tensor(results, device=self._device)[indices]
        return None
