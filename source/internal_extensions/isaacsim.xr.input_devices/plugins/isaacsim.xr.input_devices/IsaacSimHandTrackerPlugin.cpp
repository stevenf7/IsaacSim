// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/logging/Log.h>

#include <isaacsim/xr/input_devices/IsaacSimHandTrackerCAPI.h>

#if defined(_WIN32)
#    define NOMINMAX
#    include <windows.h>
#else
#    include <dlfcn.h>
#endif

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>

// Plugin that dynamically loads a vendor hand-tracker shared library and exposes
// a stable C API for Python bindings to interact with.
namespace isaacsim
{
namespace xr
{
namespace input_devices
{

#if defined(_WIN32)
using LibHandle = HMODULE;
static LibHandle loadLibraryByName(const char* path)
{
    return ::LoadLibraryA(path);
}
static void* loadSymbol(LibHandle lib, const char* name)
{
    return reinterpret_cast<void*>(::GetProcAddress(lib, name));
}
static void unloadLibrary(LibHandle lib)
{
    if (lib)
        ::FreeLibrary(lib);
}
#else
using LibHandle = void*;
static LibHandle loadLibraryByName(const char* path)
{
    return ::dlopen(path, RTLD_NOW | RTLD_LOCAL);
}
static void* loadSymbol(LibHandle lib, const char* name)
{
    return ::dlsym(lib, name);
}
static void unloadLibrary(LibHandle lib)
{
    if (lib)
    {
        ::dlclose(lib);
    }
}
#endif

struct HandTrackerLibrary
{
    std::mutex mutex;
    LibHandle handle = nullptr;
    IsaacSimHandTracker_Initialize_Func fpInitialize = nullptr;
    IsaacSimHandTracker_GetData_Func fpGetData = nullptr;
    IsaacSimHandTracker_Shutdown_Func fpShutdown = nullptr;

    bool isLoadedUnsafe() const
    {
        return handle != nullptr && fpInitialize && fpGetData && fpShutdown;
    }

    bool load(const char* overridePath)
    {
        std::lock_guard<std::mutex> lock(mutex);

        if (isLoadedUnsafe())
        {
            return true;
        }

        // Allow override via environment variables first
        const char* envPath = std::getenv("ISAACSIM_HANDTRACKER_LIB");
        const char* envName = std::getenv("ISAACSIM_HANDTRACKER_NAME");

        std::vector<std::string> candidates;

        if (overridePath && std::strlen(overridePath) > 0)
        {
            candidates.emplace_back(overridePath);
        }

        if (envPath && std::strlen(envPath) > 0)
        {
            candidates.emplace_back(envPath);
        }

        if (envName && std::strlen(envName) > 0)
        {
            std::string baseName(envName);
            std::string lowerBase = baseName;
            std::transform(lowerBase.begin(), lowerBase.end(), lowerBase.begin(),
                           [](unsigned char c) { return (char)std::tolower(c); });

#if defined(_WIN32)
            // Try as provided, then append .dll variants
            candidates.emplace_back(baseName);
            if (baseName.find('.') == std::string::npos)
            {
                candidates.emplace_back(baseName + ".dll");
                candidates.emplace_back(lowerBase + ".dll");
            }
#else
            // Try as provided, then lib<name>.so variants
            candidates.emplace_back(baseName);
            if (baseName.find(".so") == std::string::npos)
            {
                candidates.emplace_back("lib" + baseName + ".so");
                candidates.emplace_back("lib" + lowerBase + ".so");
            }
#endif
        }

#if defined(_WIN32)
        candidates.emplace_back("IsaacSimHandTracker.dll");
        candidates.emplace_back("isaacsim_handtracker.dll");
#else
        candidates.emplace_back("libIsaacSimHandTracker.so");
        candidates.emplace_back("libisaacsim_handtracker.so");
#endif

        for (const std::string& candidateStr : candidates)
        {
            const char* candidate = candidateStr.c_str();
            if (candidate == nullptr || std::strlen(candidate) == 0)
            {
                continue;
            }

            handle = loadLibraryByName(candidate);
            if (!handle)
            {
#if !defined(_WIN32)
                const char* err = ::dlerror();
                CARB_LOG_WARN("Failed to load hand tracker library '%s': %s", candidate, err ? err : "unknown error");
#else
                CARB_LOG_WARN("Failed to load hand tracker library '%s'", candidate);
#endif
                continue;
            }

            fpInitialize = reinterpret_cast<IsaacSimHandTracker_Initialize_Func>(
                loadSymbol(handle, "IsaacSimHandTracker_Initialize"));
            fpGetData =
                reinterpret_cast<IsaacSimHandTracker_GetData_Func>(loadSymbol(handle, "IsaacSimHandTracker_GetData"));
            fpShutdown =
                reinterpret_cast<IsaacSimHandTracker_Shutdown_Func>(loadSymbol(handle, "IsaacSimHandTracker_Shutdown"));

            if (!fpInitialize || !fpGetData || !fpShutdown)
            {
                CARB_LOG_ERROR("Hand tracker library '%s' is missing required symbols", candidate);
                unloadLibrary(handle);
                handle = nullptr;
                fpInitialize = nullptr;
                fpGetData = nullptr;
                fpShutdown = nullptr;
                continue;
            }

            CARB_LOG_INFO("Loaded hand tracker library: %s", candidate);
            return true;
        }

        CARB_LOG_WARN(
            "Unable to locate a valid hand tracker library. Set ISAACSIM_HANDTRACKER_LIB or ISAACSIM_HANDTRACKER_NAME or install the library.");
        return false;
    }

