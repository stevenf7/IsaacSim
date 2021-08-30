# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Optional
import numpy as np
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.types import CollisionPrimState
from pxr import UsdPhysics, Usd, UsdGeom
from omni.isaac.core.utils.collisions import add_physics_material


class CollisionPrim(XFormPrim):
    def __init__(
        self,
        stage: Usd.Stage,
        prim: UsdGeom.Gprim,
        name: Optional(str) = None,
        position: Optional(np.ndarray) = None,
        orientation: Optional(np.ndarray) = None,
        visibility: bool = True,
        density: float = 10.0,
        static_friction: float = 0.5,
        dynamic_friction: float = 0.5,
        restitution: float = 0.8,
    ) -> None:
        """Provides common functionalities to prims that has collisions enabled on them.

        Args:
            stage (Usd.Stage): current usd stage used.
            prim (Usd.Prim): prim object to encapsulate.
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
            orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
            density (float, optional): density to be applied in kg. Defaults to 1.0.
            static_friction (float, optional): static friction to be applied on the physics material. Defaults to 0.0.
            dynamic_friction (float, optional): dynamic friction to be applied on the physics material. Defaults to 0.0.
            restitution (float, optional): restitution to be applied on the physics material. Defaults to 0.8.
            visibility (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
        """
        super().__init__(prim, name=name, position=position, orientation=orientation, visibility=visibility)
        # TODO: make sure the default physics material values makes sense and revisit the args explanation
        UsdPhysics.CollisionAPI.Apply(prim)
        self._material_prim = add_physics_material(
            stage,
            prim,
            density=density,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
        )
        self._default_state = CollisionPrimState(
            position=self._default_state.position,
            orientation=self._default_state.orientation,
            density=density,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
        )

    def set_default_state(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
        density: float,
        static_friction: float,
        dynamic_friction: float,
        restitution: float,
    ) -> None:
        """Sets the default state of the prim that will be used with each reset. 

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
            orientation (np.ndarray): orientation represented as a quaternion. 
                                      quaternion is scalar-first (w, x, y, z). shape (4,).
            density (float): density to be applied in kg. Defaults to 1.0.
            static_friction (float): static friction to be applied on the physics material. Defaults to 0.0.
            dynamic_friction (float): dynamic friction to be applied on the physics material. Defaults to 0.0.
            restitution (float): restitution to be applied on the physics material. Defaults to 0.8.
        """
        self._default_state = CollisionPrimState(
            position=position,
            orientation=orientation,
            density=density,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
        )
        return

    def reset(self) -> None:
        """Resets the prim to its default state (position and orientation).
        """
        super().reset()
        # TODO: set the collission properties in case it was changed during the episode?
        return

    def set_usd_sliding_friction(self, sliding_friction: float) -> None:
        raise NotImplementedError

    def get_usd_sliding_friction(self) -> float:
        raise NotImplementedError

    def set_usd_spinning_friction(self, spinning_friction: float) -> None:
        raise NotImplementedError

    def get_usd_spinning_friction(self) -> float:
        raise NotImplementedError

    def set_usd_restitution(self, restitution: float) -> None:
        raise NotImplementedError

    def get_usd_restitution(self) -> float:
        raise NotImplementedError
