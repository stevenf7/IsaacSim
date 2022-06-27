# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp
import carb

# The most basic usage for creating a simulation app
kit = SimulationApp()

from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.carb import set_carb_setting

# set logging settings before we enable extension
settings = carb.settings.get_settings()
set_carb_setting(settings, "/exts/omni.isaac.statistics_logging/logMode", "frames")
set_carb_setting(settings, "/exts/omni.isaac.statistics_logging/logEveryNFrames", 5000)


# warm up
for i in range(100):
    kit.update()

# start logging
enable_extension("omni.isaac.statistics_logging")

from omni.isaac.statistics_logging.statistics import summarize_statistics_log, plot_statistics_log

total_frames = 15001  # log 3 sets of data
for i in range(total_frames):
    kit.update()

log_file_path = carb.tokens.get_tokens_interface().resolve("${logs}") + "/isaac_statistics/log.yaml"

kit.close()  # Cleanup application

summarize_statistics_log(log_file_path)
plot_statistics_log(log_file_path)
