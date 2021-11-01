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
from pxr import UsdGeom, Gf
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import get_current_stage


class VisualCuboid(GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "visual_cube",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        color: Optional[np.ndarray] = None,
        size: Optional[np.ndarray] = None,
        visual_material=None,
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
        if size is None:
            size = np.array([0.5, 0.5, 0.5])
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Cube):
                raise Exception("The prim at path {} cannot be parsed as a Cube object".format(prim_path))
            cubeGeom = UsdGeom.Cube(prim)
        else:
            cubeGeom = UsdGeom.Cube.Define(get_current_stage(), prim_path)
            cubeGeom.GetExtentAttr().Set(
                [
                    Gf.Vec3f([-size[0] / 2.0, -size[1] / 2.0, -size[2] / 2.0]),
                    Gf.Vec3f([size[0] / 2.0, size[1] / 2.0, size[2] / 2.0]),
                ]
            )
        GeometryPrim.__init__(
            self, prim_path=prim_path, name=name, position=position, translation=translation, orientation=orientation
        )
        VisualCuboid.set_size(self, size)
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_material = PreviewSurface(prim_path=prim_path + "/visual_material", color=color)
            VisualCuboid.apply_visual_material(self, visual_material)
        return

    def set_size(self, size: np.ndarray) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.CreateSizeAttr(1.0)
        self.set_local_scale(size)
        return

    def get_size(self) -> np.ndarray:
        """[summary]

        Returns:
            float: [description]
        """
        return self.get_local_scale()


class DynamicCuboid(RigidPrim, GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "dynamic_cube",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        mass: Optional[float] = 0.02,
        color: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
        static_friction: float = 0.2,
        dynamic_friction: float = 1.0,
        restitution: float = 0.0,
        size: Optional[np.ndarray] = None,
        physics_material_path=None,
        visual_material=None,
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
        if size is None:
            size = np.array([0.5, 0.5, 0.5])
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Cube):
                raise Exception("The prim at path {} cannot be parsed as a Cube object".format(prim_path))
            cubeGeom = UsdGeom.Cube(prim)
        else:
            cubeGeom = UsdGeom.Cube.Define(get_current_stage(), prim_path)
            cubeGeom.GetExtentAttr().Set(
                [
                    Gf.Vec3f([-size[0] / 2.0, -size[1] / 2.0, -size[2] / 2.0]),
                    Gf.Vec3f([size[0] / 2.0, size[1] / 2.0, size[2] / 2.0]),
                ]
            )
        GeometryPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            collision=True,
        )
        RigidPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            mass=mass,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
        )
        DynamicCuboid.set_size(self, size)
        # create visual material
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_material = PreviewSurface(prim_path=prim_path + "/visual_material", color=color)
            DynamicCuboid.apply_visual_material(self, visual_material)

        if physics_material_path is None:
            my_physics_material = PhysicsMaterial(
                prim_path=prim_path + "/physics_material",
                dynamic_friction=dynamic_friction,
                static_friction=static_friction,
                restitution=restitution,
            )

        else:
            my_physics_material = PhysicsMaterial(prim_path=physics_material_path)
        DynamicCuboid.apply_physics_material(self, my_physics_material)
        DynamicCuboid.set_rest_offset(self, 0.0)
        DynamicCuboid.set_contact_offset(self, 0.1)
        DynamicCuboid.set_torsional_patch_radius(self, 1.0)
        DynamicCuboid.set_min_torsional_patch_radius(self, 0.8)
        return

    def set_size(self, size: np.ndarray) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.CreateSizeAttr(1.0)
        self.set_local_scale(size)
        return

    def get_size(self) -> np.ndarray:
        """[summary]

        Returns:
            float: [description]
        """
        return self.get_local_scale()


class FixedCuboid(GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "dynamic_cube",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        color: Optional[np.ndarray] = None,
        static_friction: float = 0.2,
        dynamic_friction: float = 1.0,
        restitution: float = 0.0,
        size: float = 0.5,
        physics_material_path=None,
        visual_material=None,
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
        if size is None:
            size = np.array([0.5, 0.5, 0.5])
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Cube):
                raise Exception("The prim at path {} cannot be parsed as a Cube object".format(prim_path))
            cubeGeom = UsdGeom.Cube(prim)
        else:
            cubeGeom = UsdGeom.Cube.Define(get_current_stage(), prim_path)
            cubeGeom.GetExtentAttr().Set(
                [
                    Gf.Vec3f([-size[0] / 2.0, -size[1] / 2.0, -size[2] / 2.0]),
                    Gf.Vec3f([size[0] / 2.0, size[1] / 2.0, size[2] / 2.0]),
                ]
            )
        GeometryPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            collision=True,
        )
        FixedCuboid.set_size(self, size)
        # create visual material
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_material = PreviewSurface(prim_path=prim_path + "/visual_material", color=color)
            FixedCuboid.apply_visual_material(self, visual_material)

        if physics_material_path is None:
            my_physics_material = PhysicsMaterial(
                prim_path=prim_path + "/physics_material",
                dynamic_friction=dynamic_friction,
                static_friction=static_friction,
                restitution=restitution,
            )

        else:
            my_physics_material = PhysicsMaterial(prim_path=physics_material_path)
        FixedCuboid.apply_physics_material(self, my_physics_material)
        FixedCuboid.set_rest_offset(self, 0.0)
        FixedCuboid.set_contact_offset(self, 0.1)
        FixedCuboid.set_torsional_patch_radius(self, 1.0)
        FixedCuboid.set_min_torsional_patch_radius(self, 0.8)
        return

    def set_size(self, size: np.ndarray) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.CreateSizeAttr(1.0)
        self.set_local_scale(size)
        return

    def get_size(self) -> np.ndarray:
        """[summary]

        Returns:
            float: [description]
        """
        return self.get_local_scale()
