# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Sequence
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


class VisualCuboid(GeometryPrim):
    """[summary]

    Args:
        prim_path (str): [description]
        name (str, optional): [description]. Defaults to "visual_cube".
        position (Optional[Sequence[float]], optional): [description]. Defaults to None.
        translation (Optional[Sequence[float]], optional): [description]. Defaults to None.
        orientation (Optional[Sequence[float]], optional): [description]. Defaults to None.
        scale (Optional[Sequence[float]], optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to True.
        color (Optional[np.ndarray], optional): [description]. Defaults to None.
        size (Optional[np.ndarray], optional): [description]. Defaults to None.
        visual_material (Optional[VisualMaterial], optional): [description]. Defaults to None.

    Raises:
        Exception: [description]
    """

    def __init__(
        self,
        prim_path: str,
        name: str = "visual_cube",
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: bool = True,
        color: Optional[np.ndarray] = None,
        size: Optional[np.ndarray] = None,
        visual_material: Optional[VisualMaterial] = None,
    ) -> None:
        if size is None:
            size = np.array([5, 5, 5])
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
            scale=scale,
            visible=visible,
            collision=False,
        )
        VisualCuboid.set_size(self, size)
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_prim_path = find_unique_string_name(
                    initial_name="/World/Looks/visual_material", is_unique_fn=lambda x: not is_prim_path_valid(x)
                )
                visual_material = PreviewSurface(prim_path=visual_prim_path, color=color)
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


class FixedCuboid(VisualCuboid):
    """[summary]

        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "dynamic_cube".
            position (Optional[Sequence[float]], optional): [description]. Defaults to None.
            translation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            orientation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            scale (Optional[Sequence[float]], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            color (Optional[np.ndarray], optional): [description]. Defaults to None.
            static_friction (float, optional): [description]. Defaults to 0.2.
            dynamic_friction (float, optional): [description]. Defaults to 1.0.
            restitution (float, optional): [description]. Defaults to 0.0.
            size (Optional[np.ndarray], optional): [description]. Defaults to None.
            physics_material_path (Optional[PhysicsMaterial], optional): [description]. Defaults to None.
            visual_material (Optional[VisualMaterial], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "dynamic_cube",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        color: Optional[np.ndarray] = None,
        static_friction: float = 0.2,
        dynamic_friction: float = 1.0,
        restitution: float = 0.0,
        size: Optional[np.ndarray] = None,
        physics_material_path: Optional[PhysicsMaterial] = None,
        visual_material: Optional[VisualMaterial] = None,
    ) -> None:
        VisualCuboid.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
            color=color,
            size=size,
            visual_material=visual_material,
        )
        GeometryPrim.set_collision_enabled(self, True)

        if physics_material_path is None:
            physics_material_path = find_unique_string_name(
                initial_name="/World/Physics_Materials/physics_material",
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

        FixedCuboid.apply_physics_material(self, my_physics_material)
        FixedCuboid.set_rest_offset(self, 0.0)
        FixedCuboid.set_contact_offset(self, 0.1)
        FixedCuboid.set_torsional_patch_radius(self, 1.0)
        FixedCuboid.set_min_torsional_patch_radius(self, 0.8)
        return


class DynamicCuboid(FixedCuboid, RigidPrim):
    """[summary]

        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "dynamic_cube".
            position (Optional[Sequence[float]], optional): [description]. Defaults to None.
            translation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            orientation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            scale (Optional[Sequence[float]], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            mass (Optional[float], optional): [description]. Defaults to 0.02.
            color (Optional[np.ndarray], optional): [description]. Defaults to None.
            linear_velocity (Optional[Sequence[float]], optional): [description]. Defaults to None.
            angular_velocity (Optional[Sequence[float]], optional): [description]. Defaults to None.
            static_friction (float, optional): [description]. Defaults to 0.2.
            dynamic_friction (float, optional): [description]. Defaults to 1.0.
            restitution (float, optional): [description]. Defaults to 0.0.
            size (Optional[np.ndarray], optional): [description]. Defaults to None.
            physics_material_path (Optional[PhysicsMaterial], optional): [description]. Defaults to None.
            visual_material (Optional[VisualMaterial], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "dynamic_cube",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        mass: Optional[float] = 0.02,
        density: Optional[float] = None,
        color: Optional[np.ndarray] = None,
        linear_velocity: Optional[Sequence[float]] = None,
        angular_velocity: Optional[Sequence[float]] = None,
        static_friction: float = 0.2,
        dynamic_friction: float = 1.0,
        restitution: float = 0.0,
        size: Optional[np.ndarray] = None,
        physics_material_path: Optional[PhysicsMaterial] = None,
        visual_material: Optional[VisualMaterial] = None,
    ) -> None:
        FixedCuboid.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
            color=color,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
            size=size,
            physics_material_path=physics_material_path,
            visual_material=visual_material,
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
            density=density,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
        )
