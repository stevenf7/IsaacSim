# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from .. import utils

if TYPE_CHECKING:
    from ..settings import BenchmarkSettings

logger = utils.set_up_logging(__name__)


@dataclass
class FrametimeStats:
    render_thread_frametime_samples: List[float] = field(default_factory=list)
    gpu_frametime_samples: List[float] = field(default_factory=list)
    mean_render_thread_frametime: float = 0.00
    mean_gpu_frametime: float = 0.00
    median_render_thread_frametime: float = 0.00
    median_gpu_frametime: float = 0.00
    stdev_render_thread_frametime: float = 0.00
    stdev_gpu_frametime: float = 0.00
    min_render_thread_frametime: float = 0.00
    min_gpu_frametime: float = 0.00
    max_render_thread_frametime: float = 0.00
    max_gpu_frametime: float = 0.00
    fps_legacy: float = 0.00
    frametime_legacy: float = 0.00
    one_percent_high_render_thread_frametime: float = 0.00
    one_percent_high_gpu_frametime: float = 0.00

    def _percentile_inc(self, values: List, percent: float, key=lambda x: x) -> float:
        """
        Find the percentile of a list of values.

        Args:
            values: is a list of values. Note N MUST BE already sorted.
            percent: a float value from 0.0 to 1.0.
            key: optional key function to compute value from each element of N.

        Returns:
            The percentile of the values
        """
        k = (len(values) - 1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(values[int(k)])
        d0 = key(values[int(f)]) * (c - k)
        d1 = key(values[int(c)]) * (k - f)
        return d0 + d1

    def get_one_percent_high(self, values: List) -> float:
        """
        Given a list of floats, return the average of the largest 1% values.

        Args:
            values: A list of floats

        Returns:
            An average of the 1% largest values
        """
        ninety_nine_p = self._percentile_inc(sorted(values), 0.99)
        return statistics.mean([x for x in values if x >= ninety_nine_p])

    def calc_stats(self) -> None:
        try:
            self.mean_render_thread_frametime = round(statistics.mean(self.render_thread_frametime_samples), 2)
            self.median_render_thread_frametime = round(statistics.median(self.render_thread_frametime_samples), 2)
            self.stdev_render_thread_frametime = round(statistics.stdev(self.render_thread_frametime_samples), 2)
            self.min_render_thread_frametime = round(min(self.render_thread_frametime_samples), 2)
            self.max_render_thread_frametime = round(max(self.render_thread_frametime_samples), 2)
            self.one_percent_high_render_thread_frametime = round(
                self.get_one_percent_high(self.render_thread_frametime_samples), 2
            )

            self.mean_gpu_frametime = round(statistics.mean(self.gpu_frametime_samples), 2)
            self.median_gpu_frametime = round(statistics.median(self.gpu_frametime_samples), 2)
            self.stdev_gpu_frametime = round(statistics.stdev(self.gpu_frametime_samples), 2)
            self.min_gpu_frametime = round(min(self.gpu_frametime_samples), 2)
            self.max_gpu_frametime = round(max(self.gpu_frametime_samples), 2)
            self.one_percent_high_gpu_frametime = round(self.get_one_percent_high(self.gpu_frametime_samples), 2)

            self.fps_legacy = round(self.fps_legacy, 2)
            self.frametime_legacy = round(self.frametime_legacy, 2)
        except Exception as e:
            logger.warn(f"Unable to calculate frametime stats: {e}")
