// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif
#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>

#include "core/BaseSensorComponent.h"
#include "core/BaseSensorManager.h"
#include "imu_sensor/ImuSensor.h"
#include "contact_sensor/ContactManager.h"
#include "contact_sensor/ContactSensor.h"
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <isaacSensorSchema/isaacContactSensor.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/sensor/IsaacSensor.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/KitUtils.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/sensors/lidar/ILidarProfileReaderFactory.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.sensor.plugin", "Isaac Contact Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };


CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::sensor::ContactSensorInterface, omni::isaac::sensor::ImuSensorInterface)

CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx,
                      omni::physx::IPhysxSceneQuery,
                      omni::kit::IStageUpdate,
                      omni::renderer::IDebugDraw,
                      omni::graph::core::IGraphRegistry,
                      omni::sensors::lidar::ILidarProfileReaderFactory)

DECLARE_OGN_NODES()


// private stuff
namespace
{
omni::renderer::IDebugDraw* g_debugDraw = nullptr;
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::physx::IPhysx* g_physx = nullptr;
pxr::UsdStageWeakPtr g_stage = nullptr;
std::unique_ptr<omni::isaac::sensor::IsaacSensorManager> gIsaacSensorManager;
omni::physx::SubscriptionId g_stepSubscription;
} // end of anonymous namespace

namespace contact_sensor
{

bool CARB_ABI isContactSensor(const char* primPath)
{
    if (g_stage && gIsaacSensorManager)
    {
        omni::isaac::sensor::ContactSensor* sensor =
            gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Contact Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return false;
    }
}

const char* CARB_ABI CsDecodeBodyName(uint64_t path_token)
{
    return omni::isaac::utils::getSdfPathFromUint64(path_token).GetString().c_str();
}

omni::isaac::sensor::CsRawData* CARB_ABI CsGetBodyRawData(const char* primPath, size_t& numContacts)
{
    if (g_stage != nullptr)
    {
        pxr::UsdPrim body = g_stage->GetPrimAtPath(pxr::SdfPath(primPath));
        if (!body.IsValid())
        {
            CARB_LOG_ERROR("Prim Path is invalid");
        }

        pxr::PhysxSchemaPhysxContactReportAPI contactReportAPI =
            pxr::PhysxSchemaPhysxContactReportAPI::Get(g_stage, pxr::SdfPath(primPath));

        if (!contactReportAPI)
        {
            contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Apply(body);
        }
        if (!contactReportAPI.GetThresholdAttr())
        {
            contactReportAPI.CreateThresholdAttr();
        }
        if (!contactReportAPI.GetReportPairsRel())
        {
            contactReportAPI.CreateReportPairsRel();
        }

        // setting the minimum required force threshold to 0
        contactReportAPI.GetThresholdAttr().Set(0.0f);
        omni::isaac::sensor::CsRawData* data = nullptr;
        if (gIsaacSensorManager != nullptr && gIsaacSensorManager->getContactManager() != nullptr)
        {
            data = gIsaacSensorManager->getContactManager()->getCsRawData(primPath, numContacts);
        }
        else
        {
            CARB_LOG_ERROR("Sensor Manager or Contact Manager not found");
        }
        return data;
    }
    else
    {
        CARB_LOG_ERROR("Stage not found");
    }
    return nullptr;
}


omni::isaac::sensor::CsRawData* CARB_ABI CsGetSensorRawData(const char* primPath, size_t& numContacts)
{
    omni::isaac::sensor::ContactSensor* sensor =
        gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::CsRawData* data = nullptr;

    if (sensor)
    {
        data = sensor->getRawData(numContacts);
    }
    return data;
}

omni::isaac::sensor::CsReading CARB_ABI CsGetSensorReadings(const char* primPath, size_t& num_readings)
{
    omni::isaac::sensor::ContactSensor* sensor =
        gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::CsReading data = omni::isaac::sensor::CsReading();
    if (sensor)
    {
        data = sensor->getSensorReadings(num_readings);
    }
    return data;
}

size_t CARB_ABI CsGetSensorReadingsSize(const char* primPath)
{
    omni::isaac::sensor::ContactSensor* sensor =
        gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

    size_t num_readings = 0;
    if (sensor)
    {
        sensor->getSensorReadings(num_readings);
    }
    return num_readings;
}

omni::isaac::sensor::CsReading CARB_ABI CsGetSensorSimReading(const char* primPath)
{
    omni::isaac::sensor::ContactSensor* sensor =
        gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::CsReading data;
    if (sensor)
    {
        data = sensor->getSimSensorReading();
    }
    return data;
}

omni::isaac::sensor::CsReading CARB_ABI CsGetSensorReading(const char* primPath, const bool& getLatestValue = false)
{
    omni::isaac::sensor::ContactSensor* sensor =
        gIsaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::CsReading data;
    if (sensor)
    {
        data = sensor->getSensorReading(getLatestValue);
    }
    return data;
}
}

