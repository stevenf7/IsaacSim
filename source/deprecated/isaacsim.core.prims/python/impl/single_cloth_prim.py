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

"""Implementation of single cloth primitive for physics simulation in Isaac Sim."""


from typing import List, Optional, Sequence, Union

import carb
import numpy as np
from isaacsim.core.deprecation_manager import import_module
from isaacsim.core.utils.stage import get_current_stage
from isaacsim.core.utils.types import DynamicState
from omni.physx.scripts import particleUtils, physicsUtils
from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics, UsdShade

from .cloth_prim import ClothPrim
from .single_particle_system import SingleParticleSystem
from .single_prim_wrapper import _SinglePrimWrapper

torch = import_module("torch")


class SingleClothPrim(_SinglePrimWrapper):

    def __init__(
        self,
        prim_path: str,
        particle_system: SingleParticleSystem,
        particle_material: Optional["ParticleMaterial"] = None,
        name: Optional[str] = "cloth",
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: Optional[bool] = None,
        particle_mass: Optional[float] = 0.01,
        pressure: Optional[float] = None,
        particle_group: Optional[int] = 0,
        self_collision: Optional[bool] = True,
        self_collision_filter: Optional[bool] = True,
        stretch_stiffness: Optional[float] = None,
        bend_stiffness: Optional[float] = None,
        shear_stiffness: Optional[float] = None,
        spring_damping: Optional[float] = None,
    ):
        """Creates a cloth at prim_path given a particle_system and the cloth parameters.

        Args:
            prim_path (str): the absolute path that the prim is supposed to be registered in.
            particle_system (SingleParticleSystem): the particle system that this cloth is using.
            particle_material (ParticleMaterial): the particle material that is cloth is using.
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (Sequence[float], optional): the position of the center of the cloth.
            orientation (Sequence[float], optional): the initial orientation of the cloth, assuming cloth is flat.
            scale (Sequence[float], optional): the scale of the cloth.
            visible (bool, optional): True if the cloth is supposed to be visible, False otherwise.
            particle_mass (float, optional): the mass of one single particle.
            pressure (float, optional): if > 0, a particle cloth has an additional pressure constraint that provides
                inflatable (i.e. balloon-like) dynamics. The pressure times the rest volume defines the volume the
                inflatable tries to match. Pressure only works well for closed or approximately closed meshes,
                range: [0, inf), units: dimensionless
            particle_group (int, optional): group Id of the particles, range: [0, 2^20)
            self_collision (bool, optional): enable self collision of the particles or of the particle object.
            self_collision_filter (bool, optional): whether the simulation should filter particle-particle collisions
                based on the rest position distances.
            stretch_stiffness (Sequence[float], optional): represents a stiffness for linear springs placed between
                particles to counteract stretching, range: [0, inf), units: force / distance = mass / second / second
            bend_stiffness (Sequence[float], optional): represents a stiffness for linear springs placed in a way to
                counteract bending, range: [0, inf), units: force / distance = mass / second / second
            shear_stiffness (Sequence[float], optional): represents a stiffness for linear springs placed in a way to
                counteract shear, range: [0, inf), units: force / distance = mass / second / second
            spring_damping (Sequence[float], optional): damping on cloth spring constraints. Applies to all constraints
                parameterized by stiffness attributes, range: [0, inf),
                units: force * second / distance = mass / second

        Note:
            Particles / objects in different groups in the same system collide with each other. Within the same group in
            the same system, the collision behavior is controlled by the self_collision parameter.
        """
        self._stage = get_current_stage()
        self._prim = self._stage.GetPrimAtPath(prim_path)
        self._mesh = UsdGeom.Mesh.Get(self._stage, prim_path)

        from isaacsim.core.simulation_manager import SimulationManager

        self._backend = SimulationManager.get_backend()
        self._device = SimulationManager.get_physics_sim_device()
        self._backend_utils = SimulationManager._get_backend_utils()

        # add particle material
        if particle_material is not None:
            particle_system.apply_particle_material(particle_material)

        # configure as cloth
        particleUtils.add_physx_particle_cloth(
            self._stage,
            path=prim_path,
            dynamic_mesh_path=None,
            particle_system_path=particle_system.prim_path,
            spring_stretch_stiffness=stretch_stiffness,
            spring_bend_stiffness=bend_stiffness,
            spring_shear_stiffness=shear_stiffness,
            spring_damping=spring_damping,
            self_collision=self_collision,
            self_collision_filter=self_collision_filter,
            particle_group=particle_group,
            pressure=pressure,
        )

        # prepare inputs for view construction
        if pressure is not None:
            pressure = self._backend_utils.create_tensor_from_list([pressure], dtype="float32", device=self._device)
        if particle_group is not None:
            particle_group = self._backend_utils.create_tensor_from_list(
                [particle_group], dtype="int32", device=self._device
            )
        if self_collision is not None:
            self_collision = self._backend_utils.create_tensor_from_list(
                [self_collision], dtype="bool", device=self._device
            )
        if self_collision_filter is not None:
            self_collision_filter = self._backend_utils.create_tensor_from_list(
                [self_collision_filter], dtype="bool", device=self._device
            )
        if stretch_stiffness is not None:
            stretch_stiffness = self._backend_utils.create_tensor_from_list(
                [stretch_stiffness], dtype="float32", device=self._device
            )
        if bend_stiffness is not None:
            bend_stiffness = self._backend_utils.create_tensor_from_list(
                [bend_stiffness], dtype="float32", device=self._device
            )
        if shear_stiffness is not None:
            shear_stiffness = self._backend_utils.create_tensor_from_list(
                [shear_stiffness], dtype="float32", device=self._device
            )
        if spring_damping is not None:
            spring_damping = self._backend_utils.create_tensor_from_list(
                [spring_damping], dtype="float32", device=self._device
            )
        if particle_mass is not None:
            count = len(self._prim.GetAttribute("points").Get())
            particle_mass = self._backend_utils.create_tensor_from_list(
                [particle_mass] * count, dtype="float32", device=self._device
            )
            particle_mass = self._backend_utils.expand_dims(particle_mass, 0)
        if position is not None:
            position = self._backend_utils.convert(position, self._device)
            position = self._backend_utils.expand_dims(position, 0)
        if orientation is not None:
            orientation = self._backend_utils.convert(orientation, self._device)
            orientation = self._backend_utils.expand_dims(orientation, 0)
        if scale is not None:
            scale = self._backend_utils.convert(scale, self._device)
            scale = self._backend_utils.expand_dims(scale, 0)
        if visible is not None:
            visible = self._backend_utils.create_tensor_from_list([visible], dtype="bool", device=self._device)

        self._cloth_prim_view = ClothPrim(
            prim_paths_expr=prim_path,
            particle_systems=particle_system,
            name=name,
            positions=position,
            orientations=orientation,
            scales=scale,
            visibilities=visible,
            particle_masses=particle_mass,
            pressures=pressure,
            particle_groups=particle_group,
            self_collisions=self_collision,
            self_collision_filters=self_collision_filter,
            stretch_stiffnesses=stretch_stiffness,
            bend_stiffnesses=bend_stiffness,
            shear_stiffnesses=shear_stiffness,
            spring_dampings=spring_damping,
        )
        _SinglePrimWrapper.__init__(self, view=self._cloth_prim_view)

    """
    Properties.
    """

    @property
    def mesh(self) -> UsdGeom.Mesh:
        """USD Geometry Mesh object that this cloth prim tracks.

        Returns:
            USD Geometry Mesh object that this object tracks.
        """
        return self._mesh

    """
    Operations- State.
    """

    def get_current_dynamic_state(self) -> DynamicState:
        """Return the DynamicState that contains the position and orientation of the cloth prim.

        Returns:
            DynamicState containing position (np.ndarray, optional) - position in the world frame of the prim.
                shape is (3, ). Defaults to None, which means left unchanged; and
            orientation (np.ndarray, optional) - quaternion orientation in the world frame of the prim.
                quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None, which means left unchanged.
        """
        position, orientation = self.get_world_pose()
        return DynamicState(position=position, orientation=orientation)

    def _get_points_pose(self):
        """Return the position of the points of the cloth prim with respect to the center of the cloth prim.

        Returns:
            Position of the points that the cloth is composed of.
        """
        points = self._prim.GetAttribute("points").Get()
        if points is None:
            raise Exception(f"The prim {self.name} does not have points attribute.")
        return self._backend_utils.create_tensor_from_list(
            self._prim.GetAttribute("points").Get(), dtype="float32", device=self._device
        )

    """
    Operations- Setters.
    """

    def set_stretch_stiffness(self, stiffness: Union[np.ndarray, torch.Tensor]):
        """Sets stretch stiffness values of spring constraints in the cloth.
            It represents a stiffness for linear springs placed between particles to counteract stretching.

        Args:
            stiffness: The stretch stiffnesses.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        stiffness = self._backend_utils.convert(stiffness, self._device)
        stiffness = self._backend_utils.expand_dims(stiffness, 0)
        self._cloth_prim_view.set_stretch_stiffnesses(stiffness)

    def set_spring_damping(self, damping: Union[np.ndarray, torch.Tensor]):
        """Sets damping values of spring constraints in the cloth.

        Args:
            damping: The damping values of springs.
                Range: [0 , inf), Units: force/distance = mass/second
        """
        damping = self._backend_utils.convert(damping, self._device)
        damping = self._backend_utils.expand_dims(damping, 0)
        self._cloth_prim_view.set_spring_dampings(damping)

    def set_cloth_stretch_stiffness(self, stiffness: Union[np.ndarray, torch.Tensor]):
        """Sets a single stretch stiffness value to all springs constraints in the cloth.

        Args:
            stiffness: The cloth springs stretch stiffness value.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        self._cloth_prim_view.set_cloths_stretch_stiffnesses(
            self._backend_utils.create_tensor_from_list([stiffness], dtype="float32")
        )

    def set_cloth_bend_stiffness(self, stiffness: float):
        """Sets a single bend stiffness value to all springs constraints in the cloth.

        Args:
            stiffness: The cloth springs bend stiffness value.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        self._cloth_prim_view.set_cloths_bend_stiffnesses(
            self._backend_utils.create_tensor_from_list([stiffness], dtype="float32")
        )

    def set_cloth_shear_stiffness(self, stiffness: float):
        """Sets a single shear stiffness value to all springs constraints in the cloth.

        Args:
            stiffness: The cloth springs shear stiffness value.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        self._cloth_prim_view.set_cloths_shear_stiffnesses(
            self._backend_utils.create_tensor_from_list([stiffness], dtype="float32")
        )

    def set_cloth_damping(self, damping: float):
        """Sets a single damping value to all springs constraints in the cloth.

        Args:
            damping: The cloth springs damping value.
                Range: [0 , inf), Units: force/velocity = mass/second
        """
        self._cloth_prim_view.set_cloths_dampings(
            self._backend_utils.create_tensor_from_list([damping], dtype="float32")
        )

    def set_pressure(self, pressure: float):
        """Sets the pressure value of the cloth.

        Args:
            pressure: Pressure value.
        """
        self._cloth_prim_view.set_pressures(self._backend_utils.create_tensor_from_list([pressure], dtype="float32"))

    def set_self_collision_filter(self, self_collision_filter: bool):
        """Sets whether the simulation should filter particle-particle collisions based on rest position distances.

        Args:
            self_collision_filter: Whether to enable self collision filtering.
        """
        self._cloth_prim_view.set_self_collision_filters(
            self._backend_utils.create_tensor_from_list([self_collision_filter], dtype="bool")
        )

    def set_self_collision(self, self_collision: bool):
        """Sets whether self collision is enabled for the particles.

        Args:
            self_collision: Whether to enable self collision.
        """
        self._cloth_prim_view.set_self_collisions(
            self._backend_utils.create_tensor_from_list([self_collision], dtype="bool")
        )

    def set_particle_group(self, particle_group: int):
        """Sets the particle group ID for the cloth.

        Args:
            particle_group: Group ID of the particles.
        """
        self._cloth_prim_view.set_particle_groups(
            self._backend_utils.create_tensor_from_list([particle_group], dtype="int32")
        )

    """
    Operations- Getters.
    """

    def get_stretch_stiffness(self) -> Union[np.ndarray, torch.Tensor]:
        """Stretch stiffness values of spring constraints.

        Returns:
            The stretch stiffness values.
        """
        return self._cloth_prim_view.get_stretch_stiffnesses()[0]

    def get_spring_damping(self) -> Union[np.ndarray, torch.Tensor]:
        """Damping values of spring constraints.

        Returns:
            The spring damping values.
        """
        return self._cloth_prim_view.get_spring_dampings()[0]

    def get_cloth_stretch_stiffness(self) -> float:
        """Reports a single value that would be used to generate the stiffnesses. This API does not report the actually created stiffnesses.

        Returns:
            The stretch stiffness.
        """
        return self._cloth_prim_view.get_cloths_stretch_stiffnesses()[0]

    def get_cloth_bend_stiffness(self) -> float:
        """Reports a single value that would be used to generate the stiffnesses. This API does not report the actually created stiffnesses.

        Returns:
            The bend stiffness.
        """
        return self._cloth_prim_view.get_cloths_bend_stiffnesses()[0]

    def get_cloth_shear_stiffness(self) -> float:
        """Reports a single value that would be used to generate the stiffnesses. This API does not report the actually created stiffnesses.

        Returns:
            The shear stiffness.
        """
        return self._cloth_prim_view.get_cloths_shear_stiffnesses()[0]

    def get_cloth_damping(self) -> Union[np.ndarray, torch.Tensor]:
        """Reports a single value that would be used to generate the dampings. This API does not report the actually created dampings.

        Returns:
            The spring damping.
        """
        return self._cloth_prim_view.get_cloths_dampings()[0]

    def get_pressure(self) -> float:
        """Pressure value of the cloth.

        Returns:
            The pressure value.
        """
        return self._cloth_prim_view.get_pressures()[0]

    def get_self_collision_filter(self) -> bool:
        """Self collision filter state of the cloth.

        Returns:
            Whether the simulation should filter particle-particle collisions based on the rest position distances.
        """
        return self._cloth_prim_view.get_self_collision_filters()[0]

    def get_self_collision(self) -> bool:
        """Self collision state of the cloth.

        Returns:
            Whether self collision of the particles or particle object is enabled.
        """
        return self._cloth_prim_view.get_self_collisions()[0]

    def get_particle_group(self) -> int:
        """Particle group ID of the cloth.

        Returns:
            The group ID of the particles.
        """
        return self._cloth_prim_view.get_particle_groups()[0]
