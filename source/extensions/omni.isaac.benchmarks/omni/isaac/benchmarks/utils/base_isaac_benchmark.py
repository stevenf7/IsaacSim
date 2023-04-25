# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import json
import os
import tempfile
import time
from pathlib import Path

import carb
import omni.kit.test
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import is_stage_loading, open_stage_async
from omni.kit.testing.services import execution, settings, utils
from omni.kit.testing.services.datarecorders import cpu, interface, memory
from omni.kit.testing.services.metrics import backend, measurements
from omni.kit.widget.viewport.capture import FileCapture

from .recorders import IsaacFrameTimeRecorder

logger = utils.set_up_logging(__name__)


class BaseIsaacBenchmark(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self.assets_root_path = get_assets_root_path()
        if self.assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        self.settings = carb.settings.get_settings()
        try:
            from omni.kit.testing.metrics_uploader.extension import MetricsUploaderExtension

            self.uploader_instance = MetricsUploaderExtension().get_instance()
        except:
            self.uploader_instance = None
        await omni.usd.get_context().new_stage_async()
        for _ in range(100):
            await omni.kit.app.get_app().next_update_async()

        self._execution_env = execution.TestExecutionEnvironment.get_instance()

        self.nvdataflow_server_url = self._get_nvdataflow_server_url()

        prefix = self._get_output_file_prefix(self._testMethodName)
        version, _, _ = utils.get_kit_version_branch()

        self.context = interface.InputContext(
            artifact_prefix=prefix,
            kit_version=version,
            phase="benchmark",
            nvdataflow_server_url=self.nvdataflow_server_url,
            sync_mode=self._get_sync_mode(),
        )

        self.frametime_recorder = IsaacFrameTimeRecorder(self.context)
        self.recorders = [
            # scene.SceneStatsRecorder(self.context), # This crashes on new stage.
            cpu.CPUStatsRecorder(self.context),
            memory.MemoryRecorder(self.context),
            # memory.GPUDetailedMemoryStatsRecorder(self.context), # This is causing a crash on new stage
            self.frametime_recorder,
        ]
        self.test_run = measurements.TestRun(
            "BaseIsaacBenchmark"
        )  # the name is set by the test itself, set it to a default here.

        logger.info(f"Execution type = {type(self._execution_env).__name__}")
        if self.uploader_instance:
            self._metrics_output_folder = self.uploader_instance.metrics_output
        else:
            self._metrics_output_folder = tempfile.gettempdir()

        self.outputs_dir: Path = Path(tempfile.gettempdir()) / "isaac_sim_benchmark_outputs"

        logger.info(f"Local folder location = {self.outputs_dir}")
        logger.info(f"Starting")
        self.benchmark_start_time = time.time()
        pass

    async def tearDown(self):
        logger.info(f"Stopping")
        while is_stage_loading():
            print("asset still loading, waiting to finish")
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        logger.info("Writing metrics data.")

        if not os.path.exists(self._metrics_output_folder):
            os.mkdir(path=self._metrics_output_folder)
        fd, metrics_filename_out = tempfile.mkstemp(
            dir=self._metrics_output_folder, prefix=f"metrics_{self.test_run.test_name}", suffix=".json"
        )
        _metrics = backend.MetricsBackend.get_instance(self._execution_env)
        logger.info(f"Metrics type = {type(_metrics).__name__}")
        _metrics.add_metrics(self.test_run)
        _metrics.finalize(metrics_filename_out)
        logger.info(f"Writing metrics data to {metrics_filename_out}")

        # Create metadata.json to store NVDF destination settings (only need to do this once per session)
        metrics_metadata_filename_out = os.path.join(self._metrics_output_folder, "metadata.json")
        if not os.path.exists(metrics_metadata_filename_out):
            nvdataflow_test_suite_name = self.settings.get(
                "/exts/omni.isaac.benchmarks/metrics/nvdataflow_default_test_suite_name"
            )
            if not nvdataflow_test_suite_name:
                exit()
            # This is the same directory that datarecorders.profiler.CarbTracingProfiler creates/uses
            # This metatata write and the eventual upload of the carb trace data digest to NVDF should
            # be factored into that datarecorder somehow
            trace_dir: Path = self.outputs_dir / "traces"

            with open(metrics_metadata_filename_out, "w") as fw:
                json.dump(
                    {
                        "nvdataflow_test_suite_name": nvdataflow_test_suite_name,
                        "start_time": self.benchmark_start_time,
                        "nvdataflow_server_url": self.nvdataflow_server_url,
                        "chrometrace_dir": str(trace_dir),
                    },
                    fw,
                )
        logger.info(f"Writing metrics metadata to {metrics_metadata_filename_out}")
        await omni.kit.app.get_app().next_update_async()
        self.test_run = None
        self.recorders = None
        self.context = None
        pass

    def _get_nvdataflow_server_url(self) -> str:
        """upload metrics to nvdf only if either TC/ETM execution, or forced via env-var override (see TESTING.md)"""
        nvdataflow_server_url = os.getenv("EXTS_OMNI_KIT_TESTS_BENCHMARK_METRICS_NVDATAFLOW_METRICS_PUBLISH_URL")
        etm_active = not isinstance(self._execution_env, execution.LocalExecutionEnvironment)
        if etm_active:
            if not nvdataflow_server_url:
                nvdataflow_server_url = self.settings.get(
                    "/exts/omni.kit.tests.benchmark/metrics/nvdataflow_metrics_publish_url"
                )
        return nvdataflow_server_url or ""

    def _get_output_file_name(self, setting: settings.BenchmarkSettings, filename: str) -> str:
        version, _, _ = utils.get_kit_version_branch()
        resolution = self.get_setting_resolution(setting.image_width, setting.image_height)
        return f"{setting.test_name}_{version}_{resolution}_{filename}"

    def _get_output_file_prefix(self, test_name) -> str:
        """
        uniquefies artifact file names (so e.g if we support multiple resolutions they are included in the name
        """
        version, _, _ = utils.get_kit_version_branch()
        return f"{test_name}_{version}"

    def _get_sync_mode(self) -> utils.SyncMode:
        """Checks if we are in sync mode."""
        async_rendering = self.settings.get("/app/asyncRendering")
        usd_sync_loads = self.settings.get("/omni.kit.plugin/syncUsdLoads")

        # On Viewport 2.0 the `rtx` settings are now under `rtx-defaults`.
        materialdb_sync_loads = self.settings.get("/rtx/materialDb/syncLoads")
        if materialdb_sync_loads is None:
            materialdb_sync_loads = self.settings.get("/rtx-defaults/materialDb/syncLoads")

        hydra_material_sync_loads = self.settings.get("/rtx/hydra/materialSyncLoads")
        if hydra_material_sync_loads is None:
            hydra_material_sync_loads = self.settings.get("/rtx-defaults/hydra/materialSyncLoads")

        if not async_rendering and materialdb_sync_loads and usd_sync_loads and hydra_material_sync_loads:
            return utils.SyncMode.SYNC
        elif async_rendering and not materialdb_sync_loads and not usd_sync_loads and not hydra_material_sync_loads:
            return utils.SyncMode.ASYNC

        logger.info(
            f"ambiguous combination of async/sync flags {async_rendering} {materialdb_sync_loads} {usd_sync_loads} {hydra_material_sync_loads}"
        )
        return utils.SyncMode.AMBIGUOUS

    def set_phase(self, phase):
        logger.info(f"Starting phase: {phase}")
        self.context.phase = phase

    def start_collecting_frametime(self):
        self.frametime_recorder.start_collecting()

    def stop_collecting_frametime(self):
        self.frametime_recorder.stop_collecting()

    def get_num_frames(self):
        return self.frametime_recorder.get_num_frames()

    async def store_measurements(self):
        run_measurements = []
        run_metadata = []
        run_artifacts = []
        for m in self.recorders:
            data = await m.get_data()
            run_measurements.extend(data.measurements)
            run_metadata.extend(data.metadata)
            run_artifacts.extend(data.artefacts)
        self.test_run.measurements.extend(run_measurements)
        self.test_run.metadata.extend(run_metadata)

    async def fully_load_stage(self, usd_path, loop_frames=120):

        await open_stage_async(usd_path)

        while is_stage_loading():
            logger.info("asset still loading, waiting to finish")
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        for _ in range(loop_frames):
            await omni.kit.app.get_app().next_update_async()

    # TODO, use datarecorders.ImageComparison
    # async def capture_image(self):
    #     viewport_names = get_viewport_names()
    #     for v in range(get_num_viewports()):
    #         image_path = data_dir + "/snapshot_" + str(v)
    #         viewport_window = get_viewport_from_window_name(window_name=viewport_names[v])
    #         capture = viewport_window.schedule_capture(FileCapture(image_path))
    #         captured_aovs = await capture.wait_for_result()
    #         if captured_aovs:
    #             print(f'AOV "{captured_aovs[0]}" was written to "{image_path}"')
    #         else:
    #             print(f'No image was written to "{image_path}"')
