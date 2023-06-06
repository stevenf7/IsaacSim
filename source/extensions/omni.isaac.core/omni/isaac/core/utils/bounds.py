# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import typing

# omniverse
import carb
import numpy as np

# isaacsim
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import Gf, Usd, UsdGeom


def recompute_extents(
    prim: UsdGeom.Boundable, time: Usd.TimeCode = Usd.TimeCode.Default(), include_children: bool = False
) -> None:
    """Recomputes and overwrites the extents attribute for a UsdGeom.Boundable prim

    Args:
        prim (UsdGeom.Boundable): Input prim to recompute extents for
        time (Usd.TimeCode, optional): timecode to use for computing extents. Defaults to Usd.TimeCode.Default().
        include_children (bool, optional): include children of specified prim in calculation. Defaults to False.

    Raises:
        ValueError: If prim is not of UsdGeom.Boundable type
    """
    #
    def update_extents(prim: UsdGeom.Boundable, time: Usd.TimeCode = Usd.TimeCode.Default()):
        compute_prim = UsdGeom.Boundable(prim)
        if compute_prim:
            bounds = []
            mesh = UsdGeom.Mesh(compute_prim)
            if mesh:
                bounds = mesh.ComputeExtent(mesh.GetPointsAttr().Get())
            else:
                bounds = UsdGeom.Boundable.ComputeExtentFromPlugins(compute_prim, time)

            if compute_prim.GetExtentAttr().HasValue():
                compute_prim.GetExtentAttr().Set(bounds)
            else:
                compute_prim.CreateExtentAttr(bounds)
        else:
            raise ValueError(f"Input prim is not of type UsdGeom.Boundable, is instead {type(prim)}")

    if include_children:
        for p in Usd.PrimRange(prim.GetPrim()):
            try:
                update_extents(p, time)
            except ValueError:
                carb.log_info(f"Skipping {p}, not boundable")
    else:
        update_extents(prim, time)


def create_bbox_cache(time: Usd.TimeCode = Usd.TimeCode.Default(), use_extents_hint: bool = True) -> UsdGeom.BBoxCache:
    """Helper function to create a Bounding Box Cache object that can be used for computations

    Args:
        time (Usd.TimeCode, optional): time at which cache should be initialized. Defaults to Usd.TimeCode.Default().
        use_extents_hint (bool, optional): Use existing extents attribute on prim to compute bounding box. Defaults to True.

    Returns:
        UsdGeom.BboxCache: Initialized bbox cache
    """
    return UsdGeom.BBoxCache(time=time, includedPurposes=[UsdGeom.Tokens.default_], useExtentsHint=use_extents_hint)


def compute_aabb(bbox_cache: UsdGeom.BBoxCache, prim_path: str, include_children: bool = False) -> np.array:
    """Compute an AABB for a given prim_path, a combined AABB is computed if include_children is True

    Args:
        bbox_cache (UsdGeom.BboxCache): Existing Bounding box cache to use for computation
        prim_path (str): prim path to compute AABB for
        include_children (bool, optional): include children of specified prim in calculation. Defaults to False.

    Returns:
        np.array: Bounding box for this prim, [min x, min y, min z, max x, max y, max z]
    """
    total_bounds = Gf.BBox3d()
    prim = get_prim_at_path(prim_path)
    if include_children:
        for p in Usd.PrimRange(prim):
            total_bounds = Gf.BBox3d.Combine(
                total_bounds, Gf.BBox3d(bbox_cache.ComputeWorldBound(p).ComputeAlignedRange())
            )
    else:
        total_bounds = Gf.BBox3d(bbox_cache.ComputeWorldBound(prim).ComputeAlignedRange())

    range = total_bounds.GetRange()
    return np.array([*range.GetMin(), *range.GetMax()])


