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
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.materials import PreviewSurface
from omni.isaac.core.materials import PhysicsMaterial
from pxr import UsdGeom, Usd, Gf


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
        cubeGeom.GetExtentAttr().Set(
            [Gf.Vec3f([-size / 2.0, -size / 2.0, -size / 2.0]), Gf.Vec3f([size / 2.0, size / 2.0, size / 2.0])]
        )
        cubePrim = stage.GetPrimAtPath(prim_path)
        super().__init__(prim=cubePrim, name=name, position=position, orientation=orientation)
        self.set_usd_size(size)
        my_preview_surface = PreviewSurface(prim_path=prim_path + "/visual", color=color)
        self.apply_visual_material(my_preview_surface)
        # )
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


class DynamicCube(RigidPrim, GeometryPrim):
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
        # TODO: search for a way to compute this better
        cubeGeom.GetExtentAttr().Set(
            [Gf.Vec3f([-size / 2.0, -size / 2.0, -size / 2.0]), Gf.Vec3f([size / 2.0, size / 2.0, size / 2.0])]
        )
        cubePrim = stage.GetPrimAtPath(prim_path)
        GeometryPrim.__init__(
            self, prim=cubePrim, name=name, position=position, orientation=orientation, collision=True
        )
        RigidPrim.__init__(
            self,
            prim=cubePrim,
            name=name,
            position=position,
            orientation=orientation,
            mass=mass,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
        )
        self.set_usd_size(size)
        # create visual material
        my_preview_surface = PreviewSurface(prim_path=prim_path + "/visual", color=color)
        self.apply_visual_material(my_preview_surface)
        my_physics_material = PhysicsMaterial(
            prim_path=prim_path + "/physics_material",
            dynamic_friction=dynamic_friction,
            static_friction=static_friction,
            restitution=restitution,
        )

        self.apply_physics_material(my_physics_material)
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
