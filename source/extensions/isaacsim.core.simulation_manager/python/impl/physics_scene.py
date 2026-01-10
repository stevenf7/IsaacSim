# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from __future__ import annotations

from abc import ABC, abstractmethod

import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from pxr import Gf, Usd, UsdGeom, UsdPhysics

from .. import _simulation_manager


class PhysicsScene(ABC):
    """Base class for manipulating a USD Physics Scene prim and its attributes.

    This abstract class provides engine-agnostic functionality for working with USD Physics Scene
    prims. Engine-specific implementations should inherit from this class and implement the
    abstract methods.

    Args:
        prim: USD Physics Scene prim path or prim instance.
            If the input is a path, a new USD Physics Scene prim is created if it does not exist.

    Raises:
        ValueError: If the input prim exists and is not a USD Physics Scene prim.
    """

    def __init__(self, prim: str | Usd.Prim):
        physics_scene = _simulation_manager.PhysicsScene(prim_utils.get_prim_path(prim))
        self._path = physics_scene.path
        self._prim = prim_utils.get_prim_at_path(prim)

    @property
    def path(self) -> str:
        """USD Physics Scene prim path.

        Returns:
            Prim path encapsulated by the wrapper.

        Example:

        .. code-block:: python

            >>> physics_scene.path
            '/World/physicsScene'
        """
        return self._path

    @property
    def prim(self) -> Usd.Prim:
        """USD Physics Scene prim instance.

        Returns:
            Prim instance encapsulated by the wrapper.

        Example:

        .. code-block:: python

            >>> physics_scene.prim
            Usd.Prim(</World/physicsScene>)
        """
        return self._prim

    @property
    def physics_scene(self) -> UsdPhysics.Scene:
        """USD Physics Scene instance.

        Returns:
            Physics Scene instance encapsulated by the wrapper.

        Example:

        .. code-block:: python

            >>> physics_scene.physics_scene
            UsdPhysics.Scene(Usd.Prim(</World/physicsScene>))
        """
        return UsdPhysics.Scene(self._prim)

    @staticmethod
    def get_physics_scene_paths(stage: Usd.Stage | None = None) -> list[str]:
        """Get the paths of all USD Physics Scene prims in the stage.

        Args:
            stage: USD stage to search for Physics Scene prims. If None, the current stage is used.

        Returns:
            List of USD Physics Scene prim paths.

        Example:

        .. code-block:: python

            >>> from isaacsim.core.simulation_manager import PhysicsScene
            >>>
            >>> PhysicsScene.get_physics_scene_paths()
            ['/World/physicsScene']
        """
        if stage is not None:
            return _simulation_manager.get_physics_scene_paths(stage_utils.get_stage_id(stage))
        return _simulation_manager.get_physics_scene_paths(None)

    def get_gravity(self) -> Gf.Vec3f:
        """Get the Physics Scene's gravity vector.

        Returns:
            Gravity vector in world units per second squared.

        Example:

        .. code-block:: python

            >>> physics_scene.get_gravity()
            Gf.Vec3f(0.0, 0.0, -9.81)
        """
        stage = self._prim.GetStage()
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        magnitude = self.physics_scene.GetGravityMagnitudeAttr().Get()
        direction = self.physics_scene.GetGravityDirectionAttr().Get()
        return Gf.Vec3f(direction) * magnitude / meters_per_unit

    def set_gravity(self, gravity: Gf.Vec3f | tuple[float, float, float] | list[float]) -> None:
        """Set the Physics Scene's gravity vector.

        Args:
            gravity: Gravity vector in world units per second squared.

        Example:

        .. code-block:: python

            >>> physics_scene.set_gravity(Gf.Vec3f(0.0, 0.0, -9.81))
        """
        if not isinstance(gravity, Gf.Vec3f):
            gravity = Gf.Vec3f(*gravity)
        stage = self._prim.GetStage()
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        magnitude = gravity.GetLength() * meters_per_unit
        direction = gravity.GetNormalized() if magnitude > 0 else Gf.Vec3f(0, 0, -1)
        self.physics_scene.GetGravityMagnitudeAttr().Set(magnitude)
        self.physics_scene.GetGravityDirectionAttr().Set(direction)

    @abstractmethod
    def get_dt(self) -> float:
        """Get the Physics Scene's delta time (DT).

        Returns:
            Physics Scene's delta time (DT).
        """
        pass

    @abstractmethod
    def set_dt(self, dt: float) -> None:
        """Set the Physics Scene's delta time (DT).

        Args:
            dt: Physics Scene's delta time (DT).
        """
        pass
