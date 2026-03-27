-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
-- SPDX-License-Identifier: LicenseRef-NvidiaProprietary
--
-- NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
-- property and proprietary rights in and to this material, related
-- documentation and any modifications thereto. Any use, reproduction,
-- disclosure or distribution of this material and related documentation
-- without an express license agreement from NVIDIA CORPORATION or
-- its affiliates is strictly prohibited.

if platform_target ~= "linux-aarch64" then -- Skip build for aarch64 architecture
    -- Setup the basic extension variables
    local ext = get_current_extension_info()
    ext.target_dir = isaac_sim_extra_extsbuild_dir .. "/" .. ext.id
    ext.bin_dir = ext.target_dir .. "/bin"
    -- Set up the basic shared project information
    project_ext(ext)

    -- -------------------------------------
    -- Link/copy folders and files to be packaged with the extension
    repo_build.prebuild_link {
        { "data", ext.target_dir .. "/data" },
        { "docs", ext.target_dir .. "/docs" },
        { "include", ext.target_dir .. "/include" },
        { "python/impl", ext.target_dir .. "/isaacsim/kit/xr/teleop/bridge/impl" },
    }

    repo_build.prebuild_copy {
        { "config/extension.toml", ext.target_dir .. "/extension.toml" },
        { "python/*.py", ext.target_dir .. "/isaacsim/kit/xr/teleop/bridge" },
    }

    -- Common include directories for both plugin and bindings.
    -- omni.kit.xr.core: use extsbuild when kit is from packman (links.path in repo.toml);
    -- use kit/exts when kit is a local source link (Kit SDK builds into kit/exts/).
    local common_includedirs = {
        "include",
        isaac_sim_extsbuild_dir .. "/omni.kit.xr.core/include",
        "%{root}/_build/%{platform}/%{config}/kit/exts/omni.kit.xr.core/include",
        "%{root}/_build/%{platform}/%{config}/kit/dev/fabric/include",
        "%{target_deps}/openxr.%{cfg.buildcfg}/include",
    }

    -- OpenXR loader library directories and links
    local function add_openxr_links()
        libdirs { "%{target_deps}/openxr.%{cfg.buildcfg}/lib" }
        filter { "system:windows", "configurations:debug" }
            links { "openxr_loaderd" }
        filter { "system:windows", "configurations:release" }
            links { "openxr_loader" }
        filter { "system:linux" }
            links { "openxr_loader" }
        filter {}
    end

    -- -------------------------------------
    -- Build the C++ plugin (OpenXR Component)
    -- This implements the ITeleopBridge interface and registers as an OpenXR component
    project_ext_plugin(ext, "isaacsim.kit.xr.teleop.bridge.plugin")
    targetdir(ext.bin_dir)
    add_files("include", "include/isaacsim/kit/xr/teleop/bridge")
    add_files("source", "plugins/isaacsim.kit.xr.teleop.bridge")
    includedirs(common_includedirs)
    add_openxr_links()

    -- Enable RTTI and exceptions - required for OpenXRComponentBase templates
    -- which use exception handling macros from omni.kit.xr.core
    rtti "On"
    exceptionhandling "On"

    -- -------------------------------------
    -- Build Python bindings
    -- Uses carb::defineInterfaceClass to properly integrate with Carbonite
    project_ext_bindings {
        ext = ext,
        project_name = "isaacsim.kit.xr.teleop.bridge.python",
        module = "_bridge",
        src = "bindings/isaacsim.kit.xr.teleop.bridge",
        target_subdir = "isaacsim/kit/xr/teleop/bridge/bindings",
    }
    dependson { "isaacsim.kit.xr.teleop.bridge.plugin" }
    links { "isaacsim.kit.xr.teleop.bridge.plugin" }
    includedirs(common_includedirs)
    add_openxr_links()

else
    print("SKIPPING BUILD FOR AARCH64")
end
