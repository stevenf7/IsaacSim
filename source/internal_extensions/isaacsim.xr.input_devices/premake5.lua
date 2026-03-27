-- SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
-- http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

if platform_target == "linux-x86_64" then
    local ext = get_current_extension_info()
    ext.target_dir = isaac_sim_extra_extsbuild_dir .. "/" .. ext.id
    ext.bin_dir = ext.target_dir .. "/bin"

    project_ext(ext)

    -- Python Bindings for Carbonite Plugin
    project_ext_bindings {
        ext = ext,
        project_name = "isaacsim.xr.input_devices.python",
        module = "_isaac_xr_input_devices",
        src = "bindings",
        target_subdir = "isaacsim/xr/input_devices/bindings",
    }
    staticruntime("Off")
    add_files("impl", "plugins")
    add_files("iface", "include")
    defines { "ISAACSIM_XR_INPUT_DEVICES_EXPORT" }

    includedirs {
        "%{root}/source/internal_extensions/isaacsim.xr.input_devices/include",
        "%{root}/source/internal_extensions/isaacsim.xr.input_devices/plugins",
    }

    repo_build.prebuild_link {
        { "python/impl", ext.target_dir .. "/isaacsim/xr/input_devices/impl" },
        { "python/tests", ext.target_dir .. "/isaacsim/xr/input_devices/tests" },
        { "docs", ext.target_dir .. "/docs" },
        { "data", ext.target_dir .. "/data" },
    }

    repo_build.prebuild_copy {
        { "python/*.py", ext.target_dir .. "/isaacsim/xr/input_devices" },
    }

    -- Build a simple test shared library that implements the ISAACSIM_HANDTRACKER_API
    project_ext_plugin(ext, "isaacsim.xr.input_devices.handtracker.testlib")
    kind("SharedLib")
    files {
        "plugins/isaacsim.xr.input_devices/IsaacSimHandTrackerTestLib.cpp",
    }
    includedirs {
        "include",
    }
    defines { "ISAACSIM_HANDTRACKER_CAPI_EXPORTS" }

    -- Name the output to a test-specific filename
    filter { "system:linux" }
    targetname("IsaacSimHandTracker_test")
    -- Ensure the test lib is built for both debug and release configs
    configmap {
        ["debug"] = "debug",
        ["release"] = "release",
    }
    filter {}

    -- Copy the produced .so into the extension target folder for runtime loading
    -- Note: project_ext_plugin outputs are packaged automatically into the extension's bin folder
else
    print("SKIPPING BUILD - Only supported on linux-x86_64")
end
