# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni


def set_target_prims(primPath: str, targetPrimPaths: list, inputName: str = "inputs:targetPrim"):
    stage = omni.usd.get_context().get_stage()
    try:
        Node = stage.GetPrimAtPath(primPath)
        input_rel = Node.CreateRelationship(inputName)
        input_rel.SetTargets(targetPrimPaths)
    except Exception as e:
        print(e, primPath)
