import platform
from pathlib import Path
from typing import Optional

from omni.kit.testing.services.datarecorders import cpu, frametime, interface, memory
from omni.kit.testing.services.metrics import measurements

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


class IsaacMemoryRecorder(memory.MemoryRecorder):
    def __init__(
        self,
        context: Optional[interface.InputContext] = None,
        root_dir: Optional[Path] = None,
        benchmark_settings: Optional["BenchmarkSettings"] = None,
    ):
        self.context = context
        self.root_dir = root_dir
        self.benchmark_settings = benchmark_settings
        super().__init__(context, root_dir, benchmark_settings)

    async def get_data(self) -> interface.MeasurementData:

        (
            cpu_load,
            rss,
            vms,
            uss,
            pb,
            tracked_gpu_memory,
            dedicated_gpu_memory,
        ) = self.get_hardware_stats()

        m1 = measurements.SingleMeasurement(name=f"{self.context.phase} System Memory RSS", value=rss, unit="GB")
        m2 = measurements.SingleMeasurement(name=f"{self.context.phase} System Memory VMS", value=vms, unit="GB")
        m3 = measurements.SingleMeasurement(name=f"{self.context.phase} System Memory USS", value=uss, unit="GB")
        m4 = measurements.SingleMeasurement(
            name=f"{self.context.phase} GPU Memory Tracked", value=tracked_gpu_memory, unit="GB"
        )
        m5 = measurements.SingleMeasurement(
            name=f"{self.context.phase} GPU Memory Dedicated", value=dedicated_gpu_memory, unit="GB"
        )
        measurements_out = [m1, m2, m3, m4, m5]

        # Only capture System Memory PB for Windows.
        # if platform.system() == "Windows":
        #     measurements_out.append(
        #         measurements.SingleMeasurement(name=f"{self.context.phase} System Memory PB", value=pb, unit="GB")
        #     )

        return interface.MeasurementData(measurements=measurements_out)


class IsaacCPUStatsRecorder(cpu.CPUStatsRecorder):
    def __init__(
        self,
        context: Optional[interface.InputContext] = None,
        root_dir: Optional[Path] = None,
        benchmark_settings: Optional["BenchmarkSettings"] = None,
    ):
        self.context = context
        self.root_dir = root_dir
        self.benchmark_settings = benchmark_settings
        super().__init__(context, root_dir, benchmark_settings)

    async def get_data(self) -> interface.MeasurementData:

        (
            cpu_iowait_pct,
            cpu_system_pct,
            cpu_user_pct,
            cpu_idle_pct,
        ) = cpu.get_cpu_usage_in_pct(self.cpu_iowait, self.cpu_system, self.cpu_user, self.cpu_idle)

        m1 = measurements.SingleMeasurement(
            name=f"{self.context.phase} System CPU iowait", value=cpu_iowait_pct, unit="%"
        )
        m2 = measurements.SingleMeasurement(
            name=f"{self.context.phase} System CPU system", value=cpu_system_pct, unit="%"
        )
        m3 = measurements.SingleMeasurement(name=f"{self.context.phase} System CPU user", value=cpu_user_pct, unit="%")
        m4 = measurements.SingleMeasurement(name=f"{self.context.phase} System CPU idle", value=cpu_idle_pct, unit="%")

        return interface.MeasurementData(measurements=[m1, m2, m3, m4])
