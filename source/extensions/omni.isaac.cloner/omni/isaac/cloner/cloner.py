from typing import List
import omni.usd
from pxr import UsdGeom, Gf

import numpy as np


class Cloner:
    def __init__(self):
        pass

    def generate_paths(self, root_path: str, num_paths: int):
        return [f"{root_path}_{i}" for i in range(num_paths)]

    def clone(
        self,
        source_prim_path: str,
        prim_paths: List[str],
        positions: np.ndarray = None,
        orientations: np.ndarray = None,
    ):
        stage = omni.usd.get_context().get_stage()

        if positions is not None:
            assert len(positions) == len(prim_paths), "dimension mismatch between positions and prim_paths!"
        if orientations is not None:
            assert len(orientations) == len(prim_paths), "dimension mismatch between orientations and prim_paths!"

        for i, prim_path in enumerate(prim_paths):
            if prim_path != source_prim_path:
                omni.usd.duplicate_prim(omni.usd.get_context().get_stage(), source_prim_path, prim_path, False)

            # set actor transform
            prim = UsdGeom.Xform(stage.GetPrimAtPath(prim_path))
            if not prim.GetPrim():
                raise Exception("Failed to add actor to environment")

            if positions is not None:
                translation = Gf.Vec3d(positions[i].tolist())
            else:
                translation = Gf.Vec3d(0, 0, 0)

            if orientations is not None:
                orientation = Gf.Quatd(orientations[i][0].item(), Gf.Vec3d(orientations[i][1:].tolist()))
            else:
                orientation = Gf.Quatd.GetIdentity()

            properties = prim.GetPrim().GetPropertyNames()
            if "xformOp:translate" not in properties:
                prim.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble)
            if "xformOp:orient" not in properties:
                prim.AddOrientOp(UsdGeom.XformOp.PrecisionDouble)
            if "xformOp:scale" not in properties:
                # don't overwrite scale if it already exists
                prim.AddScaleOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(1.0, 1.0, 1.0))

            # overwrite translation and orientation to values specified
            prim.GetPrim().GetAttribute("xformOp:translate").Set(translation)
            prim.GetPrim().GetAttribute("xformOp:orient").Set(orientation)
