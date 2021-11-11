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
from omni.isaac.core.materials.visual_material import VisualMaterial
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.materials import PreviewSurface
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.utils.string import find_unique_string_name
from pxr import UsdGeom, Gf
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import get_current_stage


class VisualCapsule(GeometryPrim):
    """[summary]

        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "visual_capsule".
            position (Optional[np.ndarray], optional): [description]. Defaults to None.
            translation (Optional[np.ndarray], optional): [description]. Defaults to None.
            orientation (Optional[np.ndarray], optional): [description]. Defaults to None.
            scale (Optional[np.ndarray], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            color (Optional[np.ndarray], optional): [description]. Defaults to None.
            radius (float, optional): [description]. Defaults to 0.5.
            height (float, optional): [description]. Defaults to 0.5.
            visual_material (Optional[VisualMaterial], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "visual_capsule",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        color: Optional[np.ndarray] = None,
        radius: float = 0.5,
        height: float = 0.5,
        visual_material: Optional[VisualMaterial] = None,
    ) -> None:
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Capsule):
                raise Exception("The prim at path {} cannot be parsed as a Capsule object".format(prim_path))
            capsule_geom = UsdGeom.Capsule(prim)
        else:
            capsule_geom = UsdGeom.Capsule.Define(get_current_stage(), prim_path)
            # TODO: double check the capsule extent
            capsule_geom.GetExtentAttr().Set(
                [Gf.Vec3f([-radius, -radius, -height / 2.0]), Gf.Vec3f([radius, radius, height / 2.0])]
            )
        GeometryPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
        )
        VisualCapsule.set_radius(self, radius)
        VisualCapsule.set_height(self, height)
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_prim_path = find_unique_string_name(
                    intitial_name="/World/Looks/visual_material", is_unique_fn=lambda x: not is_prim_path_valid(x)
                )
                visual_material = PreviewSurface(prim_path=visual_prim_path, color=color)
            VisualCapsule.apply_visual_material(self, visual_material)
        return

    def set_radius(self, radius: float) -> None:
        """[summary]

        Args:
            radius (float): [description]
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
            height (float): [description]
        """
        self.geom.GetHeightAttr().Set(height)
        return

    def get_height(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetHeightAttr().Get()


class DynamicCapsule(RigidPrim, GeometryPrim):
    """[summary]

        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "dynamic_capsule".
            position (Optional[np.ndarray], optional): [description]. Defaults to None.
            translation (Optional[np.ndarray], optional): [description]. Defaults to None.
            orientation (Optional[np.ndarray], optional): [description]. Defaults to None.
            scale (Optional[np.ndarray], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            mass (Optional[float], optional): [description]. Defaults to None.
            color (Optional[np.ndarray], optional): [description]. Defaults to None.
            linear_velocity (Optional[np.ndarray], optional): [description]. Defaults to None.
            angular_velocity (Optional[np.ndarray], optional): [description]. Defaults to None.
            static_friction (float, optional): [description]. Defaults to 0.0.
            dynamic_friction (float, optional): [description]. Defaults to 0.0.
            restitution (float, optional): [description]. Defaults to 0.8.
            radius (float, optional): [description]. Defaults to 0.5.
            height (float, optional): [description]. Defaults to 0.5.
            physics_material_path (Optional[PhysicsMaterial], optional): [description]. Defaults to None.
            visual_material (Optional[VisualMaterial], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "dynamic_capsule",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        mass: Optional[float] = None,
        color: Optional[np.ndarray] = None,
        linear_velocity: Optional[np.ndarray] = None,
        angular_velocity: Optional[np.ndarray] = None,
        static_friction: float = 0.0,
        dynamic_friction: float = 0.0,
        restitution: float = 0.8,
        radius: float = 0.5,
        height: float = 0.5,
        physics_material_path: Optional[PhysicsMaterial] = None,
        visual_material: Optional[VisualMaterial] = None,
    ) -> None:
        if is_prim_path_valid(prim_path):
            prim = get_prim_at_path(prim_path)
            if not prim.IsA(UsdGeom.Capsule):
                raise Exception("The prim at path {} cannot be parsed as a Capsule object".format(prim_path))
            capsule_geom = UsdGeom.Capsule(prim)
        else:
            capsule_geom = UsdGeom.Capsule.Define(get_current_stage(), prim_path)
            # TODO: double check the sphere extent
            capsule_geom.GetExtentAttr().Set(
                [Gf.Vec3f([-radius, -radius, -height / 2.0]), Gf.Vec3f([radius, radius, height / 2.0])]
            )
        GeometryPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
            collision=True,
        )
        RigidPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
            mass=mass,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
        )
        DynamicCapsule.set_radius(self, radius)
        DynamicCapsule.set_height(self, height)
        # create visual material
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_prim_path = find_unique_string_name(
                    intitial_name="/World/Looks/visual_material", is_unique_fn=lambda x: not is_prim_path_valid(x)
                )
                visual_material = PreviewSurface(prim_path=visual_prim_path, color=color)
            DynamicCapsule.apply_visual_material(self, visual_material)

        if physics_material_path is None:
            physics_material_path = find_unique_string_name(
                intitial_name="/World/Physics_Materials/physics_material",
                is_unique_fn=lambda x: not is_prim_path_valid(x),
            )
            my_physics_material = PhysicsMaterial(
                prim_path=physics_material_path,
                dynamic_friction=dynamic_friction,
                static_friction=static_friction,
                restitution=restitution,
            )

        else:
            my_physics_material = PhysicsMaterial(prim_path=physics_material_path)
        DynamicCapsule.apply_physics_material(self, my_physics_material)
        return

    def set_radius(self, radius: float) -> None:
        """[summary]

        Args:
            radius (float): [description]
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
            height (float): [description]
        """
        self.geom.GetHeightAttr().Set(height)
        return

    def get_height(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self.geom.GetHeightAttr().Get()
