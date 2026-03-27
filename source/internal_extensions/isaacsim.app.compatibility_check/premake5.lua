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

local ext = get_current_extension_info()
ext.target_dir = isaac_sim_extra_extsbuild_dir .. "/" .. ext.id
ext.bin_dir = ext.target_dir .. "/bin"
project_ext(ext)

-- build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "isaacsim.app.compatibility_check.plugin")
targetdir(ext.bin_dir)
rtti("On")

add_files("include", "include")
add_files("source", "plugins")
includedirs {
    "include",
    "plugins",
    "%{root}/_build/target-deps/rtx_plugins/include",
}

-- build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.app.compatibility_check.python",
    module = "_compatibility_check",
    src = "bindings",
    target_subdir = "isaacsim/app/compatibility_check/bindings",
}
includedirs {
    "include",
    "%{root}/_build/target-deps/rtx_plugins/include",
}

-- link/copy folders and files that should be packaged with the extension
repo_build.prebuild_link {
    { "python/impl", ext.target_dir .. "/isaacsim/app/compatibility_check/impl" },
    { "python/tests", ext.target_dir .. "/isaacsim/app/compatibility_check/tests" },
    { "data", ext.target_dir .. "/data" },
    { "docs", ext.target_dir .. "/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/isaacsim/app/compatibility_check" },
}
