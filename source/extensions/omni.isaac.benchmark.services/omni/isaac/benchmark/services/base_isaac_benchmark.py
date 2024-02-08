# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import os
import tempfile
import time
from pathlib import Path

import carb
from omni.isaac.benchmark.services import execution, settings, utils
from omni.isaac.benchmark.services.datarecorders import interface
from omni.isaac.benchmark.services.metrics import backend, measurements
from omni.isaac.core.utils.stage import open_stage
from omni.isaac.nucleus import get_assets_root_path

from .recorders import *
from .utils import wait_until_stage_is_fully_loaded

logger = utils.set_up_logging(__name__)


# Sync mode sets settings that blocks the app until all materials are fully loaded
def set_sync_mode():
    carb_settings = carb.settings.get_settings()
    if carb_settings.get("/app/asyncRendering"):
        carb.log_warn("Async rendering is enabled, setting sync mode might not work")
    carb_settings.set("/omni.kit.plugin/syncUsdLoads", True)
    carb_settings.set("/rtx-defaults/materialDb/syncLoads", True)
    carb_settings.set("/rtx-defaults/hydra/materialSyncLoads", True)


class BaseIsaacBenchmark:
    def __init__(self, benchmark_name: str = "BaseIsaacBenchmark"):
        self._execution_env = execution.TestExecutionEnvironment.get_instance()

        self.settings = carb.settings.get_settings()
        prefix = self._get_output_file_prefix(benchmark_name)
        version, _, _ = utils.get_kit_version_branch()

        self.assets_root_path = get_assets_root_path()
        if self.assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.context = interface.InputContext(
            artifact_prefix=prefix,
            kit_version=version,
            phase="benchmark",
            sync_mode=self._get_sync_mode(),
        )

        self.frametime_recorder = IsaacFrameTimeRecorder(self.context)
        self.runtime_recorder = IsaacRuntimeRecorder(self.context)
        self.recorders = [
            IsaacMemoryRecorder(self.context),
            IsaacCPUStatsRecorder(self.context),
            self.frametime_recorder,
            self.runtime_recorder,
        ]
        self.test_run = measurements.TestRun(
            benchmark_name
        )  # the name is set by the test itself, set it to a default here.

        logger.info(f"Execution type = {type(self._execution_env).__name__}")
        self._metrics_output_folder = self.settings.get(
            "/exts/omni.isaac.benchmark.services/metrics/metrics_output_folder"
        )

        if not self._metrics_output_folder:
            self._metrics_output_folder = tempfile.gettempdir()

        logger.info(f"Local folder location = {self._metrics_output_folder}")
        logger.info("Starting")
        self.benchmark_start_time = time.time()
        self.test_mode = os.getenv("ISAAC_TEST_MODE") == "1"
        logger.info(f"Test mode = {'true' if self.test_mode else 'false'}")
        pass

    def stop(self):
        logger.info("Stopping")
        logger.info("Writing metrics data.")

        if not os.path.exists(self._metrics_output_folder):
            os.mkdir(path=self._metrics_output_folder)
        if self.settings.get("/exts/omni.isaac.benchmark.services/metrics/randomize_filename_prefix"):
            fd, metrics_filename_out = tempfile.mkstemp(
                dir=self._metrics_output_folder, prefix=f"metrics_{self.test_run.test_name}", suffix=".json"
            )
        else:
            metrics_filename_out = Path(self._metrics_output_folder) / f"metrics_{self.test_run.test_name}.json"
        _metrics = backend.MetricsBackend.get_instance(self._execution_env)
        logger.info(f"Metrics type = {type(_metrics).__name__}")
        _metrics.add_metrics(self.test_run)
        _metrics.finalize(metrics_filename_out)
        logger.info(f"Writing metrics data to {metrics_filename_out}")

        if self.settings.get("/exts/omni.isaac.benchmark.services/metrics/generate_osmo_kpi_output"):
            osmo_metrics_filename_out = Path(self._metrics_output_folder) / f"kpis_{self.test_run.test_name}.json"
            _osmo_metrics = backend.MetricsBackend.get_instance(instance_type="OsmoKPIFile")
            logger.info(f"Metrics type = {type(_osmo_metrics).__name__}")
            _osmo_metrics.add_metrics(self.test_run)
            _osmo_metrics.finalize(osmo_metrics_filename_out)
            logger.info(f"Writing metrics data to {osmo_metrics_filename_out}")

        self.test_run = None
        self.recorders = None
        self.context = None
        pass

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

    def start_runtime(self):
        self.runtime_recorder.start_time()

    def stop_runtime(self):
        self.runtime_recorder.stop_time()

    def store_measurements(self):
        run_measurements = []
        run_metadata = []
        run_artifacts = []
        for m in self.recorders:
            data = m.get_data()
            run_measurements.extend(data.measurements)
            run_metadata.extend(data.metadata)
            run_artifacts.extend(data.artefacts)
        self.test_run.measurements.extend(run_measurements)
        self.test_run.metadata.extend(run_metadata)

    def fully_load_stage(self, usd_path):
        open_stage(usd_path)
        wait_until_stage_is_fully_loaded()
