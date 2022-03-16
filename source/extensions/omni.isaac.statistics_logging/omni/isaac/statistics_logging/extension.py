# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import sys
import os
import carb.settings
import carb.tokens
import omni
from omni.isaac.core.utils.statistics import get_memory_stats


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        # printing all settings for illustrative purposes
        settings = carb.settings.get_settings()
        carb.log_warn(f'{settings.get("/exts/omni.isaac.statistics_logging/resetLogOnStart")}')
        carb.log_warn(f'{settings.get("/exts/omni.isaac.statistics_logging/logFilePath")}')
        carb.log_warn(f'{settings.get("/exts/omni.isaac.statistics_logging/logMode")}')
        carb.log_warn(f'{settings.get("/exts/omni.isaac.statistics_logging/logEveryNSeconds")}')
        carb.log_warn(f'{settings.get("/exts/omni.isaac.statistics_logging/logEveryNFrames")}')

        # get the path to the log file
        log_file_path = settings.get("/exts/omni.isaac.statistics_logging/logFilePath")
        # the file is blank, locate default log directory
        if log_file_path == "":
            log_file_path = carb.tokens.get_tokens_interface().resolve("${logs}") + "/isaac_statistics_log.yaml"

        carb.log_warn(f"log_file_path: {log_file_path}")

        self._update_event_subscription = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update_event)
        )
        # dummy counter
        self._counter = 0
        pass

    def on_shutdown(self):
        # do any cleanup here
        self._update_event_subscription = None
        pass

    def _on_update_event(self, delta):
        # check if N frames or N seconds have passed here
        if self._counter % 100 == 0:
            carb.log_warn("N Frames have passed")
        self._counter += 1
        pass
