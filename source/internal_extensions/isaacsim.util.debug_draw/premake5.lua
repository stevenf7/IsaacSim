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
local ogn = get_ogn_project_information(ext, "isaacsim/util/debug_draw")
project_ext(ext)

project_with_location("isaacsim.util.debug_draw.primitive_drawing")
targetdir(ext.bin_dir)
kind("StaticLib")
language("C++")

pic("On")
staticruntime("Off")
add_files("impl", "library")
includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/omni_physics/%{config}/include",
    "%{root}/source/internal_extensions/isaacsim.util.debug_draw/include",
}
libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}

links { "omni.usd" }
-- Begin OpenUSD
add_usd()
-- End OpenUSD

filter { "system:linux" }
disablewarnings { "error=pragmas" }
includedirs {
    "%{root}/_build/target-deps/python/include/python3.12",
}
buildoptions("-fvisibility=default")
filter { "system:windows" }
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
}
filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "isaacsim.util.debug_draw.plugin")
dependson { "isaacsim.util.debug_draw.primitive_drawing", "omni.physx.plugin" }
removeflags { "UndefinedIdentifiers" }

add_files("impl", "plugins")
add_files("ogn", ogn.nodes_path)

include_physx()
add_cuda_dependencies()
-- Add the standard dependencies all OGN projects have
add_ogn_dependencies(ogn)
includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/omni_client_library/include",
    extsbuild_dir .. "/usdrt.scenegraph/include",
    "%{root}/_build/target-deps/python/include",
    "%{kit_sdk_bin_dir}/dev/fabric/include/",
    "%{root}/source/internal_extensions/isaacsim.util.debug_draw/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
}
libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}

if os.target() == "linux" then
    includedirs {
        "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/python/include/python3.12",
    }
else
    libdirs {
        "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
    }
end

links { "isaacsim.util.debug_draw.primitive_drawing", "omni.usd" }

extra_usd_libs = {
    "usdUtils",
    "usdGeom",
    "ts",
}

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

-- ----------------------------------------------------------------------
-- Breaking this out as a separate project ensures the .ogn files are processed before their results are needed
project_ext_ogn(ext, ogn)

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.util.debug_draw.python",
    module = "_debug_draw",
    src = "bindings",
    target_subdir = "isaacsim/util/debug_draw/bindings",
}

-- Add the standard dependencies all OGN projects have, and link directories with Python nodes
dependson { "isaacsim.util.debug_draw.primitive_drawing" }
--add_files("bindings", "bindings/*.*")
--add_files("python", "python/*.py")
--add_files("python/tests", "python/tests/*.py")
include_physx()
includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{root}/source/internal_extensions/isaacsim.util.debug_draw/include",
}

libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/nv_usd/release/lib",
}
links { "isaacsim.util.debug_draw.primitive_drawing" }

extra_usd_libs = {
    "usdUtils",
    "usdGeom",
    "ts",
}

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "system:linux", "platforms:x86_64", "configurations:release" }
links { "tbb" }
filter { "system:linux", "platforms:x86_64", "configurations:debug" }
links { "tbb_debug" }
filter {}

filter { "system:windows", "platforms:x86_64" }
-- link_boost_for_windows({"boost_python310"})

filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

repo_build.prebuild_link {
    { "python/impl", ogn.python_target_path .. "/impl" },
    { "python/tests", ogn.python_tests_target_path },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "include", ext.target_dir .. "/include" },
}

repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}
