// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "import/UrdfImporter.h"
#include "import/ImportHelpers.h"

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/ext/IExt.h>
#include <omni/isaac/urdf/Urdf.h>
#include <omni/kit/IApp.h>
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdContext.h>

#include <memory>
#include <fstream>

#define EXTENSION_NAME "omni.isaac.urdf"

using namespace carb;

const struct carb::PluginImplDesc kPluginImpl = { EXTENSION_NAME, "URDF Utilities", "NVIDIA",
                                                  carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::urdf::Urdf)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging)

namespace
{

carb::Framework* g_framework = nullptr;

omni::isaac::urdf::UrdfRobot parseUrdf(const std::string& assetRoot,
                                       const std::string& assetName,
                                       const omni::isaac::urdf::ImportConfig& importConfig)
{
    omni::isaac::urdf::UrdfRobot robot;

    std::string filename = assetRoot + "/" + assetName;
    pxr::UsdStageWeakPtr stage = omni::usd::UsdContext::getContext()->getStage();
    if (stage)
    {


        CARB_LOG_ERROR("Trying to import %s", filename.c_str());

        if (parseUrdf(assetRoot, assetName, robot))
        {
        }
        else
        {
            CARB_LOG_ERROR("Failed to parse URDF file '%s'", assetName.c_str());
        }

        if (importConfig.mergeFixedJoints)
        {
            collapseFixedJoints(robot);
        }
    }
    return robot;
}
void importRobot(const std::string& assetRoot,
                 const std::string& assetName,
                 const omni::isaac::urdf::UrdfRobot& robot,
                 const omni::isaac::urdf::ImportConfig& importConfig)
{

    omni::isaac::urdf::GymAssetOptions options;
    omni::isaac::urdf::UrdfImporter urdfImporter(assetRoot, assetName, options);
    pxr::UsdStageWeakPtr stage = omni::usd::UsdContext::getContext()->getStage();
    if (stage)
    {
        urdfImporter.addToStage(stage, robot);
    }
}
}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup URDF Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
}


CARB_EXPORT void carbOnPluginShutdown()
{
}


void fillInterface(omni::isaac::urdf::Urdf& iface)
{
    memset(&iface, 0, sizeof(iface));
    iface.parseUrdf = parseUrdf;
    iface.importRobot = importRobot;
}
