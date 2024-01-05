# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import json
import os
import shutil
import typing
from pathlib import Path
from typing import Optional

import omni.kit.app
import toml

from .. import utils
from ..execution import TestExecutionEnvironmentInterface
from . import measurements

logger = utils.set_up_logging(__name__)


class MetricsBackendInterface:
    def add_metrics(self, test_run: measurements.TestRun) -> None:
        """
        accumulate metrics
        """
        pass

    def finalize(self, filename: str, **kwargs) -> None:
        """
        write the data to file and clear
        """
        pass


class KitGenericTelemetry(MetricsBackendInterface):
    """
    This uses the Kit Telemetry System to store metrics, which end up in Kratos
    """

    def __init__(self) -> None:
        """Manage privacy.toml required for Kit telemetry if running on TeamCity or ETM."""
        config_dir: Path = Path.home() / ".nvidia-omniverse" / "config"
        privacy_toml_path: str = str(config_dir / "privacy.toml")

        # Remove privacy.toml if it exists.
        try:
            shutil.rmtree(config_dir)
            logger.info("Config folder with privacy.toml removed.")
        except Exception:
            logger.info("Config folder empty.")

        # Creates directory for privacy.toml.
        if not os.path.exists(config_dir):
            logger.info(f"Creating dir for privacy.toml {config_dir}.")
            os.makedirs(config_dir)

        # Create privacy.toml.
        logger.info("Creating privacy.toml.")
        data = {
            "privacy": {
                "performance": True,
                "personalization": True,
                "usage": True,
                "userId": "perflab1",
                "extraDiagnosticDataOptIn": "externalBuilds",  # Kit 103
                "nvDiagnosticDataOptIn": "externalBuilds",  # Kit 102
                "eula": {"version": "2.0"},
                "gdpr": {"version": "1.0"},
            }
        }
        with open(privacy_toml_path, "w") as toml_file:
            toml.dump(data, toml_file)

    def add_metrics(self, test_run: measurements.TestRun):
        event_type = ("omni.kit.tests.benchmark@run_benchmark-dev",)
        # TOOD: this needs to be rewritten if we ever want to use it
        omni.kit.app.send_telemetry_event(
            event_type=event_type, duration=0.0, data1="", data2=1, value1=0.0, value2=0.0
        )


class LocalLogMetrics(MetricsBackendInterface):
    """
    Just logger.info to console
    """

    def add_metrics(self, test_run: measurements.TestRun):
        logger.info(f"LocalLogMetricsEvent::add_metrics {test_run}")


class JSONFileMetrics(MetricsBackendInterface):
    """
    Dump to a file at the end of session - just for local validation
    """

    metrics_to_upload_to_teamcity = ["Stage Load Time", "Stage FPS", "Stage DSSIM"]

    def __init__(self, execution_environment: Optional[TestExecutionEnvironmentInterface] = None):
        self._execution_environment = execution_environment
        self.data = []

    def add_metrics(self, test_run: measurements.TestRun) -> None:

        self.data.append(test_run)

        # Lets upload a subset of metrics to our execution environment (e.g TC).
        # In TC this shows up as metadata on the test run
        # This should not be hardcoded though as it is below
        if self._execution_environment:
            exec_metrics = {}
            for m in test_run.measurements:
                measurement = typing.cast(measurements.SingleMeasurement, m)
                if measurement.name in self.metrics_to_upload_to_teamcity:
                    full_name = test_run.test_name + " " + measurement.name
                    exec_metrics[full_name] = measurement.value

            self._execution_environment.add_metrics(test_run.test_name, exec_metrics)

    def finalize(self, filename: str) -> None:
        self._generate_metrics_file(filename)
        self.data.clear()

    def _generate_metrics_file(self, filename) -> None:
        """
        write JSON file for all test runs
        """
        # Append test name to measurement name as OVAT needs to uniquely identify
        for test_run in self.data:
            for m in test_run.measurements:
                m.name = test_run.test_name + " " + m.name

            for m in test_run.metadata:
                m.name = test_run.test_name + " " + m.name

        json_data = json.dumps(self.data, indent=4, cls=measurements.TestRunEncoder)
        with open(filename, "w") as f:
            f.write(json_data)


class MetricsBackend:
    """
    Note the OVATMetrics is handled by a post process that takes the files generated by JSONFileMetricsEvent
    and gathers and updates them
    """

    @classmethod
    def get_instance(
        cls,
        execution_environment: Optional[TestExecutionEnvironmentInterface] = None,
        instance_type: Optional[str] = None,
    ) -> MetricsBackendInterface:
        """Return instance."""
        if instance_type == "KitGenericTelemetry":
            return KitGenericTelemetry()
        elif instance_type == "LocalLogMetrics":
            return LocalLogMetrics()
        elif instance_type == "JSONFileMetrics":
            return JSONFileMetrics()
        else:
            if bool(os.getenv("TEAMCITY_VERSION")) or bool(os.getenv("ETM_ACTIVE")):
                return JSONFileMetrics(execution_environment)
            else:
                return JSONFileMetrics(execution_environment)
