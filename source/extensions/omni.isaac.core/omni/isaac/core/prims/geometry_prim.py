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
from omni.isaac.core.prims.prim import Prim
from omni.isaac.core.utils.types import GeometryPrimState
from pxr import Gf, UsdGeom, Usd


class GeometryPrim(Prim):
    def __init__(
        self,
        prim: Usd.Prim,
        geom: UsdGeom.Gprim,
        name: str = None,
        position: Optional(np.ndarray) = None,
        orientation: Optional(np.ndarray) = None,
        visibility: bool = True,
        color: Optional(np.ndarray) = None,
    ) -> None:
        """Provides common functionalities to geometry prims such as cube, sphere..etc.

        Args:
            prim (Usd.Prim): USD prim object to encapsulate.
            geom (UsdGeom.Gprim): USD geometry object to encapsulate. You can retrive it using UsdGeom.Gprim(prim).
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
            orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
            color (np.ndarray, optional): color to be applied to the geometric prim (R, G, B) 0-255. shape (3,). Defaults to None.
            visibility (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
        """
        super().__init__(prim, name=name, position=position, orientation=orientation, visibility=visibility)
        self._geom = geom
        if color is not None:
            self.set_usd_color(color)
        default_color = self.get_usd_color()
        self._default_state = GeometryPrimState(
            position=self._default_state.position, orientation=self._default_state.orientation, color=default_color
        )
        return

    @property
    def geom(self) -> UsdGeom.Gprim:
        """
        Returns:
            UsdGeom.Gprim: USD geometry object encapsulated.
        """
        return self._geom

    def set_usd_color(self, color: np.ndarray) -> None:
        """Sets the color of the USD geom.
        Args:
            color (np.ndarray): color to be applied to the geometric prim (R, G, B) 0-255. shape (3,).
        """
        color = color.tolist()
        color = Gf.Vec3f(color)
        self._geom.CreateDisplayColorAttr().Set([color])
        return

    def get_usd_color(self) -> np.ndarray:
        """
        Returns:
            np.ndarray: color of the geometric prim (R, G, B) 0-255.
        """
        return np.array(self._geom.GetDisplayColorAttr().Get())

    def set_default_state(self, position: np.ndarray, orientation: np.ndarray, color: np.ndarray) -> None:
        """Sets the default state of the prim that will be used with each reset. 

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
            orientation (np.ndarray): orientation represented as a quaternion. 
                                      quaternion is scalar-first (w, x, y, z). shape (4,).
            color (np.ndarray): olor to be applied to the geometric prim (R, G, B) 0-255. shape (3,).
        """
        self._default_state = GeometryPrimState(position=position, orientation=orientation, color=color)
        return

    def reset(self) -> None:
        """Resets the prim to its default state (position and orientation).
        """
        super().reset()
        # TODO: reset the color to its default state
        # self.set_color(self._default_state.color)
        return