namespace imu_sensor
{

bool CARB_ABI isImuSensor(const char* primPath)
{
    if (g_stage && gIsaacSensorManager)
    {
        omni::isaac::sensor::ImuSensor* sensor =
            gIsaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Imu Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return false;
    }
}

omni::isaac::sensor::IsReading CARB_ABI IsGetSensorReadings(const char* primPath, size_t& num_readings)
{
    omni::isaac::sensor::ImuSensor* sensor =
        gIsaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::IsReading data = omni::isaac::sensor::IsReading();
    if (sensor)
    {
        data = sensor->getSensorReadings(num_readings);
    }
    return data;
}

omni::isaac::sensor::IsReading CARB_ABI IsGetSensorReading(
    const char* primPath,
    const std::function<omni::isaac::sensor::IsReading(std::vector<omni::isaac::sensor::IsReading>, float)>&
        interpolateFunction = {},
    const bool& getLatestValue = false)
{
    omni::isaac::sensor::ImuSensor* sensor =
        gIsaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::IsReading data = omni::isaac::sensor::IsReading();
    if (sensor)
    {
        data = sensor->getSensorReading(interpolateFunction, getLatestValue);
    }
    return data;
}

omni::isaac::sensor::IsReading CARB_ABI IsGetSensorSimReading(const char* primPath)
{
    omni::isaac::sensor::ImuSensor* sensor =
        gIsaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::IsReading data;
    if (sensor)
    {
        data = sensor->getSimSensorReading();
    }
    return data;
}

size_t CARB_ABI IsGetSensorReadingsSize(const char* primPath)
{
    omni::isaac::sensor::ImuSensor* sensor =
        gIsaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

    size_t num_readings = 0;
    if (sensor)
    {
        sensor->getSensorReadings(num_readings);
    }
    return num_readings;
}
}


void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    if (!settings->isPlaying)
    {
        return;
    }

    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->drawSensor();
    }
}

void onPrimAdd(const pxr::SdfPath& primPath, void* userData)
{
    if (g_stage && gIsaacSensorManager)
    {
        pxr::UsdPrim addedPrim = g_stage->GetPrimAtPath(primPath);
        if (!addedPrim)
        {
            return;
        }
        // Add the root prim
        gIsaacSensorManager->onComponentAdd(addedPrim);

        // Check if it has any descendants that need to be added
        pxr::UsdPrimSubtreeRange range = addedPrim.GetDescendants();
        for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            gIsaacSensorManager->onComponentAdd(prim);
        }
    }
}


static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    g_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!g_stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->initialize(g_stage);
        gIsaacSensorManager->initComponents();
    }
}

static void onDetach(void* userData)
{
    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->deleteAllComponents();
    }
}

static void onStop(void* userData)
{
    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->onStop();
    }
}

static void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->onComponentRemove(primPath);
    }
}

void onComponentChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    if (g_stage && gIsaacSensorManager)
    {
        gIsaacSensorManager->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPhysicsStep(float dt, void* userData)
{
    if (gIsaacSensorManager)
    {
        gIsaacSensorManager->onPhysicsStep(static_cast<double>(dt));
    }
}

CARB_EXPORT void carbOnPluginStartup()
{


    g_debugDraw = carb::getCachedInterface<omni::renderer::IDebugDraw>();
    if (!g_debugDraw)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
        return;
    }

    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();
    if (!g_stageUpdate)
    {
        CARB_LOG_ERROR("*** Failed to acquire stage update interface\n");
        return;
    }

    g_physx = carb::getCachedInterface<omni::physx::IPhysx>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }


    gIsaacSensorManager = std::make_unique<omni::isaac::sensor::IsaacSensorManager>(g_physx, g_debugDraw);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Isaac Sensor Interface";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimOrPropertyChange = onComponentChange;
    desc.onPrimRemove = onPrimRemove;
    desc.order = 50; // happens after physx, dc, but before robot engine bridge

    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    g_stepSubscription = g_physx->subscribePhysicsStepEvents(onPhysicsStep, nullptr);
    if (!g_stageUpdateNode)
    {
        CARB_LOG_ERROR("*** Failed to create stage update node\n");
        return;
    }
    INITIALIZE_OGN_NODES()
}


CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
    gIsaacSensorManager.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
    g_physx->unsubscribePhysicsStepEvents(g_stepSubscription);
    g_physx = nullptr;
    g_stage = nullptr;
}

void fillInterface(omni::isaac::sensor::ContactSensorInterface& iface)
{
    using namespace omni::isaac::sensor;

    memset(&iface, 0, sizeof(iface));


    iface.getSensorRawData = contact_sensor::CsGetSensorRawData;
    iface.getBodyRawData = contact_sensor::CsGetBodyRawData;
    iface.getSensorReadingsSize = contact_sensor::CsGetSensorReadingsSize;
    iface.getSensorReadings = contact_sensor::CsGetSensorReadings;
    iface.getSensorSimReading = contact_sensor::CsGetSensorSimReading;
    iface.getSensorReading = contact_sensor::CsGetSensorReading;
    iface.decodeBodyName = contact_sensor::CsDecodeBodyName;
    iface.isContactSensor = contact_sensor::isContactSensor; // Checks if the path is a contact sensor
}

void fillInterface(omni::isaac::sensor::ImuSensorInterface& iface)
{
    using namespace omni::isaac::sensor;

    memset(&iface, 0, sizeof(iface));

    iface.getSensorReadingsSize = imu_sensor::IsGetSensorReadingsSize;
    iface.getSensorReadings = imu_sensor::IsGetSensorReadings;
    iface.getSensorReading = imu_sensor::IsGetSensorReading;
    iface.getSensorSimReading = imu_sensor::IsGetSensorSimReading;
    iface.isImuSensor = imu_sensor::isImuSensor;
}
#ifdef _WIN32
#    pragma warning(pop)
#endif
