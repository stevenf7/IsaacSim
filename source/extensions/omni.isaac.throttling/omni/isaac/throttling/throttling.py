# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import carb
import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # Enable the developer throttling settings when extension starts
        carb.settings.get_settings().set("/app/show_developer_preference_section", True)
        pass

    def on_stop_play(self, event: carb.events.IEvent):
        pass

    def on_shutdown(self):
        pass
