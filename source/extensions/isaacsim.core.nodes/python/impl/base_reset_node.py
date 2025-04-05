# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb.events
import omni.usd


class BaseResetNode:
    """
    Base class for nodes that automatically reset when stop is pressed.
    """

    def __init__(self, initialize=False):
        self.initialized = initialize

        timeline = omni.timeline.get_timeline_interface()

        self.timeline_event_sub = timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            int(omni.timeline.TimelineEventType.STOP), self.on_stop_play, name="IsaacSimOGNCoreNodesStageEventHandler"
        )

    def on_stop_play(self, event: carb.events.IEvent):
        self.custom_reset()
        self.initialized = False

    # Defined by subclass
    def custom_reset(self):
        pass

    def reset(self):
        self.timeline_event_sub = None
        self.initialized = None
