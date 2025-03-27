// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#define CARB_EXPORTS
#include <carb/PluginUtils.h>

#include <isaacSim/Version.h>
#include <omni/ext/IExt.h>

namespace isaacsim::core::api
{
class CoreExt : public omni::ext::IExt
{
public:
    void onStartup(const char* extId) override{};
    void onShutdown() override{};
};
}

const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.core.api.plugin", "Core interface to Isaac sim", "NVIDIA",
                                                    carb::PluginHotReload::eEnabled, "dev" };
CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::core::api::CoreExt)

void addCrashreporterMetadata()
{
    carb::crashreporter::addCrashMetadata("lib_isaacSim_buildVersion", ISAACSIM_BUILD_VERSION);
    carb::crashreporter::addCrashMetadata("lib_isaacSim_buildRepo", ISAACSIM_BUILD_REPO);
    carb::crashreporter::addCrashMetadata("lib_isaacSim_buildHash", ISAACSIM_BUILD_SHA);
    carb::crashreporter::addCrashMetadata("lib_isaacSim_buildBranch", ISAACSIM_BUILD_BRANCH);
    carb::crashreporter::addCrashMetadata("lib_isaacSim_buildDate", ISAACSIM_BUILD_DATE);
}

CARB_EXPORT void carbOnPluginStartup()
{
    addCrashreporterMetadata();
}

CARB_EXPORT void carbOnPluginShutdown()
{
}

void fillInterface(isaacsim::core::api::CoreExt& iface)
{
    iface = {};
}
