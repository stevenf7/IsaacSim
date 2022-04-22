# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp
import sys
import carb

# The most basic usage for creating a simulation app
kit = SimulationApp()
from omni.isaac.core.utils.statistics import get_memory_stats, get_memory_delta

memory_usage_start = 0
total_frames = 15000
for i in range(total_frames):
    kit.update()
    if i == 1000:
        stats_start = get_memory_stats()
        memory_usage_start = stats_start["Total"]["System Memory"]["value"]
    if i % 1000 == 0:
        stats = get_memory_stats()
        print(i, stats["Total"]["System Memory"]["value"])

stats_end = get_memory_stats()


delta = get_memory_delta(stats_start, stats_end)
delta_usage = delta["Total"]["System Memory"]["value"]

print("memory usage delta: ", delta_usage)
print("memory usage delta per frame: ", delta_usage / total_frames)

# Fail test if we gain more than 1 MB memory usage delta, disable failure state until TC uses 510+ driver
if delta_usage > 1.0:
    # raise (ValueError(f"Memory delta greater than 1.0, actually is {delta_usage}. Memory leak detected!"))
    print(f"Memory delta greater than 1.0, actually is {delta_usage}. Memory leak detected!")

kit.close()  # Cleanup application
