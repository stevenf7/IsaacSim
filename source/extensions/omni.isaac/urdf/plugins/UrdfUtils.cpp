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

#include <memory>
#include <fstream>

#define EXTENSION_NAME "omni.isaac.urdf"

using namespace carb;

const struct carb::PluginImplDesc kPluginImpl = { EXTENSION_NAME, "URDF Utilities", "NVIDIA",
                                                  carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::urdf::Urdf)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging, omni::kit::IStageUpdate)

namespace
{

carb::Framework* g_framework = nullptr;
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
pxr::UsdStageRefPtr g_stage = nullptr;

std::unique_ptr<omni::isaac::urdf::UsdUrdfStream> g_urdfStream = nullptr;

void importUrdf(std::string filename, const omni::isaac::urdf::ImportConfig& importConfig)
{
    CARB_LOG_INFO("Trying to import %s", filename.c_str());

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
            g_urdfStream->UsdUrdfTranslateUrdfToUsd(g_stage);
        }
    }
}

void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    pxr::UsdStageRefPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("URDF Importer could not find USD stage");
        return;
    }

    g_stage = stage;
}

}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup URDF Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
    g_stageUpdate = g_framework->acquireInterface<omni::kit::IStageUpdate>();
    g_urdfStream = std::make_unique<omni::isaac::urdf::UsdUrdfStream>();

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacUrdfUtils";
    desc.onAttach = onAttach;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
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
