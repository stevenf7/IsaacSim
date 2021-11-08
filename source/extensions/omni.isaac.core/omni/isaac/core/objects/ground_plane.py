# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.prims import GeometryPrim
from omni.isaac.core.utils.string import find_unique_string_name
from pxr import Gf, PhysicsSchemaTools
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.materials import PreviewSurface
from omni.isaac.core.utils.prims import is_prim_path_valid, get_first_matching_child_prim, get_prim_type_name
from omni.isaac.core.utils.stage import get_current_stage, get_stage_units
from typing import Optional
import numpy as np
import carb


class GroundPlane(GeometryPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "ground_plane",
        size: float = 500.0,
        z_position: float = 0,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        color: Optional[np.ndarray] = None,
        physics_material_path=None,
        visual_material=None,
        static_friction=0.5,
        dynamic_friction=0.5,
        restitution=0.8,
    ) -> None:
        """adds a ground plane at the specified height and with the specified size length and thickness.
           collisions are enabled on this plane by default. 

        Args:
            stage (Usd.Prim): current usd stage used.
            prim_path (str): prim path to add the ground plane at in the stage.
            size (float): side length of the plane.
            z_position (float): height to add the plane at.
            thickness (float): thickness of the plane itself.
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
        """
        if not is_prim_path_valid(prim_path):
            carb.log_info("Creating a new Ground Plane prim at path {}".format(prim_path))
            stage = get_current_stage()
            if size is None:
                size = 50.0 / get_stage_units()
            PhysicsSchemaTools.addGroundPlane(
                stage, prim_path, "Z", size, Gf.Vec3f(0, 0, z_position), Gf.Vec3f([0.0, 0.0, 0.0])
            )
            prim_path = prim_path + "/geom"
        else:
            prim_path = get_first_matching_child_prim(
                prim_path=prim_path, predicate=lambda x: get_prim_type_name(x) == "Plane"
            )
        GeometryPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=None,
            orientation=None,
            scale=scale,
            visible=visible,
            collision=True,
        )
        GeometryPrim.set_world_pose(self, position=np.array([0, 0, z_position]))
        GeometryPrim.set_default_state(self, position=np.array([0, 0, z_position]))
        if physics_material_path is None:
            physics_material_path = find_unique_string_name(
                intitial_name="/World/Physics_Materials/physics_material",
                is_unique_fn=lambda x: not is_prim_path_valid(x),
            )
            physics_material = PhysicsMaterial(
                prim_path=physics_material_path,
                dynamic_friction=dynamic_friction,
                static_friction=static_friction,
                restitution=restitution,
            )
        else:
            physics_material = PhysicsMaterial(prim_path=physics_material_path)
        self.apply_physics_material(physics_material)
        if not self.is_visual_material_applied():
            if visual_material is None:
                if color is None:
                    color = np.array([0.5, 0.5, 0.5])
                visual_prim_path = find_unique_string_name(
                    intitial_name="/World/Looks/visual_material", is_unique_fn=lambda x: not is_prim_path_valid(x)
                )
                visual_material = PreviewSurface(prim_path=visual_prim_path, color=color)
            self.apply_visual_material(visual_material)
        return
