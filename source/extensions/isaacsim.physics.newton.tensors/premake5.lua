-- SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
-- SPDX-License-Identifier: Apache-2.0

-- Setup the extension.
local ext = get_current_extension_info()

project_ext(ext)

-- Link folders that should be packaged with the extension.
repo_build.prebuild_link {
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "python/impl", ext.target_dir.."/isaacsim/physics/newton/tensors/impl" },
    { "python/tests", ext.target_dir.."/isaacsim/physics/newton/tensors/tests" },
}

-- Copy the module __init__.py to maintain the module root
repo_build.prebuild_copy {
    { "python/__init__.py", ext.target_dir.."/isaacsim/physics/newton/tensors/__init__.py" },
}

-- Build the C++ plugin
project_ext_plugin(ext, "isaacsim.physics.newton.tensors.plugin")

    add_files("source", "src")
    add_files("base", "src/base")
    add_files("cpu", "src/cpu")
    add_files("gpu", "src/gpu")
    add_files("utils", "src/utils")

    add_cuda_dependencies()

    includedirs {
        "%{root}/source/extensions/isaacsim.physics.newton.tensors/src",
        target_deps .. "/omni_physics/%{config}/include",
        target_deps .. "/pybind11/include",
        target_deps .. "/usd/%{cfg.buildcfg}/include",
    }

    filter { "system:linux" }
    includedirs {
        target_deps .. "/usd/%{cfg.buildcfg}/include/boost",
        target_deps .. "/python/include/python3.12",
    }
    filter {}

    libdirs {
        target_deps .. "/python/lib",
        target_deps .. "/usd/%{cfg.buildcfg}/lib",
    }

    links {
        "carb",
    }

    add_usd({ "sdf", "usd" })

    defines {
        "NOMINMAX",
    }

    -- Upstream JointTypes.h uses std::numeric_limits without including <limits>.
    forceincludes { "limits" }

    filter { "system:linux" }
        exceptionhandling "On"
    filter {}
