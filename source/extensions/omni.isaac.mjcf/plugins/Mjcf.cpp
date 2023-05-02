// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include "MjcfImporter.h"
#include "stdio.h"

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <omni/ext/IExt.h>
#include <omni/isaac/mjcf/mjcf.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
// clang-format off
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdContext.h>
// clang-format on

#define EXTENSION_NAME "omni.isaac.mjcf.plugin"

using namespace carb;

const struct carb::PluginImplDesc kPluginImpl = { EXTENSION_NAME, "MJCF Utilities", "NVIDIA",
                                                  carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::mjcf::Mjcf)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging)

namespace
{

// passed in from python
void createAssetFromMJCF(const char* fileName,
                         const char* primName,
                         omni::isaac::mjcf::ImportConfig& config,
                         const std::string& stage_identifier = "")
{
    omni::isaac::mjcf::MJCFImporter mjcf(fileName, config);
    if (!mjcf.isLoaded)
    {
        printf("cannot load mjcf xml file\n");
    }
    Transform trans = Transform();

    bool save_stage = true;
    pxr::UsdStageRefPtr _stage;
    if (stage_identifier != "" && pxr::UsdStage::IsSupportedFile(stage_identifier))
    {
        _stage = pxr::UsdStage::Open(stage_identifier);
        if (!_stage)
        {
            CARB_LOG_INFO("Creating Stage: %s", stage_identifier.c_str());
            _stage = pxr::UsdStage::CreateNew(stage_identifier);
        }
        else
        {
            for (const auto& p : _stage->GetPrimAtPath(pxr::SdfPath("/")).GetChildren())
            {
                _stage->RemovePrim(p.GetPath());
            }
        }
        config.makeDefaultPrim = true;
        pxr::UsdGeomSetStageUpAxis(_stage, pxr::UsdGeomTokens->z);
    }
    if (!_stage) // If all else fails, import on current stage
    {
        CARB_LOG_INFO("Importing URDF to Current Stage");
        _stage = omni::usd::UsdContext::getContext()->getStage();
        save_stage = false;
    }
    std::string result = "";
    if (_stage)
    {
        pxr::UsdGeomSetStageMetersPerUnit(_stage, 1.0 / config.distanceScale);
        if (!mjcf.AddPhysicsEntities(_stage, trans, primName, config))
        {
            printf("no physics entities found!\n");
        }
        // CARB_LOG_WARN("Import Done, saving");
        if (save_stage)
        {
            // CARB_LOG_WARN("Saving Stage %s", _stage->GetRootLayer()->GetIdentifier().c_str());
            _stage->Save();
        }
    }
}

}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup MJCF Extension");
}


CARB_EXPORT void carbOnPluginShutdown()
{
}


void fillInterface(omni::isaac::mjcf::Mjcf& iface)
{
    using namespace omni::isaac::mjcf;
    memset(&iface, 0, sizeof(iface));
    // iface.helloWorld = helloWorld;
    iface.createAssetFromMJCF = createAssetFromMJCF;
    // iface.importRobot = importRobot;
}
