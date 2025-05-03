# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import carb
import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # Enable the developer throttling settings when extension starts
        carb.settings.get_settings().set("/app/show_developer_preference_section", True)

        timeline = omni.timeline.get_timeline_interface()
        self.timeline_event_sub = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self.on_stop_play, name="IsaacSimThrottlingEventHandler"
        )
        pass

    def on_stop_play(self, event: carb.events.IEvent):
        # Enable eco mode if playing sim, disable if stopped
        # Disable legacy gizmos during runtime
        _settings = carb.settings.get_settings()
        if event.type == int(omni.timeline.TimelineEventType.PLAY):
            _settings.set("/rtx/ecoMode/enabled", False)
            _settings.set("/exts/omni.kit.hydra_texture/gizmos/enabled", False)
        elif event.type == int(omni.timeline.TimelineEventType.STOP):
            _settings.set("/rtx/ecoMode/enabled", True)
            _settings.set("/exts/omni.kit.hydra_texture/gizmos/enabled", True)
        pass

    def on_shutdown(self):
        self.timeline_event_sub = None
        pass
