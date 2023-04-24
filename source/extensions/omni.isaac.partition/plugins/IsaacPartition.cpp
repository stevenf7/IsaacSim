// Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#define CARB_EXPORTS

#include "IsaacPartitionProcessor.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/settings/ISettings.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/kit/KitUpdateOrder.h>
#include <omni/kit/KitUtils.h>

using namespace carb;
using namespace omni;
using namespace isaac;
using namespace pxr;

kit::IStageUpdate* gStageUpdate{ nullptr };
kit::StageUpdateNode* gStageUpdateNode{ nullptr };
settings::ISettings* gSettings{ nullptr };
std::unique_ptr<omni::isaac::IsaacPartitionProcessor> gPartition{};

const PluginImplDesc kPluginImpl = { "omni.isaac.partition.plugin", "Isaac Partition", "NVIDIA",
                                     PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::IsaacPartition)
CARB_PLUGIN_IMPL_DEPS(carb::settings::ISettings, omni::kit::IStageUpdate)

namespace
{
void SetExportPath(const char* filePath)
{
    gPartition->setExportPath(filePath);
}

const char* GetExportPath()
{
    return gPartition->getExportPath();
}

void ClearCameras()
{
    gPartition->clearCameras();
}

void AddCameraPath(const char* cameraPath)
{
    gPartition->addCameraPath(cameraPath);
}

size_t NumCameraPaths()
{
    return gPartition->numCameraPaths();
}

const char* GetCameraPath(size_t index)
{
    return gPartition->getCameraPath(index);
}

void SaveToUsd()
{
    gPartition->saveToUsd();
}

void OnAttach(long int stageId, double metersPerUnit, void*)
{
    gPartition->mStageId = stageId;
    gPartition->mMetersPerUnit = metersPerUnit;
}

void OnDetach(void*)
{
    gPartition->mStageId = 0;
}

}

//
CARB_EXPORT void carbOnPluginShutdown()
{
    if (gStageUpdate != nullptr)
    {
        gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
        gStageUpdate = nullptr;
    }

    gPartition.release();
}

//
CARB_EXPORT void carbOnPluginStartup()
{
    if (Framework* framework = getFramework())
    {
        gPartition.reset(new omni::isaac::IsaacPartitionProcessor{});
        gStageUpdate = framework->acquireInterface<kit::IStageUpdate>();
        gSettings = framework->acquireInterface<settings::ISettings>();

        if (gStageUpdate != nullptr && gSettings != nullptr)
        {
            kit::StageUpdateNodeDesc desc = { nullptr };

            desc.displayName = "IsaacPartition";
            desc.order = kit::update::eIUsdStageUpdatePhysics;
            desc.userData = gPartition.get();
            desc.onAttach = OnAttach;
            desc.onDetach = OnDetach;

            gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
        }
    }
}

//
void fillInterface(IsaacPartition& iface)
{
    memset(&iface, 0, sizeof iface);

    iface.saveToUsd = SaveToUsd;
    iface.setExportPath = SetExportPath;
    iface.getExportPath = GetExportPath;
    iface.clearCameras = ClearCameras;
    iface.addCameraPath = AddCameraPath;
    iface.numCameraPaths = NumCameraPaths;
    iface.getCameraPath = GetCameraPath;
}
