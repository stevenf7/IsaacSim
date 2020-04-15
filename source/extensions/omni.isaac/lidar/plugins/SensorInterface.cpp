// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
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
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <omni/kit/IStageUpdate.h>
#include <omni/isaac/lidar/LidarInterface.h>

#include "lidar/LidarSensorManager.h"
#include "lidar/LidarSensor.h"

#include <LidarSchema/lidar.h>

#include <carb/imgui/ImGui.h>

#include <carb/physx/physx.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/fastcache/FastCache.h>

#include <omni/kit/IEditor.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/KitUtils.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UsdContext.h>

#include <map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.lidar.plugin", "Isaac Lidar", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::lidar::LidarInterface)
CARB_PLUGIN_IMPL_DEPS(carb::physics::PhysX,
                      carb::imgui::ImGui,
                      omni::kit::IEditor,
                      omni::kit::IStageUpdate,
                      carb::fastcache::FastCache,
                      omni::isaac::dynamic_control::DynamicControl)

// private stuff
namespace
{


omni::kit::IEditor* g_editor = nullptr;
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
carb::imgui::ImGui* g_imGuiInterface = nullptr;
carb::fastcache::FastCache* g_FastCache = nullptr;
carb::physics::PhysX* g_physx = nullptr;
omni::isaac::dynamic_control::DynamicControl* g_DynamicControl = nullptr;
pxr::UsdStageRefPtr g_stage = nullptr;

std::unique_ptr<omni::isaac::lidar::LidarSensorManager> gLidarSensorManager;

} // end of anonymous namespace

int CARB_ABI getNumCols(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumCols();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumRows(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumRows();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumColsTicked(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumColsTicked();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

uint16_t* CARB_ABI getDepthData(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}
uint8_t* CARB_ABI getIntensityData(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getIntensityData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getZenithData(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getZenithData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getAzimuthData(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getAzimuthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

bool CARB_ABI isLidar(const char* primPath)
{
    if (gLidarSensorManager)
    {
        omni::isaac::lidar::LidarSensor* sensor =
            gLidarSensorManager->getSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return false;
    }
}
// stage update
void onAttach(long stageId, double metersPerUnit, void* data)
{
    pxr::UsdStageRefPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    g_stage = stage;
    if (gLidarSensorManager)
    {
        gLidarSensorManager->initialize(g_stage);
        gLidarSensorManager->initComponents();
    }

    // printf("++ LidarInterface: Stage Attach: stageId %ld\n", stageId);
}

void onDetach(void* data)
{
    if (gLidarSensorManager)
    {
        gLidarSensorManager->deleteAllComponents();
    }
    // printf("++ LidarInterface: Stage Detach\n");
}

void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{

    if (!settings->isPlaying)
    {
        return;
    }
    // printf("++ LidarInterface: Stage Update %f\n", elapsedSecs);

    if (gLidarSensorManager)
    {
        gLidarSensorManager->tick(elapsedSecs);
    }
}

void onPrimAdd(const char* primPath, void* userData)
{
    // printf("++ Lidar: Prim Add: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (gLidarSensorManager)
    {
        gLidarSensorManager->onComponentAdd(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    }
}
void onComponentChange(const char* primPath, const omni::kit::PrimDirtyBits*, void* userData)
{
    // printf("++ Lidar: Prim Change: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (gLidarSensorManager)
    {
        gLidarSensorManager->onComponentChange(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    }
}

void onPrimRemove(const char* primPath, void* userData)
{
    printf("++ Lidar: Prim Remove: %s\n", primPath);
    if (gLidarSensorManager)
    {
        gLidarSensorManager->onComponentRemove(pxr::SdfPath(primPath));
    }
}


CARB_EXPORT void carbOnPluginStartup()
{

    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    g_editor = framework->acquireInterface<omni::kit::IEditor>();
    if (!g_editor)
    {
        CARB_LOG_ERROR("*** Failed to acquire editor interface\n");
        return;
    }

    g_imGuiInterface = framework->acquireInterface<carb::imgui::ImGui>();
    if (!g_imGuiInterface)
    {
        CARB_LOG_ERROR("*** Failed to acquire ImGui interface\n");
        return;
    }

    g_stageUpdate = framework->acquireInterface<omni::kit::IStageUpdate>();
    if (!g_stageUpdate)
    {
        CARB_LOG_ERROR("*** Failed to acquire stage update interface\n");
        return;
    }

    g_FastCache = framework->acquireInterface<carb::fastcache::FastCache>();
    if (!g_FastCache)
    {
        CARB_LOG_ERROR("*** Failed to acquire FastCache interface\n");
        return;
    }
    g_DynamicControl = framework->acquireInterface<omni::isaac::dynamic_control::DynamicControl>();
    if (!g_DynamicControl)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }

    g_physx = framework->acquireInterface<carb::physics::PhysX>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }


    gLidarSensorManager =
        std::make_unique<omni::isaac::lidar::LidarSensorManager>(g_editor, g_physx, g_DynamicControl, g_FastCache);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Lidar Interface";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimChange = onComponentChange;
    desc.onPrimRemove = onPrimRemove;
    desc.order = 50; // happens after physx, dc, but before robot engine bridge

    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    if (!g_stageUpdateNode)
    {
        CARB_LOG_ERROR("*** Failed to create stage update node\n");
        return;
    }
}


CARB_EXPORT void carbOnPluginShutdown()
{
    gLidarSensorManager.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);

    g_physx = nullptr;
    g_stage = nullptr;
    g_FastCache = nullptr;
}


void fillInterface(omni::isaac::lidar::LidarInterface& iface)
{
    using namespace omni::isaac::lidar;

    memset(&iface, 0, sizeof(iface));
    iface.getNumCols = getNumCols;
    iface.getNumRows = getNumRows;
    iface.getNumColsTicked = getNumColsTicked;

    iface.getDepthData = getDepthData;
    iface.getIntensityData = getIntensityData;
    iface.getZenithData = getZenithData;
    iface.getAzimuthData = getAzimuthData;

    iface.isLidar = isLidar;
}
