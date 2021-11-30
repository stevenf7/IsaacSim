# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp
import sys

# The most basic usage for creating a simulation app
kit = SimulationApp()
from omni.isaac.core.utils.statistics import get_memory_stats

memory_usage_start = 0
total_frames = 10000
for i in range(total_frames):
    kit.update()
    if i == 1000:
        stats = get_memory_stats()
        memory_usage_start = stats["Total"]["System Memory"]["value"]
    if i % 1000 == 0:
        stats = get_memory_stats()
        print(i, stats["Total"]["System Memory"]["value"])

stats = get_memory_stats()
memory_usage_end = stats["Total"]["System Memory"]["value"]
delta = memory_usage_end - memory_usage_start
print("memory usage delta: ", delta)
print("memory usage delta per frame: ", delta / total_frames)

# fail test if we gain more than 1 MB
if delta > 1.0:
    raise (ValueError(f"Memory delta greater than 1.0, actually is {delta}"))
    # sys.exit()

kit.close()  # Cleanup application
