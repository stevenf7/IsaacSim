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


class VisualCone(GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "visual_cone",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        color: Optional[np.ndarray] = None,
        radius: float = 0.5,
        height: float = 0.5,
        visual_material_path=None,
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
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Cone):
                raise Exception("The prim at path {} cannot be parsed as a Cone object".format(prim_path))
            cone_geom = UsdGeom.Cone(prim)
        else:
            cone_geom = UsdGeom.Cone.Define(get_current_stage(), prim_path)
            # TODO: double check the sphere extent
            cone_geom.GetExtentAttr().Set(
                [Gf.Vec3f([-radius, -radius, -height / 2.0]), Gf.Vec3f([radius, radius, height / 2.0])]
            )
        GeometryPrim.__init__(
            self, prim_path=prim_path, name=name, position=position, translation=translation, orientation=orientation
        )
        VisualCone.set_radius(self, radius)
        VisualCone.set_height(self, height)
        if visual_material_path is None:
            if color is None:
                color = np.arrray([0.5, 0.5, 0.5])
            preview_surface = PreviewSurface(prim_path=prim_path + "/visual_material", color=color)
        else:
            preview_surface = PreviewSurface(prim_path=visual_material_path)
        VisualCone.apply_visual_material(self, preview_surface)
        return

    def set_radius(self, radius: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.GetRadiusAttr().Set(radius)
        return

    def get_radius(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetRadiusAttr().Get()

    def set_height(self, height: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.GetHeightAttr().Set(height)
        return

    def get_height(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetHeightAttr().Get()


class DynamicCone(RigidPrim, GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "dynamic_cone",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        mass: Optional[float] = None,
        color: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
        static_friction: float = 0.0,
        dynamic_friction: float = 0.0,
        restitution: float = 0.8,
        radius: float = 0.5,
        height: float = 0.5,
        physics_material_path=None,
        visual_material_path=None,
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
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Cone):
                raise Exception("The prim at path {} cannot be parsed as a Cone object".format(prim_path))
            cone_geom = UsdGeom.Cone(prim)
        else:
            cone_geom = UsdGeom.Cone.Define(get_current_stage(), prim_path)
            # TODO: double check the sphere extent
            cone_geom.GetExtentAttr().Set(
                [Gf.Vec3f([-radius, -radius, -height / 2.0]), Gf.Vec3f([radius, radius, height / 2.0])]
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
        DynamicCone.set_radius(self, radius)
        DynamicCone.set_height(self, height)
        # create visual material
        if visual_material_path is None:
            if color is None:
                color = np.arrray([0.5, 0.5, 0.5])
            preview_surface = PreviewSurface(prim_path=prim_path + "/visual_material", color=color)
        else:
            preview_surface = PreviewSurface(prim_path=visual_material_path)
        DynamicCone.apply_visual_material(self, preview_surface)

        if physics_material_path is None:
            my_physics_material = PhysicsMaterial(
                prim_path=prim_path + "/physics_material",
                dynamic_friction=dynamic_friction,
                static_friction=static_friction,
                restitution=restitution,
            )

        else:
            my_physics_material = PhysicsMaterial(prim_path=physics_material_path)
        DynamicCone.apply_physics_material(self, my_physics_material)
        return

    def set_radius(self, radius: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.GetRadiusAttr().Set(radius)
        return

    def get_radius(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetRadiusAttr().Get()

    def set_height(self, height: float) -> None:
        """[summary]

        Args:
            size (float): [description]
        """
        self.geom.GetHeightAttr().Set(height)
        return

    def get_height(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetHeightAttr().Get()
