# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.prims import GeometryPrim
from pxr import Gf, PhysicsSchemaTools, Usd
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.materials import PreviewSurface
import numpy as np


class GroundPlane(GeometryPrim):
    def __init__(
        self,
        stage: Usd.Prim,
        prim_path: str,
        name: str,
        size: float = 50.0,
        z_position: float = 0.0,
        thickness: float = 0.01,
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
        PhysicsSchemaTools.addGroundPlane(stage, prim_path, "Z", size, Gf.Vec3f(0, 0, z_position), Gf.Vec3f(thickness))
        ground_prim = stage.GetPrimAtPath(prim_path)
        super().__init__(prim=ground_prim, name=name, position=None, orientation=None, collision=True)

        physics_material = PhysicsMaterial(
            prim_path=prim_path + "/physics_material", static_friction=0.5, dynamic_friction=0.5, restitution=0.8
        )

        self.apply_physics_material(physics_material)
        preview_surface = PreviewSurface(prim_path=prim_path + "/visual_material", color=np.array([0.5, 0.5, 0.5]))
        self.apply_visual_material(preview_surface)
        return
