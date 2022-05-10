from typing import List

from omni.isaac.cloner import Cloner
import omni.usd
from pxr import Gf, Usd, UsdGeom, UsdPhysics, PhysxSchema

import numpy as np


class GridCloner(Cloner):

    """ This is a specialized Cloner class that will automatically generate clones in a grid fashion. """

    def __init__(self, spacing: float, num_per_row: int = -1):
        """ 
        Args:
            spacing (float): Spacing between clones.
            num_per_row (int): Number of clones to place in a row. Defaults to sqrt(num_clones).
        """
        self._spacing = spacing
        self._num_per_row = num_per_row

    def define_base_env(self, base_env_path: str):
        """ Creates a USD Scope at base_env_path. This is designed to be the parent that holds all clones.

        Args:
            base_env_path (str): Path to create the USD Scope at.
        """

        UsdGeom.Scope.Define(omni.usd.get_context().get_stage(), base_env_path)

    def clone(
        self,
        source_prim_path: str,
        prim_paths: List[str],
        position_offsets: np.ndarray = None,
        orientation_offsets: np.ndarray = None,
    ):

        """ Creates clones in a grid fashion. Positions of clones are computed automatically.

        Args:
            source_prim_path (str): Path of source object.
            prim_paths (List[str]): List of destination paths.
            position_offsets (np.ndarray): Positions to be applied as local translations on top of computed clone position.
                                           Defaults to None, no offset will be applied.
            orientation_offsets (np.ndarray): Orientations to be applied as local rotations for each clone.
                                           Defaults to None, no offset will be applied.

        Returns:
            positions (List): Computed positions of all clones.
        """

        num_clones = len(prim_paths)

        self._num_per_row = int(np.sqrt(num_clones)) if self._num_per_row == -1 else self._num_per_row
        num_rows = np.ceil(num_clones / self._num_per_row)
        num_cols = np.ceil(num_clones / num_rows)

        row_offset = 0.5 * self._spacing * (num_rows - 1)
        col_offset = 0.5 * self._spacing * (num_cols - 1)

        stage = omni.usd.get_context().get_stage()

        positions = []
        orientations = []

        for i in range(num_clones):
            # compute transform
            row = i // num_cols
            col = i % num_cols
            x = row_offset - row * self._spacing
            y = col * self._spacing - col_offset

            up_axis = UsdGeom.GetStageUpAxis(stage)
            position = [x, y, 0] if up_axis == UsdGeom.Tokens.z else [x, 0, y]
            orientation = Gf.Quatd.GetIdentity()

            if position_offsets is not None:
                translation = position_offsets[i] + np.array(position)
            else:
                translation = np.array(position)

            if orientation_offsets is not None:
                orientation = np.array(
                    Gf.Quatd(orientation_offsets[i][0].item(), Gf.Vec3d(orientation_offsets[i][1:].tolist()))
                    * orientation
                )
            else:
                orientation = np.array(
                    [
                        orientation.GetReal(),
                        orientation.GetImaginary()[0],
                        orientation.GetImaginary()[1],
                        orientation.GetImaginary()[2],
                    ]
                )

            positions.append(translation)
            orientations.append(orientation)

        super().clone(
            source_prim_path=source_prim_path,
            prim_paths=prim_paths,
            positions=np.array(positions),
            orientations=np.array(orientations),
        )

        return positions

    def filter_collisions(
        self, physicsscene_path: str, collision_root_path: str, prim_paths: List[str], global_paths: List[str] = []
    ):
        """ Filters collisions between clones. Clones will not collide with each other, but can collide with objects specified in global_paths.
        
        Args:
            physicsscene_path (str): Path to PhysicsScene object in stage.
            collision_root_path (str): Path to place collision groups under.
            prim_paths (List[str]): Paths of objects to filter out collision.
            global_paths (List[str]): Paths of objects to generate collision (e.g. ground plane).

        """

        stage = omni.usd.get_context().get_stage()
        physx_scene = PhysxSchema.PhysxSceneAPI(stage.GetPrimAtPath(physicsscene_path))

        # We invert the collision group filters for more efficient collision filtering across environments
        physx_scene.CreateInvertCollisionGroupFilterAttr().Set(True)

        collision_scope = UsdGeom.Scope.Define(stage, collision_root_path)

        if len(global_paths) > 0:
            global_collision_group_path = collision_root_path + f"/global_group"
            collision_group = UsdPhysics.CollisionGroup.Define(stage, global_collision_group_path)
            collection = Usd.CollectionAPI.ApplyCollection(collision_group.GetPrim(), "colliders")

            for global_path in global_paths:
                collection.CreateIncludesRel().AddTarget(global_path)

            # We are using inverted collision group filtering, which means objects by default don't collide across
            # groups. We need to add this group as a filtered group, so that objects within this group collide with
            # each other.
            collision_group.CreateFilteredGroupsRel().AddTarget(global_collision_group_path)

        # set collision groups and filters
        for i, prim_path in enumerate(prim_paths):
            collision_group_path = collision_root_path + f"/group{i}"
            collision_group = UsdPhysics.CollisionGroup.Define(stage, collision_group_path)
            collection = Usd.CollectionAPI.ApplyCollection(collision_group.GetPrim(), "colliders")
            collection.CreateIncludesRel().AddTarget(prim_path)

            # We are using inverted collision group filtering, which means objects by default don't collide across
            # groups. We need to add this group as a filtered group, so that objects within this group collide with
            # each other.
            collision_group.CreateFilteredGroupsRel().AddTarget(collision_group_path)
            if len(global_paths) > 0:
                collision_group.CreateFilteredGroupsRel().AddTarget(global_collision_group_path)
                UsdPhysics.CollisionGroup.Get(stage, global_collision_group_path).CreateFilteredGroupsRel().AddTarget(
                    collision_group_path
                )
