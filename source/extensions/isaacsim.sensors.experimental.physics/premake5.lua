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

project_ext(ext)

local python_target_path = "isaacsim/sensors/experimental/physics"

add_files("python", "python/*.py")
add_files("python/impl", "python/impl/**.py")
add_files("python/tests", "python/tests/*.py")

repo_build.prebuild_link {
    { "python/impl", ext.target_dir .. "/" .. python_target_path .. "/impl" },
    { "python/tests", ext.target_dir .. "/" .. python_target_path .. "/tests" },
    { "data", ext.target_dir .. "/data" },
    { "docs", ext.target_dir .. "/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/" .. python_target_path },
}
