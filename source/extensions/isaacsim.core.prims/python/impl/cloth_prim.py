# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provides high-level cloth prim management functionality for cloth simulation objects in Isaac Sim."""


from typing import Optional, Union

import carb
import carb.eventdispatcher
import numpy as np
import omni.kit.app
import omni.timeline
from isaacsim.core.deprecation_manager import import_module
from pxr import PhysxSchema, UsdPhysics, Vt

from .xform_prim import XFormPrim

torch = import_module("torch")


class ClothPrim(XFormPrim):
    """The view class for cloth prims."""

    def __init__(
        self,
        prim_paths_expr: str,
        particle_systems: np.ndarray | torch.Tensor = None,
        particle_materials: np.ndarray | torch.Tensor | None = None,
        name: str = "cloth_prim_view",
        reset_xform_properties: bool = True,
        positions: np.ndarray | torch.Tensor | None = None,
        translations: np.ndarray | torch.Tensor | None = None,
        orientations: np.ndarray | torch.Tensor | None = None,
        scales: np.ndarray | torch.Tensor | None = None,
        visibilities: np.ndarray | torch.Tensor | None = None,
        particle_masses: np.ndarray | torch.Tensor | None = None,
        pressures: np.ndarray | torch.Tensor | None = None,
        particle_groups: np.ndarray | torch.Tensor | None = None,
        self_collisions: np.ndarray | torch.Tensor | None = None,
        self_collision_filters: np.ndarray | torch.Tensor | None = None,
        stretch_stiffnesses: np.ndarray | torch.Tensor | None = None,
        bend_stiffnesses: np.ndarray | torch.Tensor | None = None,
        shear_stiffnesses: np.ndarray | torch.Tensor | None = None,
        spring_dampings: np.ndarray | torch.Tensor | None = None,
    ):
        """
        Provides high level functions to deal with cloths (1 or more cloths)
        as well as its attributes/ properties. This object wraps all matching cloths found at the regex provided at the prim_paths_expr.
        This object wraps all matching Cloth Prims found at the regex provided at the prim_paths_expr.

        Note: - if the prim does not already have a rigid body api applied to it before init, it will apply it.

        Args:
            prim_paths_expr: Prim paths regex to encapsulate all prims that match it.
            particle_systems: Particle systems to be applied to each prim.
            particle_materials: Particle materials to be applied to each prim.
            name: Shortname to be used as a key by Scene class.
            reset_xform_properties: Whether to reset the transformation operation attributes of the prims to a standard
                set.
            positions: Default positions in the world frame of the prim. Shape is (N, 3).
            translations: Default translations in the local frame of the prims (with respect to its parent prims).
                Shape is (N, 3).
            orientations: Default quaternion orientations in the world/local frame of the prim (depends if translation
                or position is specified). Quaternion is scalar-first (w, x, y, z). Shape is (N, 4).
            scales: Local scales to be applied to the prim's dimensions. Shape is (N, 3).
            visibilities: Set to false for an invisible prim in the stage while rendering. Shape is (N,).
            particle_masses: Particle masses to be applied to each prim.
            pressures: Pressures to be applied to each prim. If > 0, a particle cloth has an additional pressure
                constraint that provides inflatable (i.e. balloon-like) dynamics. The pressure times the rest volume
                defines the volume the inflatable tries to match. Pressure only works well for closed or approximately
                closed meshes, range: [0, inf), units: dimensionless.
            particle_groups: Group Id of the particles of each prim, range: [0, 2^20).
            self_collisions: Enable self collision of the particles of each prim.
            self_collision_filters: Whether the simulation should filter particle-particle collisions based on the
                rest position distances of each prim. Shape is (N,).
            stretch_stiffnesses: Represents the stretch spring stiffnesses for linear springs placed between particles
                to counteract stretching, shape is (N,). Range: [0, inf), units: force / distance = mass / second /
                second.
            bend_stiffnesses: Represents the spring bend stiffnesses for linear springs placed in a way to counteract
                bending, shape is (N,). Range: [0, inf), units: force / distance = mass / second / second.
            shear_stiffnesses: Represents the shear stiffnesses for linear springs placed in a way to counteract shear,
                shape is (N,). Range: [0, inf), units: force / distance = mass / second / second.
            spring_dampings: Damping on cloth spring constraints. Applies to all constraints parameterized by stiffness
                attributes, range: [0, inf), shape is (N,). Units: force * second / distance = mass / second.
        """
        carb.log_warn(
            "Please note that support for particle cloth and related APIs is now deprecated. These features will be removed in future releases."
        )

        self._physics_view = None
        self._device = None
        self._name = name
        XFormPrim.__init__(
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
        self._cloth_auto_apis = [None] * self._count
        self._cloth_apis = [None] * self._count
        self._particle_apis = [None] * self._count
        self._mass_apis = [None] * self._count

        if particle_masses is not None:
            self.set_particle_masses(particle_masses)
        if pressures is not None:
            self.set_pressures(pressures)
        if particle_groups is not None:
            self.set_particle_groups(particle_groups)
        if self_collision_filters is not None:
            self.set_self_collision_filters(self_collision_filters)
        if self_collisions is not None:
            self.set_self_collisions(self_collisions)
        if stretch_stiffnesses is not None:
            if len(stretch_stiffnesses.tolist()) == self._count:
                self.set_cloths_stretch_stiffnesses(stretch_stiffnesses)
            else:
                self.set_stretch_stiffnesses(stretch_stiffnesses)
        if bend_stiffnesses is not None:
            if len(bend_stiffnesses.tolist()) == self._count:
                self.set_cloths_bend_stiffnesses(bend_stiffnesses)
            else:
                self.set_bend_stiffnesses(bend_stiffnesses)
        if shear_stiffnesses is not None:
            if len(shear_stiffnesses.tolist()) == self._count:
                self.set_cloths_shear_stiffnesses(shear_stiffnesses)
            else:
                self.set_shear_stiffnesses(shear_stiffnesses)
        if spring_dampings is not None:
            if len(spring_dampings.tolist()) == self._count:
                self.set_cloths_dampings(spring_dampings)
            else:
                self.set_spring_dampings(spring_dampings)

        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_STOP,
            on_event=self._invalidate_physics_handle_callback,
            observer_name="isaacsim.core.prims.ClothPrim.initialize._invalidate_physics_handle_callback",
        )

    def __del__(self):
        """Clean up the ClothPrim instance by calling the parent destructor and releasing physics resources."""
        XFormPrim.__del__(self)
        if hasattr(self, "_physics_view"):
            del self._physics_view
        self._invalidate_physics_handle_event = None
        return

    """
    Properties.
    """

    @property
    def count(self) -> int:
        """Number of cloth prims in the view.

        Returns:
            The count of cloth prims.
        """
        return self._count

    @property
    def max_springs_per_cloth(self) -> int:
        """Maximum number of springs per cloth in the view.

        Returns:
            The maximum number of springs per cloth.
        """
        return self._max_springs_per_cloth

    @property
    def max_particles_per_cloth(self) -> int:
        """Maximum number of particles per cloth in the view.

        Returns:
            The maximum number of particles per cloth.
        """
        return self._max_particles_per_cloth

    def is_physics_handle_valid(self) -> bool:
        """Checks whether the physics handle of the view is valid.

        Returns:
            True if the physics handle of the view is valid (i.e physics is initialized for the view). Otherwise False.
        """
        return self._physics_view is not None

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates a rigid body view in physX.

        Args:
            physics_sim_view: Current physics simulation view.
        """

        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        if not carb.settings.get_settings().get_as_bool("/physics/suppressReadback"):
            carb.log_error("Using cloth view requires the gpu pipeline or (a World initialized with a cuda device)")
        self._physics_sim_view = physics_sim_view
        self._physics_view = self._physics_sim_view.create_particle_cloth_view(
            self._regex_prim_paths[0].replace(".*", "*")
        )
        self._count = self._physics_view.count
        self._max_springs_per_cloth = self._physics_view.max_springs_per_cloth
        self._max_particles_per_cloth = self._physics_view.max_particles_per_cloth
        carb.log_info("Cloth Prim View Device: {}".format(self._device))
        return

    def _invalidate_physics_handle_callback(self, event):
        """Callback to invalidate the physics handle when timeline stops.

        Args:
            event: The timeline event that triggered the callback.
        """
        self._physics_view = None
        return

    def _apply_cloth_auto_api(self, index):
        """Apply PhysxAutoParticleClothAPI to the cloth prim at the specified index.

        Args:
            index: Index of the cloth prim to apply the API to.
        """
        if self._cloth_auto_apis[index] is None:
            if self._prims[index].HasAPI(PhysxSchema.PhysxAutoParticleClothAPI):
                cloth_api = PhysxSchema.PhysxAutoParticleClothAPI(self._prims[index])
            else:
                cloth_api = PhysxSchema.PhysxAutoParticleClothAPI.Apply(self._prims[index])
            self._cloth_auto_apis[index] = cloth_api

    def _apply_cloth_api(self, index):
        """Apply PhysxParticleClothAPI to the cloth prim at the specified index.

        Args:
            index: Index of the cloth prim to apply the API to.
        """
        if self._cloth_apis[index] is None:
            if self._prims[index].HasAPI(PhysxSchema.PhysxParticleClothAPI):
                cloth_api = PhysxSchema.PhysxParticleClothAPI(self._prims[index])
            else:
                cloth_api = PhysxSchema.PhysxParticleClothAPI.Apply(self._prims[index])
            self._cloth_apis[index] = cloth_api

    def _apply_particle_api(self, index):
        """Apply PhysxParticleAPI to the cloth prim at the specified index.

        Args:
            index: Index of the cloth prim to apply the API to.
        """
        if self._cloth_apis[index] is None:
            if self._prims[index].HasAPI(PhysxSchema.PhysxParticleAPI):
                particle_api = PhysxSchema.PhysxParticleAPI(self._prims[index])
            else:
                particle_api = PhysxSchema.PhysxParticleAPI.Apply(self._prims[index])
            self._particle_apis[index] = particle_api

    def set_world_positions(
        self,
        positions: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the particle world positions for the cloths indicated by the indices.

        Args:
            positions: particle positions with the shape (M, max_particles_per_cloth, 3).
            indices: indices to specify which cloth prims to manipulate. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            new_positions = self._backend_utils.move_data(positions, self._device)
            current_positions = self.get_world_positions(clone=False)
            current_positions[indices] = new_positions
            self._physics_view.set_positions(current_positions, indices)
        else:
            idx_count = 0
            for i in indices:
                self._apply_cloth_auto_api(i.tolist())
                points = self._prims[i.tolist()].GetAttribute("points").Get()
                if points is None:
                    raise Exception(f"The prim {self.name} does not have points attribute.")
                self._prims[i.tolist()].GetAttribute("points").Set(positions[idx_count].tolist())
                idx_count += 1
        return

    def get_world_positions(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the particle world positions for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            position tensor with shape (M, max_particles_per_cloth, 3)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            positions = self._physics_view.get_positions()
            if not clone:
                return positions[indices].reshape(len(indices), -1, 3)
            else:
                return self._backend_utils.clone_tensor(
                    positions[indices].reshape(len(indices), -1, 3), device=self._device
                )
        else:
            positions = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], self.max_particles_per_cloth, 3], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                self._apply_cloth_auto_api(i.tolist())
                points = self._prims[i.tolist()].GetAttribute("points").Get()
                if points is None:
                    raise Exception(f"The prim {self.name} does not have points attribute.")
                positions[write_idx] = self._backend_utils.create_tensor_from_list(
                    points, dtype="float32", device=self._device
                ).view(self.max_particles_per_cloth, 3)
                write_idx += 1
            return positions

    def set_velocities(
        self,
        velocities: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the particle velocities for the cloths indicated by the indices.

        Args:
            velocities: particle velocities with the shape (M, max_particles_per_cloth, 3).
            indices: indices to specify which cloth prims to manipulate. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            new_velocities = self._backend_utils.move_data(velocities, self._device)
            current_velocities = self.get_velocities(clone=False)
            current_velocities[indices] = new_velocities
            self._physics_view.set_velocities(current_velocities, indices)
        else:
            idx_count = 0
            for i in indices:
                self._apply_cloth_auto_api(i.tolist())
                point_velocities = self._prims[i.tolist()].GetAttribute("velocities").Get()
                if point_velocities is None:
                    raise Exception(f"The prim {self.name} does not have velocities attribute.")
                self._prims[i.tolist()].GetAttribute("velocities").Set(velocities[idx_count].tolist())
                idx_count += 1

    def get_velocities(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the particle velocities for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            velocity tensor with shape (M, max_particles_per_cloth, 3)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            velocities = self._physics_view.get_velocities()
            if not clone:
                return velocities[indices].reshape(len(indices), -1, 3)
            else:
                return self._backend_utils.clone_tensor(
                    velocities[indices].reshape(len(indices), -1, 3), device=self._device
                )
        else:
            velocities = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], self.max_particles_per_cloth, 3], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                self._apply_cloth_auto_api(i.tolist())
                point_velocities = self._prims[i.tolist()].GetAttribute("velocities").Get()
                if point_velocities is None:
                    raise Exception(f"The prim {self.name} does not have velocities attribute.")
                velocities[write_idx] = self._backend_utils.create_tensor_from_list(
                    point_velocities, dtype="float32", device=self._device
                ).view(self.max_particles_per_cloth, 3)
                write_idx += 1
            return velocities

    def set_particle_masses(
        self,
        masses: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the particle masses for the cloths indicated by the indices.

        Args:
            masses: cloth particle masses with the shape (M, max_particles_per_cloth, 3).
            indices: indices to specify which cloth prims to manipulate. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            new_masses = self._backend_utils.move_data(masses, self._device)
            current_masses = self.get_masses(clone=False)
            current_masses[indices] = new_masses
            self._physics_view.set_masses(current_masses, indices)
        else:
            idx_count = 0
            for i in indices:
                if self._mass_apis[i.tolist()] is None:
                    if self._prims[i.tolist()].HasAPI(UsdPhysics.MassAPI):
                        mass_api = UsdPhysics.MassAPI(self._prims[i.tolist()])
                    else:
                        mass_api = UsdPhysics.MassAPI.Apply(self._prims[i.tolist()])
                    self._mass_apis[i.tolist()] = mass_api
                mass_api.GetMassAttr().Set(sum(masses[idx_count].tolist()))
                idx_count += 1

    def get_particle_masses(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the particle masses for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            mass tensor with shape (M, max_particles_per_cloth)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            masses = self._physics_view.get_masses()
            if not clone:
                return masses[indices]
            else:
                return self._backend_utils.clone_tensor(masses[indices], device=self._device)
        else:
            values = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], self.max_particles_per_cloth], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                if "physics:mass" not in self._prims[i.tolist()].GetPropertyNames():
                    carb.log_warn(
                        f"physics:mass is not defined on the cloth prim: {self.name}. Using the default value."
                    )
                    values[write_idx] = (
                        self._mass_apis[i.tolist()].CreateMassAttr().Get() / self.max_particles_per_cloth
                    )
                else:
                    values[write_idx, :] = (
                        self._mass_apis[i.tolist()].GetMassAttr().Get() / self.max_particles_per_cloth
                    )
                write_idx += 1
            return values

    def set_stretch_stiffnesses(
        self,
        stiffness: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the spring stretch stiffness values for springs within the cloths indicated by the indices.

        Args:
            stiffness: cloth spring stiffness with the shape  (M, max_springs_per_cloth).
            indices: indices to specify which cloth prims to manipulate. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            new_stiffnesses = self._backend_utils.move_data(stiffness, self._device)
            current_stiffnesses = self.get_stretch_stiffnesses(clone=False)
            current_stiffnesses[indices] = new_stiffnesses
            self._physics_view.set_spring_stiffness(current_stiffnesses, indices)
        else:
            idx_count = 0
            for i in indices:
                if stiffness[idx_count].any() < 0:
                    carb.log_error("The range of stiffness is [0. inf). Incorrect value for index ", idx_count)
                self._apply_cloth_api(i.tolist())
                if "physxParticle:springStiffnesses" not in self._prims[i.tolist()].GetPropertyNames():
                    self._cloth_apis[i.tolist()].CreateSpringStiffnessesAttr().Set(
                        Vt.FloatArray(stiffness[idx_count].tolist())
                    )
                else:
                    self._cloth_apis[i.tolist()].GetSpringStiffnessesAttr().Set(
                        Vt.FloatArray(stiffness[idx_count].tolist())
                    )
                idx_count += 1

    def get_stretch_stiffnesses(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the spring stretch stiffness for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            stiffness tensor with shape (M, max_springs_per_cloth)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            stiffness = self._physics_view.get_spring_stiffness()
            if not clone:
                return stiffness[indices]
            else:
                return self._backend_utils.clone_tensor(stiffness[indices], device=self._device)
        else:
            stiffnesses = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], self.max_springs_per_cloth], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                self._apply_cloth_api(i.tolist())
                if "physxParticle:springStiffnesses" not in self._prims[i.tolist()].GetPropertyNames():
                    carb.log_warn(
                        f"Stretch stiffness is not defined on the cloth prim: {self.name}. Using the default value."
                    )
                    stiffnesses[write_idx] = self._backend_utils.create_tensor_from_list(
                        self._cloth_apis[i.tolist()].CreateSpringStiffnessesAttr().Get(), dtype="float32"
                    )
                else:
                    stiffnesses[write_idx] = self._backend_utils.create_tensor_from_list(
                        self._cloth_apis[i.tolist()].GetSpringStiffnessesAttr().Get(), dtype="float32"
                    )
                write_idx += 1
            return stiffnesses

    def set_spring_dampings(
        self,
        damping: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the spring damping for the cloths indicated by the indices.

        Args:
            damping: cloth spring damping with the shape (M, max_springs_per_cloth).
            indices: indices to specify which cloth prims to manipulate. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            new_damping = self._backend_utils.move_data(damping, self._device)
            current_damping = self.get_spring_dampings(clone=False)
            current_damping[indices] = new_damping
            self._physics_view.set_spring_damping(current_damping, indices)
        else:
            idx_count = 0
            for i in indices:
                if damping[idx_count].any() < 0:
                    carb.log_error("The range of damping is [0. inf). Incorrect value for index ", idx_count)
                self._apply_cloth_api(i.tolist())
                if "physxParticle:springDampings" not in self._prims[i.tolist()].GetPropertyNames():
                    self._cloth_apis[i.tolist()].CreateSpringDampingsAttr().Set(
                        Vt.FloatArray(damping[idx_count].tolist())
                    )
                else:
                    self._cloth_apis[i.tolist()].GetSpringDampingsAttr().Set(Vt.FloatArray(damping[idx_count].tolist()))
                idx_count += 1

    def get_spring_dampings(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the spring damping for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            damping tensor with shape (M, max_springs_per_cloth)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            damping = self._physics_view.get_spring_damping()
            if not clone:
                return damping[indices]
            else:
                return self._backend_utils.clone_tensor(damping[indices], device=self._device)
        else:
            dampings = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], self.max_springs_per_cloth], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                self._apply_cloth_api(i.tolist())
                if "physxParticle:springDampings" not in self._prims[i.tolist()].GetPropertyNames():
                    carb.log_warn(
                        f"Stretch damping is not defined on the cloth prim: {self.name}. Using the default value"
                    )
                    dampings[write_idx] = self._backend_utils.create_tensor_from_list(
                        self._cloth_apis[i.tolist()].GetSpringDampingsAttr().Get(), dtype="float32"
                    )
                else:
                    dampings[write_idx] = self._backend_utils.create_tensor_from_list(
                        self._cloth_apis[i.tolist()].GetSpringDampingsAttr().Get(), dtype="float32"
                    )
                write_idx += 1
            return dampings

    def set_pressures(
        self,
        pressures: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the pressures of the cloths indicated by the indices.

        Args:
            pressures: Cloths pressure with shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            self._apply_cloth_api(i.tolist())
            if "physxParticle:pressure" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_apis[i.tolist()].CreatePressureAttr().Set(pressures[idx_count].tolist())
            else:
                self._cloth_apis[i.tolist()].GetPressureAttr().Set(pressures[idx_count].tolist())
            idx_count += 1

    def set_self_collision_filters(
        self,
        self_collision_filters: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the self collision filters for the cloths indicated by the indices.

        Args:
            self_collision_filters: Self collision filters with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            self._apply_cloth_api(i.tolist())
            if "physxParticle:selfCollisionFilter" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_apis[i.tolist()].CreateSelfCollisionFilterAttr().Set(
                    self_collision_filters[idx_count].tolist()
                )
            else:
                self._cloth_apis[i.tolist()].GetSelfCollisionFilterAttr().Set(
                    self_collision_filters[idx_count].tolist()
                )
            idx_count += 1

    def set_self_collisions(
        self,
        self_collisions: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the self collision flags for the cloths indicated by the indices.

        Args:
            self_collisions: Self collision flag with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            self._apply_particle_api(i.tolist())
            if "physxParticle:selfCollision" not in self._prims[i.tolist()].GetPropertyNames():
                self._particle_apis[i.tolist()].CreateSelfCollisionAttr().Set(self_collisions[idx_count].tolist())
            else:
                self._particle_apis[i.tolist()].GetSelfCollisionAttr().Set(self_collisions[idx_count].tolist())
            idx_count += 1

    def set_particle_groups(
        self,
        particle_groups: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets the particle group of the cloths indicated by the indices.

        Args:
            particle_groups: Particle group with shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            self._apply_particle_api(i.tolist())
            if "physxParticle:particleGroup" not in self._prims[i.tolist()].GetPropertyNames():
                self._particle_apis[i.tolist()].CreateParticleGroupAttr().Set(particle_groups[idx_count].tolist())
            else:
                self._particle_apis[i.tolist()].GetParticleGroupAttr().Set(particle_groups[idx_count].tolist())
            idx_count += 1

    def set_cloths_dampings(
        self,
        values: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets a single value of damping to all the springs within cloths indicated by the indices.

        Args:
            values: Cloth spring damping with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            if values[idx_count] < 0:
                carb.log_error("The range of damping is [0. inf). Incorrect value for index ", idx_count)
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springDamping" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_auto_apis[i.tolist()].CreateSpringDampingAttr().Set(values[idx_count].tolist())
            else:
                self._cloth_auto_apis[i.tolist()].GetSpringDampingAttr().Set(values[idx_count].tolist())
            idx_count += 1

    def set_cloths_stretch_stiffnesses(
        self,
        values: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets a single value of stretch stiffnesses to all the springs within cloths indicated by the indices.

        Args:
            values: Cloth spring stretch stiffness values with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            if values[idx_count] < 0:
                carb.log_error("The range of stretch stiffness is [0. inf). Incorrect value for index ", idx_count)
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springStretchStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_auto_apis[i.tolist()].CreateSpringStretchStiffnessAttr().Set(values[idx_count].tolist())
            else:
                self._cloth_auto_apis[i.tolist()].GetSpringStretchStiffnessAttr().Set(values[idx_count].tolist())

            idx_count += 1

    def set_cloths_bend_stiffnesses(
        self,
        values: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets a single value of bend stiffnesses to all the springs within cloths indicated by the indices.

        Args:
            values: Cloth spring bend stiffness values with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            if values[idx_count] < 0:
                carb.log_error("The range of bend stiffness is [0. inf). Incorrect value for index ", idx_count)
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springBendStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_auto_apis[i.tolist()].CreateSpringBendStiffnessAttr().Set(values[idx_count].tolist())
            else:
                self._cloth_auto_apis[i.tolist()].GetSpringBendStiffnessAttr().Set(values[idx_count].tolist())

            idx_count += 1

    def set_cloths_shear_stiffnesses(
        self,
        values: np.ndarray | torch.Tensor | None,
        indices: np.ndarray | list | torch.Tensor | None = None,
    ) -> None:
        """Sets a single value of shear stiffnesses to all the springs within cloths indicated by the indices.

        Args:
            values: Cloth spring shear stiffness values with the shape ``(M, )``.
            indices: Indices to specify which cloth prims to manipulate. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
        idx_count = 0
        for i in indices:
            if values[idx_count] < 0:
                carb.log_error("The range of shear stiffness is [0. inf). Incorrect value for index ", idx_count)
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springShearStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                self._cloth_auto_apis[i.tolist()].CreateSpringShearStiffnessAttr().Set(values[idx_count].tolist())
            else:
                self._cloth_auto_apis[i.tolist()].GetSpringShearStiffnessAttr().Set(values[idx_count].tolist())

            idx_count += 1

    def get_cloths_dampings(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the value of damping set for all the springs within cloths indicated by the indices.

        Args:
            indices: Indices to specify which cloth prims to query. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            Damping tensor with shape ``(M, )``.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        values = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springDamping" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(f"damping is not defined on the cloth prim: {self.name}. Using the default value.")
                values[write_idx] = self._cloth_auto_apis[i.tolist()].CreateSpringDampingAttr().Get()
            else:
                values[write_idx] = self._cloth_auto_apis[i.tolist()].GetSpringDampingAttr().Get()
            write_idx += 1
        return values

    def get_cloths_stretch_stiffnesses(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the value of stretch stiffness set to all the springs within cloths indicated by the indices.

        Args:
            indices: Indices to specify which cloth prims to query. Shape ``(M,)``.
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            Stretch stiffness tensor with shape ``(M, )``.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        values = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springStretchStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(
                    f"Stretch stiffness is not defined on the cloth prim: {self.name}. Using the default value."
                )
                values[write_idx] = self._cloth_auto_apis[i.tolist()].CreateSpringStretchStiffnessAttr().Get()
            else:
                values[write_idx] = self._cloth_auto_apis[i.tolist()].GetSpringStretchStiffnessAttr().Get()
            write_idx += 1
        return values

    def get_cloths_bend_stiffnesses(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the value of bend stiffness set to all the springs within cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            bend stiffness tensor with shape (M, )
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        values = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springBendStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(f"bend stiffness is not defined on the cloth prim: {self.name}. Using the default value.")
                values[write_idx] = self._cloth_auto_apis[i.tolist()].CreateSpringBendStiffnessAttr().Get()
            else:
                values[write_idx] = self._cloth_auto_apis[i.tolist()].GetSpringBendStiffnessAttr().Get()
            write_idx += 1
        return values

    def get_cloths_shear_stiffnesses(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the value of shear stiffness set to all the springs within cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            shear stiffness tensor with shape (M, )
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        values = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_cloth_auto_api(i.tolist())
            if "physxAutoParticleCloth:springShearStiffness" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(
                    f"shear stiffness is not defined on the cloth prim: {self.name}. Using the default values."
                )
                values[write_idx] = self._cloth_auto_apis[i.tolist()].CreateSpringShearStiffnessAttr().Get()
            else:
                values[write_idx] = self._cloth_auto_apis[i.tolist()].GetSpringShearStiffnessAttr().Get()
            write_idx += 1
        return values

    def get_self_collision_filters(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the self collision filters for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            the self collision filters tensor with shape (M, )
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        self_collision_filters = self._backend_utils.create_zeros_tensor(
            [indices.shape[0]], dtype="bool", device=self._device
        )
        write_idx = 0
        for i in indices:
            self._apply_cloth_api(i.tolist())
            if "physxParticle:selfCollisionFilter" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(
                    f"selfCollisionFilter is not defined on the cloth prim: {self.name}. Using the default values."
                )
                self_collision_filters[write_idx] = self._cloth_apis[i.tolist()].CreateSelfCollisionFilterAttr().Get()
            else:
                self_collision_filters[write_idx] = self._cloth_apis[i.tolist()].GetSelfCollisionFilterAttr().Get()
            write_idx += 1
        return self_collision_filters

    def get_self_collisions(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the self collision for the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            the self collision tensor with shape (M, )
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        self_collisions = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="bool", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_particle_api(i.tolist())
            if "physxParticle:selfCollision" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(f"selfCollision is not defined on the cloth prim: {self.name}. Using the default values.")
                self_collisions[write_idx] = self._particle_apis[i.tolist()].CreateSelfCollisionAttr().Get()
            else:
                self_collisions[write_idx] = self._particle_apis[i.tolist()].GetSelfCollisionAttr().Get()
            write_idx += 1
        return self_collisions

    def get_pressures(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the pressures of the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            cloths pressure with shape (M, ).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        pressures = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            self._apply_cloth_api(i.tolist())
            if "physxParticle:pressure" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(f"pressure is not defined on the cloth prim: {self.name}. Using the default value.")
                pressures[write_idx] = self._cloth_apis[i.tolist()].CreatePressureAttr().Get()
            else:
                pressures[write_idx] = self._cloth_apis[i.tolist()].GetPressureAttr().Get()
            write_idx += 1
        return pressures

    def get_particle_groups(
        self, indices: np.ndarray | list | torch.Tensor | None = None, clone: bool = True
    ) -> np.ndarray | torch.Tensor:
        """Gets the particle groups of the cloths indicated by the indices.

        Args:
            indices: indices to specify which cloth prims to query. Shape (M,).
                Where M <= size of the encapsulated prims in the view.
                Defaults to None (i.e: all prims in the view).
            clone: True to return a clone of the internal buffer. Otherwise False.

        Returns:
            particle groups with shape (M, ).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        particle_groups = self._backend_utils.create_zeros_tensor(
            [indices.shape[0]], dtype="int32", device=self._device
        )
        write_idx = 0
        for i in indices:
            self._apply_particle_api(i.tolist())
            if "physxParticle:particleGroup" not in self._prims[i.tolist()].GetPropertyNames():
                carb.log_warn(f"particleGroup is not defined on the cloth prim: {self.name}. Using the default value.")
                particle_groups[write_idx] = self._particle_apis[i.tolist()].GetParticleGroupAttr().Get()
            else:
                particle_groups[write_idx] = self._particle_apis[i.tolist()].GetParticleGroupAttr().Get()
            write_idx += 1
        return particle_groups
