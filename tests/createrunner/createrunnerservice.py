# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
See kitrunnerservice for the more general documentation
"""
import os
from typing import Dict

from nv_benchflow.client import Benchmark, Inputs, Types, input, script, service, service_method
from nv_benchflow.client.services import BenchmarkServiceNotFoundException
from nv_benchflow.config import BenchmarkConfig, EnvConfig
from runnerlib import create_runner  # The library
from runnerservice import BaseRunnerService


@script(
    "PYScript Create Runner Service", "1.0", script_type=BenchmarkConfig.Type.Setup, os_type=EnvConfig.OSType.Windows
)
@service("CreateRunner", "1.0", priority=0, tags=None)
@input("tc_build_id", "Teamcity Build ID", Types.Int, default=0, required=False)
@input("local_path", "Local Kit Directory", Types.String, default="", required=False)
@input("build_archive", "Local Kit Archive", Types.String, default="", required=False)
@input("absolute_exe_path", "Absolute EXE Path", Types.String, default="", required=False)
@input("experience_name", "name of the experience", Types.String, default="create", required=False)
@input("timeout", "Kit Timeout", input_type=Types.Int, required=False, default=300)
@input("skip_omnitrace_overlay", "Skip Omnitrace Overlay", input_type=Types.Bool, required=False, default=False)
@input("realtime_output", "Realtime stdout and stderr", input_type=Types.Bool, required=False, default=0)

# If you want to use a specific Kit build and override whatever comes with create, do it here
@input("kit_build_id", "Kit Build ID", input_type=Types.String, required=False)
class CreateRunnerService(BaseRunnerService):

    service_name = "CreateRunnerService"
    app_name = "Create"

    def __init__(self):

        # we store tc_build_id to warn the user prepare() could take a long time
        self._tc_build_id = None if Inputs.tc_build_id == 0 else Inputs.tc_build_id
        self._local_path = None if Inputs.local_path == "" else Inputs.local_path
        self._kit_build_id = None if Inputs.kit_build_id == "" else Inputs.kit_build_id

        if self._tc_build_id:
            Benchmark.log_info(f"Initializing {self.service_name} with Create Teamcity Build ID: {self._tc_build_id}")
        if self._local_path:
            Benchmark.log_info(f"Initializing {self.service_name} with Local Create Directory: {self._local_path}")
        self._build_archive_path = None if Inputs.build_archive == "" else Inputs.build_archive
        self._absolute_exe_path = None if Inputs.absolute_exe_path == "" else Inputs.absolute_exe_path
        self._absolute_exe_path = os.getenv("OVAT_KIT_ARTIFACT", self._absolute_exe_path)
        if self._absolute_exe_path:
            Benchmark.log_info(f"Initializing {self.service_name} with absolute path: {self._absolute_exe_path}")
        self._experience_name = None if Inputs.experience_name == "" else Inputs.experience_name
        if self._experience_name:
            Benchmark.log_info(f"Initializing {self.service_name} with experience name: {self._experience_name}")

        if self._kit_build_id:
            Benchmark.log_info(f"Initializing {self.service_name} with kit build id : {self._kit_build_id}")

        self._k = create_runner.CreateRunner(
            tc_build_id=self._tc_build_id,
            app_root_dir=self._local_path,
            build_extraction_dir=self._build_archive_path,
            app_exe_path=self._absolute_exe_path,
            experience_name=self._experience_name,
            kit_tc_build_id=self._kit_build_id,
        )

    # RPC Service Methods
    @service_method
    def set_exe(self, experience_name: str):
        """
        Args:
            experienceName: some kit based apps take an experience name which is used to load a specific
                            configuration of the app
        """
        if experience_name:
            Benchmark.log_info(f"Overriding {self.service_name} with experience name: {experience_name}")
            self._k.experience_name = experience_name
            self._k._find_exe()


if __name__ == "__main__":
    Benchmark.run()
