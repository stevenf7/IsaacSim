# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pxr import UsdGeom


def recompute_extents(mesh_prim: UsdGeom.Mesh):
    mesh_prim.GetExtentAttr().Set(mesh_prim.ComputeExtent(mesh_prim.GetPointsAttr().Get()))
