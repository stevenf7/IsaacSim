# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import copy

import omni
import omni.replicator.core as rep
from omni.isaac.core.utils.prims import set_targets
from pxr import Usd


def set_target_prims(primPath: str, targetPrimPaths: list, inputName: str = "inputs:targetPrim"):
    stage = omni.usd.get_context().get_stage()
    try:
        set_targets(stage.GetPrimAtPath(primPath), inputName, targetPrimPaths)
    except Exception as e:
        print(e, primPath)
