-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "schemas", ext.target_dir .. "/schemas" },
    { "include", ext.target_dir .. "/include" },
    { "isaacsim", ext.target_dir .. "/isaacsim" },
}

-- Structured log schema code generation: produces the baked .json and a C++ .gen.h
-- from the .schema source file.
dofile('_build/target-deps/carb_sdk_plugins/tools/omni.structuredlog/omni.structuredlog.lua')
setup_omni_structuredlog('../../../_build/target-deps/carb_sdk_plugins/')

project_with_location("isaacsim.core.telemetry.schema")
    omni_structuredlog_schema {
        schema     = "schemas/isaacsim.telemetry.common.schema",
        cpp_output = "include/isaacsim/core/telemetry/IsaacsimTelemetryCommon.gen.h",
        bake_to    = "schemas/isaacsim.telemetry.common.1.0.json",
        namespace  = "isaacsim::core::telemetry",
    }
