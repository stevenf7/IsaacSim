from typing import List
import omni.usd
from pxr import UsdGeom, Gf

import numpy as np


class Cloner:

    """ This class provides a set of simple APIs to make duplication of objects simple and
        efficient. Objects can be cloned using this class to create copies of the same object,
        placed at user-specified locations in the scene.
    """

    def __init__(self):
        pass

    def generate_paths(self, root_path: str, num_paths: int):

        """ Generates a list of paths under the root path specified. 

        Args:
            root_path (str): Base path where new paths will be created under.
            num_paths (int): Number of paths to generate.

        Returns:
            paths (List[str]): A list of paths
        """

        return [f"{root_path}_{i}" for i in range(num_paths)]

    def clone(
        self,
        source_prim_path: str,
        prim_paths: List[str],
        positions: np.ndarray = None,
        orientations: np.ndarray = None,
    ):

        """ Clones a source prim at user-specified destination paths. Clones will 
            be placed at user-specified positions and orientations. 

        Args:
            source_prim_path (str): Path of source object.
            prim_paths (List[str]): List of destination paths.
            positions (np.ndarray): Numpy array containing target positions of clones. Dimension must equal length of prim_paths.
                                    Defaults to None. Clones will be placed at (0, 0, 0) if not specified.
            orientations (np.ndarray): Numpy array containing target orientations of clones. Dimension must equal length of prim_paths.
                                    Defaults to None. Clones will have identity orientation (1, 0, 0, 0) if not specified.
        """

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
