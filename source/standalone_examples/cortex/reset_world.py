# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from cortex_object import CortexObject
from df import DfNetwork, DfAction
from dfb import DfToolsContext


def reset_object_poses(objects):
    if objects is not None:
        for name, obj in objects.items():
            obj.post_reset()
            CortexObject(obj).sync_sim()


class ResetWorld(DfAction):
    def enter(self):
        reset_object_poses(self.context.tools.objects)


def build_behavior(tools):
    return DfNetwork(ResetWorld(), context=DfToolsContext(tools))
