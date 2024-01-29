# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
The Kit Runner Service is the main interface to Omniverse Kit within OVAT Tests. It is responsible
for acquiring, launching and configuring a Kit build. Acquisition comes from Teamcity, or a local
filesystem path can be provided.

It is largely a wrapper around the [Kit Runner](https://gitlab-master.nvidia.com/ovat/libraries/kit-runner)
Python library.

The reason the Kit Runner Service exists (as opposed to just including the kit_runner library
directly) is to provide a standardized Inputs interface (Teamcity Build ID is always called the
same for every script that uses this service), as well as to take care of some convenience code
for the test developer.

For example, the service automatically adds the latest `omniverse-kit.log` to the Task Outputs,
as well as Kit's stdout and stderr contents. Also, it will automatically configure Kit for the
MQTT Synchronizer library if the service is part of the task definition.

## Declaring Kit Runner Service in Task Definition YAMLs
In order to use the Kit Runner Service you must declare it as a component in your Task Definition
YAMLs.

These can be either GCN YAMLs (development) or Task Architect YAMLs (for production).

### GCN YAML (Local Development)

`gcn.yml`
```yaml
## KIT RUNNER SERVICE
- component: kit
  entrypoint_script:
    name: PYScript Kit Runner Service
    # The numeric ID is a GTL Build ID. You can find the list for Kit Runner Service at:
    # https://gtl-ui.nvidia.com/application/29421#builds
    origin: gtl://build/5082194
  entrypoint_type: setup
  inputs:
    Teamcity Build ID: 5548724
    # Local Kit Directory: /home/OVAT/kit
```

### Task Architect YAML (Deployment)

#### Task Architect (Production)
`task_architect.yml`
```yaml
add:
  component: kit_runner
  app: PYScript Kit Runner Service
  branch: master
  # The version is a GTL build version. You can find the list for Kit Runner Service at:
  # https://gtl-ui.nvidia.com/application/29421#builds
  version: 1.0.33
inputs:
#  Local Kit Directory: "D:\\kit_devel\\kit"
  Teamcity Build ID: 5548724
```

#### Task Architect (Bleeding Edge)
`task_architect_dev.yml`
```yaml
add:
  component: kit_runner
  app: PYScript Kit Runner Service
  branch: dev
inputs:
#  Local Kit Directory: "D:\\kit_devel\\kit"
  Teamcity Build ID: 5548724
```

### Special Cases

#### Developing The Runner
`gcn_dev.yml`
```yaml
## KIT RUNNER SERVICE
- component: kit
  debug_info:
    environment:
      environment_type: python
      config:
        python_version: 3.7
    entrypoint_path: kitrunnerservice.py
  entrypoint_script:
    origin: ../../services/kit-runner-service/src  # must point to a valid relative location
  entrypoint_type: setup
  # Uncomment Local Kit Directory and comment Teamcity Build ID  to work with local paths
  inputs:
    Teamcity Build ID: 5548724
#    Local Kit Directory: c:\\Work\\NVIDIA\\_kit\\kit-2020.2.5896-5805e31a-release
```

## Using The Service In A Test

In order to use the Kit Runner Service in a Python Benchflow script, you must acquire a handle with the
regular `find_service()` method.

```python
# The KitRunner service must be defined in your task_architect / gcn_dev
# YAML files in order for it to be available
kit_runner = Benchmark.services.find_service("KitRunner", "1.0")
# This either downloads Kit from Teamcity or just configures all the paths
kit_runner.prepare()

# launches Kit in a blocking manner until it exits or 60 seconds elapses
kit_runner.run_kit(timeout=60)
```

After calling `prepare()`, the full functionality of the methods below are available.

## Declared Inputs
The following inputs are declared by this service:

1. `Teamcity Build ID` (type: `int`, optional)

    The numeric Teamcity Build ID of an artifact-generating Kit build. This can be found by looking at the URL of
    a specific Teamcity Kit Build.

    If not provided, and no `Local Kit Directory` is provided, the default is to download the latest `master` build.

    Example: `5548724`

2. `Local Kit Directory` (type: `str`, optional)

    A valid path to a Kit directory on the local filesystem. This is the directory which contains the `_build`
    sub-directory.

    Example: `"D:\\kit_devel\\kit"`

3. `Kit Timeout` (type: `int`, optional)

    The default amount of seconds to wait for a Kit execution before killing it. Defaults to 300.

    Can be declared for every execution with the `timeout=` parameter to `run_kit`

    Example: `60`

4. `Absolute EXE Path` (type: `str`, optional)

    A valid path to a Kit executable. If set, overrides all other locators for Kit.

    This can be overridden in the `OVAT_KIT_ARTIFACT` environment variable.

    This lets you modify which Kit is used without adjusting any YAMLs or inputs.

    Example: `"C:\\Work\\NVIDIA\\_kit\\_build\\windows-x86_64\\release\\omniverse-kit.exe"`

"""
import os

from kit_runner import KitRunner
from nv_benchflow.client import Benchmark, Inputs, Types, input, script, service
from nv_benchflow.config import BenchmarkConfig, EnvConfig
from runnerservice import BaseRunnerService


@script("PYScript Kit Runner Service", "1.0", script_type=BenchmarkConfig.Type.Setup, os_type=EnvConfig.OSType.Windows)
@service("KitRunner", "1.0", priority=0, tags=None)
@input("tc_build_id", "Teamcity Build ID", Types.Int, default=0, required=False)
@input("local_path", "Local Kit Directory", Types.String, default="", required=False)
@input("build_archive", "Local Kit Archive", Types.String, default="", required=False)
@input("absolute_exe_path", "Absolute EXE Path", Types.String, default="", required=False)
@input("timeout", "Kit Timeout", input_type=Types.Int, required=False, default=300)
@input("skip_omnitrace_overlay", "Skip Omnitrace Overlay", input_type=Types.Bool, required=False, default=False)
class KitRunnerService(BaseRunnerService):
    """
    Note, you will never create an instance of this class directly. You must use
    Benchflow's `find_service()` call to get a reference, please refer to the documentation
    above.
    """

    service_name = "KitRunnerService"
    app_name = "Kit"

    def __init__(self):
        # we store tc_build_id to warn the user prepare() could take a long time
        self._tc_build_id = None if Inputs.tc_build_id == 0 else Inputs.tc_build_id
        local_path = None if Inputs.local_path == "" else Inputs.local_path
        self.experienceName = ""

        if self._tc_build_id:
            Benchmark.log_info(f"Initializing KitRunner with Kit Teamcity Build ID: {self._tc_build_id}")
        if local_path:
            Benchmark.log_info(f"Initializing KitRunner with Local Kit Directory: {local_path}")
        build_archive_path = None if Inputs.build_archive == "" else Inputs.build_archive
        absolute_exe_path = None if Inputs.absolute_exe_path == "" else Inputs.absolute_exe_path
        absolute_exe_path = os.getenv("OVAT_KIT_ARTIFACT", absolute_exe_path)
        if absolute_exe_path:
            Benchmark.log_info(f"Initializing KitRunner with absolute path: {absolute_exe_path}")

        self._k = KitRunner(
            tc_build_id=self._tc_build_id,
            app_root_dir=local_path,
            build_extraction_dir=build_archive_path,
            app_exe_path=absolute_exe_path,
        )


if __name__ == "__main__":
    Benchmark.run()
