from typing import List

from omni.isaac.cloner import Cloner
import omni.usd
from pxr import Gf, Usd, UsdGeom, UsdPhysics

import numpy as np


class GridCloner(Cloner):
    def __init__(self, spacing: int, num_per_row: int = -1):
        self._spacing = spacing
        self._num_per_row = num_per_row

    def define_base_env(self, base_env_path: str):
        UsdGeom.Scope.Define(omni.usd.get_context().get_stage(), base_env_path)

    def clone(
        self,
        source_prim_path: str,
        prim_paths: List[str],
        position_offsets: np.ndarray = None,
        orientation_offsets: np.ndarray = None,
    ):
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

    def filter_collisions(self, collision_root_path: str, prim_paths: List[str]):
        stage = omni.usd.get_context().get_stage()

        collision_scope = UsdGeom.Scope.Define(stage, collision_root_path)
        collision_group_dict = dict()
        collision_group_paths = []

        # set collision groups and filters
        for i, prim_path in enumerate(prim_paths):
            collision_group_path = collision_root_path + f"/group{i}"
            collision_group = UsdPhysics.CollisionGroup.Define(stage, collision_group_path)
            collection = Usd.CollectionAPI.ApplyCollection(collision_group.GetPrim(), "colliders")
            collection.CreateIncludesRel().AddTarget(prim_path)
            collision_group_dict[prim_path] = collision_group
            collision_group_paths.append(collision_group_path)

        for i, prim_path in enumerate(prim_paths):
            other_collision_groups = collision_group_paths[:i] + collision_group_paths[i + 1 :]
            collision_group_dict[prim_path].CreateFilteredGroupsRel().SetTargets(other_collision_groups)
