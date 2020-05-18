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

#include "UsdUrdfStream.h"

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

std::unique_ptr<omni::isaac::urdf::UsdUrdfStream> g_urdfStream = nullptr;

void importUrdf(std::string filename, const omni::isaac::urdf::ImportConfig& importConfig)
{
    CARB_LOG_INFO("Trying to import %s", filename.c_str());

    pxr::UsdStageRefPtr stage = omni::usd::UsdContext::getContext()->getStage();
    if (!stage)
    {
        CARB_LOG_ERROR("Stage Not Valid");
        return;
    }
    std::ifstream fin(filename.c_str());
    if (!fin.is_open())
    {
        CARB_LOG_ERROR("Failed to open file \"%s\"", filename.c_str());
    }
    else
    {

        std::string error;

        g_urdfStream->SetFileName(filename);
        g_urdfStream->SetImportConfig(importConfig);
        if (!g_urdfStream->UsdUrdfReadDataFromStream(fin, &error))
        {
            CARB_LOG_ERROR("Failed to READ \"%s\"", filename.c_str());
        }
        else
        {
            g_urdfStream->UsdUrdfTranslateUrdfToUsd(stage);
        }
    }
}
}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup URDF Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
    g_urdfStream = std::make_unique<omni::isaac::urdf::UsdUrdfStream>();
}


CARB_EXPORT void carbOnPluginShutdown()
{
    g_urdfStream = nullptr;
}


void fillInterface(omni::isaac::urdf::Urdf& iface)
{
    memset(&iface, 0, sizeof(iface));
    iface.importUrdf = importUrdf;
}