def compute_combined_aabb(bbox_cache: UsdGeom.BBoxCache, prim_paths: typing.List[str]) -> np.array:
    """Computes a combined AABB given a list of prim paths

    Args:
        bbox_cache (UsdGeom.BboxCache): Existing Bounding box cache to use for computation
        prim_paths (typing.List[str]): List of prim paths to compute combined AABB for

    Returns:
        np.array: Bounding box for input prims, [min x, min y, min z, max x, max y, max z]
    """
    total_bounds = Gf.BBox3d()
    for prim_path in prim_paths:
        prim = get_prim_at_path(prim_path)
        bounds = bbox_cache.ComputeWorldBound(prim)
        total_bounds = Gf.BBox3d.Combine(total_bounds, Gf.BBox3d(bounds.ComputeAlignedRange()))
    range = total_bounds.GetRange()
    return np.array([*range.GetMin(), *range.GetMax()])


def compute_obb(bbox_cache: UsdGeom.BBoxCache, prim_path: str) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Computes the Oriented Bounding Box (OBB) of a prim

    Args:
        bbox_cache (UsdGeom.BBoxCache): USD Bounding Box Cache object to use for computation
        prim_path (str): Prim path to compute OBB for

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing the following OBB information:
            - The centroid of the OBB as a NumPy array.
            - The axes of the OBB as a 2D NumPy array, where each row represents a different axis.
            - The half extent of the OBB as a NumPy array.

    # NOTE: The rotation matrix incorporates any scale factors applied to the object.
    # The `half_extent` values do not include these scaling effects.

    """
    # Compute the BBox3d for the prim
    prim = get_prim_at_path(prim_path)
    bound = bbox_cache.ComputeWorldBound(prim)

    # Compute the translated centroid of the world bound
    centroid = bound.ComputeCentroid()

    # Compute the axis vectors of the OBB
    # NOTE: The rotation matrix incorporates the scale factors applied to the object
    rotation_matrix = bound.GetMatrix().ExtractRotationMatrix()
    x_axis = rotation_matrix.GetRow(0)
    y_axis = rotation_matrix.GetRow(1)
    z_axis = rotation_matrix.GetRow(2)

    # Compute the half-lengths of the OBB along each axis
    # NOTE the size/extent values do not include any scaling effects
    half_extent = bound.GetRange().GetSize() * 0.5

    return np.array([*centroid]), np.array([[*x_axis], [*y_axis], [*z_axis]]), np.array(half_extent)


def compute_obb_corners(bbox_cache: UsdGeom.BBoxCache, prim_path: str) -> np.ndarray:
    """Computes the corners of the Oriented Bounding Box (OBB) of a prim

    Args:
        bbox_cache (UsdGeom.BBoxCache): Bounding Box Cache object to use for computation
        prim_path (str): Prim path to compute OBB for

    Returns:
        np.ndarray: NumPy array of shape (8, 3) containing each corner location of the OBB
    """
    centroid, axis, half_extent = compute_obb(bbox_cache, prim_path)
    corners = [
        centroid - axis[0] * half_extent[0] - axis[1] * half_extent[1] - axis[2] * half_extent[2],
        centroid - axis[0] * half_extent[0] - axis[1] * half_extent[1] + axis[2] * half_extent[2],
        centroid - axis[0] * half_extent[0] + axis[1] * half_extent[1] - axis[2] * half_extent[2],
        centroid - axis[0] * half_extent[0] + axis[1] * half_extent[1] + axis[2] * half_extent[2],
        centroid + axis[0] * half_extent[0] - axis[1] * half_extent[1] - axis[2] * half_extent[2],
        centroid + axis[0] * half_extent[0] - axis[1] * half_extent[1] + axis[2] * half_extent[2],
        centroid + axis[0] * half_extent[0] + axis[1] * half_extent[1] - axis[2] * half_extent[2],
        centroid + axis[0] * half_extent[0] + axis[1] * half_extent[1] + axis[2] * half_extent[2],
    ]
    return np.array(corners)
