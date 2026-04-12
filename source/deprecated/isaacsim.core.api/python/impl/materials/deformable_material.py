# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


"""A module for creating and managing deformable materials used in soft body physics simulations."""

from __future__ import annotations

import carb

# isaac-core
import isaacsim.core.utils.stage as stage_utils

# omniverse
from isaacsim.core.api.materials.deformable_material_view import DeformableMaterialView
from isaacsim.core.api.simulation_context.simulation_context import SimulationContext
from pxr import Usd, UsdShade


class DeformableMaterial:
    """A wrapper around deformable material used to simulate soft bodies.

    Applies the PhysxSchema.PhysxDeformableSurfaceMaterialAPI to the prim at path.

    Note:
        If a prim does not exist at specified path, then a new UsdShade.Material prim is created.

    Args:
        prim_path: The prim path to create/apply deformable material properties.
        name: Name given to the prim when instantiating it.
        dynamic_friction: The dynamic friction coefficient in range [0, inf).
        youngs_modulus: The Young's modulus coefficient controlling stiffness of the bodies in range [0, inf).
        poissons_ratio: The Poisson's ratio coefficient that is related to volume preservation in range [0, 0.5).
        elasticity_damping: Material damping parameter in [0, inf).
        damping_scale: The damping scale coefficient in [0, 1].

    """

    def __init__(
        self,
        prim_path: str,
        name: str | None = "deformable_material",
        dynamic_friction: float | None = None,
        youngs_modulus: float | None = None,
        poissons_ratio: float | None = None,
        elasticity_damping: float | None = None,
        damping_scale: float | None = None,
    ) -> None:
        stage = stage_utils.get_current_stage()
        self._name = name
        self._prim_path = prim_path
        self._prim = stage.GetPrimAtPath(prim_path)

        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._device = SimulationContext.instance().device
            self._backend_utils = SimulationContext.instance().backend_utils
        else:
            import isaacsim.core.utils.numpy as np_utils  # noqa: F401

        if stage.GetPrimAtPath(prim_path).IsValid():
            if not self._prim.IsA(UsdShade.Material):
                raise ValueError(f"A prim at path '{prim_path}' exists but is not a Usd.Material prim.")
            else:
                carb.log_warn(f"A material prim already defined at path: {prim_path}.")
                self._material = UsdShade.Material(stage.GetPrimAtPath(prim_path))
        else:
            self._material = UsdShade.Material.Define(stage, prim_path)

        # set properties
        if dynamic_friction is not None:
            dynamic_friction = self._backend_utils.create_tensor_from_list(
                [dynamic_friction], dtype="float32", device=self._device
            )
        if youngs_modulus is not None:
            youngs_modulus = self._backend_utils.create_tensor_from_list(
                [youngs_modulus], dtype="float32", device=self._device
            )
        if poissons_ratio is not None:
            poissons_ratio = self._backend_utils.create_tensor_from_list(
                [poissons_ratio], dtype="float32", device=self._device
            )
        if damping_scale is not None:
            damping_scale = self._backend_utils.create_tensor_from_list(
                [damping_scale], dtype="float32", device=self._device
            )
        if elasticity_damping is not None:
            elasticity_damping = self._backend_utils.create_tensor_from_list(
                [elasticity_damping], dtype="float32", device=self._device
            )

        self._deformable_material_view = DeformableMaterialView(
            prim_paths_expr=prim_path,
            name=name,
            dynamic_frictions=dynamic_friction,
            youngs_moduli=youngs_modulus,
            poissons_ratios=poissons_ratio,
            damping_scales=damping_scale,
            elasticity_dampings=elasticity_damping,
        )

    """
    Properties.
    """

    @property
    def prim_path(self) -> str:
        """Stage path to the material.

        Returns:
            The stage path to the material.

        """
        return self._prim_path

    @property
    def prim(self) -> Usd.Prim:
        """USD prim present.

        Returns:
            The USD prim present.

        """
        return self._prim

    @property
    def material(self) -> UsdShade.Material:
        """USD Material object.

        Returns:
            The USD Material object.

        """
        return self._material

    @property
    def name(self) -> str | None:
        """Name given to the prim when instantiating it.

        Returns:
            Name given to the prim when instantiating it. Otherwise None.

        """
        return self._name

    def initialize(self, physics_sim_view: object = None) -> None:
        """Initializes the deformable material view.

        Args:
            physics_sim_view: Physics simulation view to initialize with.

        """
        self._deformable_material_view.initialize(physics_sim_view=physics_sim_view)
        return

    def is_valid(self) -> bool:
        """Validates the deformable material prim.

        Returns:
            True if the current prim path corresponds to a valid prim in stage. False otherwise.

        """
        return self._deformable_material_view.is_valid()

    def post_reset(self) -> None:
        """Resets the prim to its default state."""
        self._deformable_material_view.post_reset()
        return

    """
    Operations - Setters.
    """

    def set_dynamic_friction(self, value: float) -> None:
        """Sets the dynamic_friction coefficient.

        The dynamic_friction takes effect in all interactions between particles and rigids or deformables.
        For solid particle-particle interactions it is multiplied by the particle dynamic_friction scale.

        Args:
            value: The dynamic_friction coefficient. Range: [0, inf), Units: dimensionless

        """
        if value < 0:
            carb.log_error("The valid range of dynamic_friction coefficient is [0. inf).")
        self._deformable_material_view.set_dynamic_frictions(
            self._backend_utils.create_tensor_from_list([value], dtype="float32")
        )

    def set_youngs_modululs(self, value: float) -> None:
        """Sets the youngs_modululs for fluid particles.

        Args:
            value: The youngs_modululs. Range: [0, inf)

        """
        if value < 0:
            carb.log_error("The valid range of youngs_modululs is [0. inf).")
        self._deformable_material_view.set_youngs_moduli(
            self._backend_utils.create_tensor_from_list([value], dtype="float32")
        )

    def set_poissons_ratio(self, value: float) -> None:
        """Sets the poissons ratio coefficient.

        Args:
            value: The poissons ratio. Range: (0 , 0.5)

        """
        self._deformable_material_view.set_poissons_ratios(
            self._backend_utils.create_tensor_from_list([value], dtype="float32")
        )

    def set_damping_scale(self, value: float) -> None:
        """Sets the damping scale coefficient.

        Args:
            value: The damping scale coefficient Range: [0, inf)

        """
        if value < 0:
            carb.log_error("The valid range of damping_scale coefficient is [0. inf).")
        self._deformable_material_view.set_damping_scales(
            self._backend_utils.create_tensor_from_list([value], dtype="float32")
        )

    def set_elasticity_damping(self, value: float) -> None:
        """Sets the global velocity elasticity damping coefficient.

        Args:
            value: The elasticity damping coefficient.
                Range: [0, inf), Units: dimensionless

        """
        if value < 0:
            carb.log_error("The valid range of elasticity damping coefficient is [0. inf).")
        self._deformable_material_view.set_elasticity_dampings(
            self._backend_utils.create_tensor_from_list([value], dtype="float32")
        )

    """
    Operations - Getters.
    """

    def get_dynamic_friction(self) -> float:
        """Dynamic friction coefficient.

        Returns:
            The dynamic friction coefficient.

        """
        return self._deformable_material_view.get_dynamic_frictions()[0]

    def get_youngs_modululs(self) -> float:
        """Youngs modulus coefficient.

        Returns:
            The youngs modulus coefficient.

        """
        return self._deformable_material_view.get_youngs_moduli()[0]

    def get_poissons_ratio(self) -> float:
        """Poissons ratio coefficient.

        Returns:
            The poissons ratio.

        """
        return self._deformable_material_view.get_poissons_ratios()[0]

    def get_damping_scale(self) -> float:
        """Damping scale coefficient.

        Returns:
            The damping scale coefficient.

        """
        return self._deformable_material_view.get_damping_scales()[0]

    def get_elasticity_damping(self) -> float:
        """Elasticity damping coefficient.

        Returns:
            The elasticity damping coefficient.

        """
        return self._deformable_material_view.get_elasticity_dampings()[0]
