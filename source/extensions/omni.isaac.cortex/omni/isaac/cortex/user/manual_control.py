# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from df import DfAction, DfNetwork
import math_util


class EmptyContext:
    pass


class ManualControl(DfAction):
    pass


def build_behavior(tools):
    behavior = DfNetwork(ManualControl())
    behavior.bind_context(EmptyContext())
    return behavior
