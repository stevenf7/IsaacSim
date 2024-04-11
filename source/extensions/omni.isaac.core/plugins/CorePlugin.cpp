// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#define CARB_EXPORTS
#include <carb/PluginUtils.h>

#include <isaacSim/Version.h>
#include <omni/ext/IExt.h>

// namespace omni::isaac::core
// {
// class coreExt : public omni::ext::IExt
// {
// public:
//     void onStartup(const char* extId) override{};
//     void onShutdown() override{};
// };
// }

// const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.core.plugin", "Core interface to Isaac sim", "NVIDIA",
//                                                   carb::PluginHotReload::eEnabled, "dev" };
// CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::core::coreExt)

// void addCrashreporterMetadata()
// {
//     carb::crashreporter::addCrashMetadata("lib_isaacSim_buildVersion", ISAACSIM_BUILD_VERSION);
//     carb::crashreporter::addCrashMetadata(
//         "lib_isaacSim_buildRepo", "gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim");
//     carb::crashreporter::addCrashMetadata("lib_isaacSim_buildHash", ISAACSIM_BUILD_SHA);
//     carb::crashreporter::addCrashMetadata("lib_isaacSim_buildBranch", ISAACSIM_BUILD_BRANCH);
//     carb::crashreporter::addCrashMetadata("lib_isaacSim_buildDate", ISAACSIM_BUILD_DATE);
// }

// CARB_EXPORT void carbOnPluginStartup()
// {
//     addCrashreporterMetadata();
// }

// CARB_EXPORT void carbOnPluginShutdown()
// {
// }

// void fillInterface(omni::isaac::core::coreExt& iface)
// {
//     iface = {};
// }
