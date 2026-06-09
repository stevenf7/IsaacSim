# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Shared JSON, transform, and edge-overlap helpers for cuOpt USD visualizations."""

import json
import math
from typing import Any

import omni.kit.commands
from pxr import Gf, Usd, UsdGeom


# utility for reading json data
def read_json(json_file_path: Any) -> Any:
    """Read visualization sample JSON such as warehouse, graph, order, or vehicle data.

    Args:
        json_file_path: Path to the JSON file to load.

    Returns:
        Parsed JSON content.
    """
    with open(json_file_path) as json_file:
        json_data = json.load(json_file)

    return json_data


# utility for setting prim transform
def translate_rotate_scale_prim(
    stage: Any,
    prim: Any = None,
    prim_path: Any = None,
    translate_set: Any = None,
    rotate_set: Any = None,
    scale_set: Any = None,
    clear_orient: Any = False,
) -> None:
    """Create or update translate, rotateXYZ, and scale xform ops on a USD prim.

    Args:
        stage: Stage containing the prim to transform.
        prim: Prim to transform, if already resolved.
        prim_path: Path to the prim to transform when ``prim`` is not supplied.
        translate_set: Translation value to set, or ``None`` to leave unchanged.
        rotate_set: XYZ rotation value to set, or ``None`` to leave unchanged.
        scale_set: Scale value to set, or ``None`` to leave unchanged.
        clear_orient: Whether to remove an existing orient xform op before setting transforms.
    """
    if prim is not None:
        xform = UsdGeom.Xformable(prim)
        prim_path = prim.GetPrimPath()
    elif prim_path is not None:
        prim = stage.GetPrimAtPath(prim_path)
        xform = UsdGeom.Xformable(prim)
    else:
        return "Need prim or prim path to manipulate"

    xform_ops = {op.GetBaseName(): op for op in xform.GetOrderedXformOps()}

    # verify if the required xform ops exist, create them if not
    if "translate" in xform_ops:
        translate = xform_ops["translate"]
    else:
        translate = xform.AddTranslateOp()

    if "rotateXYZ" in xform_ops:
        rotate = xform_ops["rotateXYZ"]
    else:
        rotate = xform.AddRotateXYZOp()

    if "scale" in xform_ops:
        scale = xform_ops["scale"]
    else:
        scale = xform.AddScaleOp()

    # conditionally remove the orient xform op
    if ("orient" in xform_ops) and clear_orient:
        omni.kit.commands.execute(
            "RemoveXformOp",
            op_order_attr_path=f"{prim_path}.xformOpOrder",
            op_name="xformOp:orient",
            op_order_index=1,
        )

    # set the assigned xform ops
    if translate_set is not None:
        translate.Set(Gf.Vec3d(translate_set))
    if rotate_set is not None:
        rotate.Set(Gf.Vec3d(rotate_set))
    if scale_set is not None:
        scale.Set(Gf.Vec3d(scale_set))


# verify that prim base path exists and create it if not
def check_build_base_path(stage: Any, semantic_path: Any, final_xform: Any = True) -> Any:
    """Ensure each component of a target prim path exists before authoring generated content.

    Args:
        stage: Stage where missing path components are defined.
        semantic_path: Target prim path whose parent hierarchy should exist.
        final_xform: Whether to define the final path component as an Xform.

    Returns:
        None.
    """
    path_components = semantic_path.split("/")
    check_path = ""

    for path_comp in path_components[1:-1]:
        check_path += f"/{path_comp}"
        if not stage.GetPrimAtPath(check_path).IsValid():
            stage.DefinePrim(check_path, "Xform")

    final_base_prim = f"{check_path}/{path_components[-1]}"

    if not stage.GetPrimAtPath(final_base_prim).IsValid():

        if final_xform:
            stage.DefinePrim(final_base_prim, "Xform")
        else:
            stage.DefinePrim(final_base_prim)


# helper utility for get translation value for a prim
def get_prim_translation(prim: Any) -> Any:
    """Return the world-space translation of a waypoint or semantic prim.

    Args:
        prim: Prim whose transform should be evaluated.

    Returns:
        Translation extracted from the prim's local-to-world transform.
    """
    prim_tf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    transform = Gf.Transform()
    transform.SetMatrix(prim_tf)
    prim_translation = transform.GetTranslation()
    return prim_translation


# Check if given edge is within Volume. Return the overlap percentage
def edge_in_volume(edge_prim: Any, vol_prim: Any) -> Any:
    """Test whether a waypoint edge intersects a semantic volume and measure overlap.

    Args:
        edge_prim: Cylinder prim representing a waypoint graph edge.
        vol_prim: Volume prim to test against the edge segment.

    Returns:
        Pair containing whether the edge overlaps the volume and the overlapped length fraction.
    """
    bbox_cache = UsdGeom.BBoxCache(
        time=Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_], useExtentsHint=True
    )
    total_bounds = Gf.BBox3d(bbox_cache.ComputeWorldBound(vol_prim).ComputeAlignedRange())

    prim_tf = UsdGeom.Xformable(edge_prim).ComputeLocalToWorldTransform(Usd.TimeCode())

    p1 = prim_tf.Transform(Gf.Vec3d(0, 0, -1))
    p2 = prim_tf.Transform(Gf.Vec3d(0, 0, 1))

    my_ray = Gf.Ray().SetEnds(p1, p2)

    intersects, d1, d2 = my_ray.Intersect(total_bounds)

    i1 = my_ray.GetPoint(d1)
    i2 = my_ray.GetPoint(d2)

    if not intersects:
        return False, 0.0

    if 0 <= d1 <= 1 and 0 <= d2 <= 1:
        s1 = i1
        s2 = i2
    elif 0 <= d1 <= 1:
        s1 = i1
        s2 = p2
    elif 0 <= d2 <= 1:
        s1 = p1
        s2 = i2
    else:
        return False, 0.0

    line_len = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)
    seg_len = math.sqrt((s2[0] - s1[0]) ** 2 + (s2[1] - s1[1]) ** 2 + (s2[2] - s1[2]) ** 2)

    return True, seg_len / line_len
