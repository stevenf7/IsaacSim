// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdContextIncludes.h>
// clang-format on

#include <omni/kit/IStageUpdate.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>

#include "core/RangeSensorManager.h"
#include "lidar/LidarSensor.h"
#include "ultrasonic/UltrasonicSensor.h"
#include "radar/RadarSensor.h"

#include <carb/imgui/ImGui.h>

#include <omni/physx/IPhysx.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/fastcache/FastCache.h>
#include <carb/tasking/ITasking.h>

#include <omni/kit/IEditor.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/KitUtils.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UsdContext.h>
#include <omni/renderer/IDebugDraw.h>

#include <map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.range_sensor.plugin", "Isaac Range Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl,
                 omni::isaac::range_sensor::LidarSensorInterface,
                 omni::isaac::range_sensor::UltrasonicSensorInterface,
                 omni::isaac::range_sensor::RadarSensorInterface)


CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx,
                      carb::imgui::ImGui,
                      omni::kit::IEditor,
                      omni::kit::IStageUpdate,
                      carb::fastcache::FastCache,
                      omni::renderer::IDebugDraw,
                      carb::tasking::ITasking)

// private stuff
namespace
{


omni::kit::IEditor* g_editor = nullptr;
omni::renderer::IDebugDraw* g_debugDraw = nullptr;
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
carb::imgui::ImGui* g_imGuiInterface = nullptr;
carb::fastcache::FastCache* g_FastCache = nullptr;
omni::physx::IPhysx* g_physx = nullptr;
pxr::UsdStageWeakPtr g_stage = nullptr;
carb::tasking::ITasking* gTasking = nullptr;


std::unique_ptr<omni::isaac::range_sensor::RangeSensorManager> gRangeSensorManager;

} // end of anonymous namespace

namespace lidar
{

int CARB_ABI getNumCols(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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

float* CARB_ABI getLinearDepthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getLinearDepthData().data();
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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

carb::Float3* CARB_ABI getPointCloud(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getPointCloud().data();
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

bool CARB_ABI isLidarSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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

}

namespace ultrasonic
{
bool CARB_ABI isUltrasonicSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return false;
    }
}

int CARB_ABI getNumBins(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumBins();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumRows(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumRows();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumEmitters(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumEmitters();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumCols(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumCols();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}


uint16_t* CARB_ABI getDepthData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        // TODO @markb: put sensible indexing guards on this
        if (sensor)
        {

            return sensor->getDepthData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getEnvelope(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getEnvelope(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getLinearDepthData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getLinearDepthData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}
uint8_t* CARB_ABI getIntensityData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getIntensityData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getZenithData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getZenithData().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getAzimuthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getAzimuthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

carb::Float3* CARB_ABI getPointCloud(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getPointCloud().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

}

namespace radar
{
bool CARB_ABI isRadarSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::RadarSensor* sensor =
            gRangeSensorManager->getRadarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Radar Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Radar Sensor Manager does not exist");
        return false;
    }
}

}

void onAttach(long stageId, double metersPerUnit, void* data)
{
    g_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!g_stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    if (gRangeSensorManager)
    {
        gRangeSensorManager->initialize(g_stage);
        gRangeSensorManager->initComponents();
    }
}

void onDetach(void* data)
{
    if (gRangeSensorManager)
    {
        gRangeSensorManager->deleteAllComponents();
    }
}

// TODO @markb: add this to ultrasonic!!!
void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    if (!settings->isPlaying)
    {
        return;
    }

    if (gRangeSensorManager)
    {
        gRangeSensorManager->tick(elapsedSecs);
    }
}
void onStop(void* userData)
{
    if (gRangeSensorManager)
    {
        gRangeSensorManager->onStop();
    }
}

void onPrimAdd(const pxr::SdfPath& primPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Add: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());

    if (g_stage && gRangeSensorManager)
    {
        pxr::UsdPrim addedPrim = g_stage->GetPrimAtPath(primPath);
        if (!addedPrim)
        {
            return;
        }
        // Add the root prim
        gRangeSensorManager->onComponentAdd(addedPrim);

        // Check if it has any descendants that need to be added
        pxr::UsdPrimSubtreeRange range = addedPrim.GetDescendants();
        for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            gRangeSensorManager->onComponentAdd(prim);
        }
    }
}
void onComponentChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Change: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (g_stage && gRangeSensorManager)
    {
        gRangeSensorManager->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Remove: %s\n", primPath);
    if (gRangeSensorManager)
    {
        gRangeSensorManager->onComponentRemove(primPath);
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

    g_debugDraw = framework->acquireInterface<omni::renderer::IDebugDraw>();
    if (!g_debugDraw)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
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

    g_physx = framework->acquireInterface<omni::physx::IPhysx>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }
    gTasking = framework->acquireInterface<carb::tasking::ITasking>();


    gRangeSensorManager =
        std::make_unique<omni::isaac::range_sensor::RangeSensorManager>(g_debugDraw, g_physx, g_FastCache, gTasking);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Range Sensor Interface";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimOrPropertyChange = onComponentChange;
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
    gRangeSensorManager.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);

    g_physx = nullptr;
    g_stage = nullptr;
    g_FastCache = nullptr;
}


void fillInterface(omni::isaac::range_sensor::LidarSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;

    memset(&iface, 0, sizeof(iface));
    iface.getNumCols = lidar::getNumCols;
    iface.getNumRows = lidar::getNumRows;
    iface.getNumColsTicked = lidar::getNumColsTicked;
    iface.getDepthData = lidar::getDepthData;
    iface.getLinearDepthData = lidar::getLinearDepthData;
    iface.getIntensityData = lidar::getIntensityData;
    iface.getZenithData = lidar::getZenithData;
    iface.getAzimuthData = lidar::getAzimuthData;
    iface.getPointCloud = lidar::getPointCloud;
    iface.isLidarSensor = lidar::isLidarSensor;
}


void fillInterface(omni::isaac::range_sensor::UltrasonicSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;
    memset(&iface, 0, sizeof(iface));
    iface.getNumCols = ultrasonic::getNumCols;
    iface.getNumRows = ultrasonic::getNumRows;
    iface.getDepthData = ultrasonic::getDepthData;
    iface.getLinearDepthData = ultrasonic::getLinearDepthData;
    iface.getIntensityData = ultrasonic::getIntensityData;
    iface.getZenithData = ultrasonic::getZenithData;
    iface.getAzimuthData = ultrasonic::getAzimuthData;
    iface.getNumBins = ultrasonic::getNumBins;
    iface.getPointCloud = ultrasonic::getPointCloud;
    iface.getEnvelope = ultrasonic::getEnvelope;
    iface.isUSS = ultrasonic::isUltrasonicSensor;
}


void fillInterface(omni::isaac::range_sensor::RadarSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;
    memset(&iface, 0, sizeof(iface));
    iface.isRadarSensor = radar::isRadarSensor;
}
