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
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.prims.collision_prim import CollisionPrim
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.utils.types import DynamicCubeState, VisualCubeState
from pxr import UsdGeom, Usd


class VisualCube(GeometryPrim):
    def __init__(
        self,
        stage: Usd.Stage,
        prim_path: str,
        name: str,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        color: Optional[np.ndarray] = None,
        size: float = 0.5,
    ) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
            prim_path (str): [description]
            name (Optional, optional): [description]. Defaults to None.
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
            color (Optional, optional): [description]. Defaults to None.
            size (float, optional): [description]. Defaults to 0.5.
        """
        cubeGeom = UsdGeom.Cube.Define(stage, prim_path)
        cubePrim = stage.GetPrimAtPath(prim_path)
        super().__init__(cubePrim, cubeGeom, name, position, orientation, color=color)
        self.set_usd_size(size)
        # TODO: opacity is not working for some reason
        # self.geom.CreateDisplayOpacityAttr([0.5])
        self._default_state = VisualCubeState(
            self._default_state.position, self._default_state.orientation, self._default_state.color, size
        )
        return

    def set_usd_size(self, size: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.CreateSizeAttr(size)
        return

    def get_usd_size(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetSizeAttr().Get()

    def set_usd_extent(self, extent):
        """[summary]

        Args:
            extent ([type]): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def get_usd_extent(self, extent):
        """[summary]

        Args:
            extent ([type]): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def set_default_state(self, position: np.ndarray, orientation: np.ndarray, color: np.ndarray, size: float) -> None:
        """[summary]

        Args:
            position (np.ndarray): [description]
            orientation (np.ndarray): [description]
            color (np.ndarray): [description]
            size (float): [description]
        """
        self._default_state = VisualCubeState(position, orientation, color, size)
        return

    def reset(self) -> None:
        """Resets the prim to its default state.
        """
        super().reset()
        self.set_usd_size(self._default_state.size)
        return


class DynamicCube(RigidPrim):
    def __init__(
        self,
        stage: Usd.Stage,
        prim_path: str,
        name: str,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        mass: Optional[float] = None,
        color: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
        collisions_enabled: bool = True,
        static_friction: float = 0.0,
        dynamic_friction: float = 0.0,
        restitution: float = 0.8,
        size: float = 0.5,
    ) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
            prim_path (str): [description]
            name (Optional, optional): [description]. Defaults to None.
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
            mass (Optional, optional): [description]. Defaults to None.
            color (Optional, optional): [description]. Defaults to None.
            linear_velocity (Optional, optional): [description]. Defaults to None.
            angular_velocity (Optional, optional): [description]. Defaults to None.
            collisions_enabled (bool, optional): [description]. Defaults to True.
            static_friction (float, optional): [description]. Defaults to 0.0.
            dynamic_friction (float, optional): [description]. Defaults to 0.0.
            restitution (float, optional): [description]. Defaults to 0.8.
            size (float, optional): [description]. Defaults to 0.5.
        """
        cubeGeom = UsdGeom.Cube.Define(stage, prim_path)
        cubePrim = stage.GetPrimAtPath(prim_path)
        super().__init__(
            prim=cubePrim,
            name=name,
            position=position,
            orientation=orientation,
            mass=mass,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
        )
        self._geom_prim = GeometryPrim(
            prim=cubePrim, geom=cubeGeom, name=name, position=position, orientation=orientation, color=color
        )
        self._collision_prim = None
        if collisions_enabled:
            self._collision_prim = CollisionPrim(
                stage=stage,
                prim=cubePrim,
                name=name,
                position=position,
                orientation=orientation,
                density=None,
                static_friction=static_friction,
                dynamic_friction=dynamic_friction,
                restitution=restitution,
            )
        self.set_usd_size(size)
        self._default_state = DynamicCubeState(
            self._default_state.position,
            self._default_state.orientation,
            self._default_state.linear_velocity,
            self._default_state.angular_velocity,
            self._default_state.mass,
            size,
        )
        return

    def set_usd_size(self, size: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self._geom_prim.geom.CreateSizeAttr(size)
        return

    def get_usd_size(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self._geom_prim.geom.GetSizeAttr().Get()

    def set_usd_extent(self, extent):
        raise NotImplementedError

    def get_usd_extent(self, extent):
        raise NotImplementedError

    def set_default_state(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
        linear_velocity: np.ndarray,
        angular_velocity: np.ndarray,
        mass: float,
        size: float,
    ) -> None:
        """[summary]

        Args:
            position (np.ndarray): [description]
            orientation (np.ndarray): [description]
            linear_velocity (np.ndarray): [description]
            angular_velocity (np.ndarray): [description]
            mass (float): [description]
            size (float): [description]
        """
        self._default_state = DynamicCubeState(position, orientation, linear_velocity, angular_velocity, mass, size)
        # TODO: collision state and geometry state
        return

    def reset(self) -> None:
        """Resets the prim to its default state.
        """
        super().reset()
        self.set_usd_size(self._default_state.size)
        # TODO: reset collision prim and geometry prim
        return
