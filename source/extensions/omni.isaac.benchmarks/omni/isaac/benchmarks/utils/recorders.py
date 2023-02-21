from typing import Optional
from pathlib import Path
from omni.kit.testing.services.metrics import measurements
from omni.kit.testing.services.datarecorders import frametime, interface
from .collectors import IsaacUpdateFrametimeCollector


class IsaacFrameTimeRecorder(interface.MeasurementDataRecorder):
    def __init__(
        self,
        context: Optional[interface.InputContext] = None,
        root_dir: Optional[Path] = None,
        benchmark_settings: Optional["BenchmarkSettings"] = None,
    ):
        self.context = context
        self.root_dir = root_dir
        self.benchmark_settings = benchmark_settings
        self.frametime_collector = IsaacUpdateFrametimeCollector()

    def start_collecting(self):
        self.frametime_collector.start_collecting()

    def stop_collecting(self):
        self.frametime_collector.stop_collecting()

    def get_num_frames(self):
        return len(self.frametime_collector.render_frametimes_ms)

    async def get_data(self):
        frametime_stats = frametime.FrametimeStats()
        frametime_stats.render_thread_frametime_samples = self.frametime_collector.render_frametimes_ms
        frametime_stats.gpu_frametime_samples = self.frametime_collector.gpu_frametimes_ms
        frametime_stats.calc_stats()

        m1 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Mean Render Thread Frametime",
            value=frametime_stats.mean_render_thread_frametime,
            unit="ms",
        )
        m2 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Mean GPU Frametime", value=frametime_stats.mean_gpu_frametime, unit="ms"
        )
        m3 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Stdev Render Thread Frametime",
            value=frametime_stats.stdev_render_thread_frametime,
            unit="ms",
        )
        m4 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Stdev GPU Frametime", value=frametime_stats.stdev_gpu_frametime, unit="ms"
        )
        m5 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Min Render Thread Frametime",
            value=frametime_stats.min_render_thread_frametime,
            unit="ms",
        )
        m6 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Min GPU Frametime", value=frametime_stats.min_gpu_frametime, unit="ms"
        )
        m7 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Max Render Thread Frametime",
            value=frametime_stats.max_render_thread_frametime,
            unit="ms",
        )
        m8 = measurements.SingleMeasurement(
            name=f"{self.context.phase} Max GPU Frametime", value=frametime_stats.max_gpu_frametime, unit="ms"
        )
        m9 = measurements.ListMeasurement(
            name=f"{self.context.phase} Render Thread Frametime Samples",
            value=frametime_stats.render_thread_frametime_samples,
        )
        m10 = measurements.ListMeasurement(
            name=f"{self.context.phase} GPU Frametime Samples", value=frametime_stats.gpu_frametime_samples
        )
        measurements_out = [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10]
        return interface.MeasurementData(measurements=measurements_out)
