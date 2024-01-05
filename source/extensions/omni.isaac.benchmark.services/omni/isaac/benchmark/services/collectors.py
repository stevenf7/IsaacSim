# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import time
from typing import List, Optional, Tuple

import carb
import omni.kit.test
from omni.hydra.engine.stats import HydraEngineStats


def get_last_gpu_time_ms(
    hydra_engine_stats: HydraEngineStats,
) -> float:
    """
    Return the RTX Renderer duration (in milliseconds) as seen in the profiler window.
    """
    device_nodes = hydra_engine_stats.get_gpu_profiler_result()

    total_time = 0.0

    # jcannon TODO: make this handle multi GPU
    for node in device_nodes[0]:
        # RTX Renderer duration, seems to always be available even if the profiler
        # isn't on... it is always the root node
        if node["indent"] == 0:
            total_time += node["duration"]

    return round(total_time, 6)


class IsaacUpdateFrametimeCollector:
    """
    Utility to collect app update + GPU frame times (in milliseconds)

    The GPU frame time represents the time spent on the GPU itself.
    """

    def __init__(self, usd_context_name="", hydra_engine="rtx") -> None:
        self.hydra_engine_stats = HydraEngineStats(usd_context_name, hydra_engine)
        self.render_frametimes_ms: List[float] = []
        self.gpu_frametimes_ms: List[float] = []

        self.__last_frametime_timestamp_ns = 0
        self.__subscription: Optional[carb.events.ISubscription] = None

    def __update_event_callback(self, event: carb.events.IEvent):
        timestamp_ns = time.perf_counter_ns()
        app_update_time_ms = round((timestamp_ns - self.__last_frametime_timestamp_ns) / 1000 / 1000, 6)
        self.__last_frametime_timestamp_ns = timestamp_ns
        gpu_frametime_ms = get_last_gpu_time_ms(self.hydra_engine_stats)
        # print(app_update_time_ms, gpu_frametime_ms)
        self.render_frametimes_ms.append(app_update_time_ms)
        self.gpu_frametimes_ms.append(gpu_frametime_ms)

    def start_collecting(self):
        # reset our tracking variables
        self.render_frametimes_ms: List[float] = []
        self.gpu_frametimes_ms: List[float] = []
        self.__last_frametime_timestamp_ns = time.perf_counter_ns()

        self.__subscription = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.__update_event_callback)
        )

    def stop_collecting(self) -> Tuple[List[float], List[float]]:
        self.__subscription = None

        # drop the first frame since the interval approach doesn't work for
        # the render frame
        self.render_frametimes_ms.pop(0)
        self.gpu_frametimes_ms.pop(0)

        return self.render_frametimes_ms, self.gpu_frametimes_ms