    void unload()
    {
        std::lock_guard<std::mutex> lock(mutex);
        if (handle)
        {
            unloadLibrary(handle);
            handle = nullptr;
        }
        fpInitialize = nullptr;
        fpGetData = nullptr;
        fpShutdown = nullptr;
    }
};

static HandTrackerLibrary g_library;

#if defined(_MSC_VER)
#    ifdef ISAACSIM_HANDTRACKER_PLUGIN_EXPORTS
#        define ISAACSIM_HANDTRACKER_PLUGIN_API __declspec(dllexport)
#    else
#        define ISAACSIM_HANDTRACKER_PLUGIN_API __declspec(dllimport)
#    endif
#else
#    define ISAACSIM_HANDTRACKER_PLUGIN_API __attribute__((visibility("default")))
#endif

extern "C"
{

    // Load the hand tracker shared library. Optional path overrides default search.
    ISAACSIM_HANDTRACKER_PLUGIN_API bool IsaacSimHandTrackerPlugin_Load(
        const char* overrideLibraryPath) // NOLINT(readability-identifier-naming)
    {
        return g_library.load(overrideLibraryPath);
    }

    // Unload the previously loaded hand tracker shared library.
    ISAACSIM_HANDTRACKER_PLUGIN_API void IsaacSimHandTrackerPlugin_Unload() // NOLINT(readability-identifier-naming)
    {
        g_library.unload();
    }

    // Initialize the underlying device via the loaded library.
    ISAACSIM_HANDTRACKER_PLUGIN_API bool IsaacSimHandTrackerPlugin_Initialize() // NOLINT(readability-identifier-naming)
    {
        if (!g_library.load(nullptr))
        {
            return false;
        }
        return g_library.fpInitialize();
    }

    // Fetch joint data via the loaded library.
    // NOLINTNEXTLINE(readability-identifier-naming)
    ISAACSIM_HANDTRACKER_PLUGIN_API bool IsaacSimHandTrackerPlugin_GetData(IsaacSimHandJointPose* outJointPoses,
                                                                           int outJointPoseCount)
    {
        if (!g_library.isLoadedUnsafe())
        {
            return false;
        }
        return g_library.fpGetData(outJointPoses, outJointPoseCount);
    }

    // Shutdown the underlying device via the loaded library.
    ISAACSIM_HANDTRACKER_PLUGIN_API void IsaacSimHandTrackerPlugin_Shutdown() // NOLINT(readability-identifier-naming)
    {
        if (g_library.isLoadedUnsafe())
        {
            g_library.fpShutdown();
        }
    }
}

} // namespace input_devices
} // namespace xr
} // namespace isaacsim
