# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.timeline
import omni.graph.core as og


class OgnIsaacSimulationGate:
    """
    Isaac Sim Simulation Gate
    """

    @staticmethod
    def compute(db) -> bool:
        timeline = omni.timeline.acquire_timeline_interface()
        if timeline.is_playing():
            db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        else:
            db.outputs.execOut = og.ExecutionAttributeState.DISABLED
        return True
