// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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
#include <pch/UsdPCH.h>
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>

#include "core/BaseSensorComponent.h"
#include "core/BaseSensorManager.h"
#include "imu_sensor/ImuSensor.h"
#include "contact_sensor/ContactManager.h"
#include "contact_sensor/ContactSensor.h"
#include "lightbeam_sensor/LightBeamSensor.h"
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/KitUtils.h>
#include <omni/physics/tensors/IRigidBodyView.h>
#include <omni/physics/tensors/IRigidContactView.h>
#include <omni/physics/tensors/ISimulationView.h>
#include <omni/physics/tensors/TensorApi.h>
#include <omni/physics/tensors/TensorDesc.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/sensors/IProfileReader.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <IsaacSensor.h>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.sensor.plugin", "Isaac Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };


CARB_PLUGIN_IMPL(kPluginImpl,
                 omni::isaac::sensor::ContactSensorInterface,
                 omni::isaac::sensor::ImuSensorInterface,
                 omni::isaac::sensor::LightBeamSensorInterface)

CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx,
                      omni::physx::IPhysxSceneQuery,
                      omni::kit::IStageUpdate,
                      omni::graph::core::IGraphRegistry,
                      omni::sensors::IProfileReaderFactory)

DECLARE_OGN_NODES()


// private stuff
namespace
{
omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::physx::IPhysx* g_physx = nullptr;
pxr::UsdStageWeakPtr g_stage = nullptr;
omni::physics::tensors::TensorApi* g_tensorApi = nullptr;
omni::physics::tensors::ISimulationView* g_simulationView = nullptr;
omni::physics::tensors::IRigidBodyView* g_rigidBodyView = nullptr;
omni::physics::tensors::TensorDesc rigidBodyData;
std::vector<std::string> g_rigidBodyPaths;
carb::settings::ISettings* g_settings = nullptr;
std::unique_ptr<omni::isaac::sensor::IsaacSensorManager> g_isaacSensorManager;
omni::physx::SubscriptionId g_stepSubscription;
std::vector<float> g_rigidBodyDataBuffer;
bool firstFrame = true;
long int g_stageID;
std::unordered_map<std::string, size_t> g_rigidBodyToDataBufferMap;
} // end of anonymous namespace

namespace contact_sensor
{

bool CARB_ABI isContactSensor(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::ContactSensor* sensor =
            g_isaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
        if (g_isaacSensorManager != nullptr && g_isaacSensorManager->getContactManager() != nullptr)
        {
            data = g_isaacSensorManager->getContactManager()->getCsRawData(primPath, numContacts);
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
        g_isaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::CsRawData* data = nullptr;

    if (sensor)
    {
        data = sensor->getRawData(numContacts);
    }
    return data;
}

omni::isaac::sensor::CsReading CARB_ABI CsGetSensorReading(const char* primPath, const bool& getLatestValue = false)
{
    omni::isaac::sensor::ContactSensor* sensor =
        g_isaacSensorManager->getContactSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::ImuSensor* sensor =
            g_isaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
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

omni::isaac::sensor::IsReading CARB_ABI IsGetSensorReading(
    const char* primPath,
    const std::function<omni::isaac::sensor::IsReading(std::vector<omni::isaac::sensor::IsReading>, float)>&
        interpolateFunction = {},
    const bool& getLatestValue = false,
    const bool& readGravity = true)
{
    omni::isaac::sensor::ImuSensor* sensor =
        g_isaacSensorManager->getImuSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    omni::isaac::sensor::IsReading data = omni::isaac::sensor::IsReading();
    if (sensor)
    {
        data = sensor->getSensorReading(interpolateFunction, getLatestValue, readGravity);
    }
    return data;
}

}

namespace lightbeam_sensor
{
bool CARB_ABI isLightBeamSensor(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::LightBeamSensor* sensor =
            g_isaacSensorManager->getLightBeamSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Light Beam Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return false;
    }
}

float* CARB_ABI getLinearDepthData(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::LightBeamSensor* sensor =
            g_isaacSensorManager->getLightBeamSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

        if (sensor)
        {
            return sensor->getLinearDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Light Beam Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return nullptr;
    }
}

int CARB_ABI getNumRays(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::LightBeamSensor* sensor =
            g_isaacSensorManager->getLightBeamSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

        if (sensor)
        {
            return sensor->getNumRays();
        }
        else
        {
            CARB_LOG_ERROR("Light Beam Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return 0;
    }
}

carb::Float3* CARB_ABI getHitPosData(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::LightBeamSensor* sensor =
            g_isaacSensorManager->getLightBeamSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

        if (sensor)
        {
            return sensor->getHitPosData().data();
        }
        else
        {
            CARB_LOG_ERROR("Light Beam Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return 0;
    }
}

uint8_t* CARB_ABI getBeamHitData(const char* primPath)
{
    if (g_stage && g_isaacSensorManager)
    {
        omni::isaac::sensor::LightBeamSensor* sensor =
            g_isaacSensorManager->getLightBeamSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));

        if (sensor)
        {
            return sensor->getBeamHitData().data();
        }
        else
        {
            CARB_LOG_ERROR("Light Beam Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Isaac Sensor Manager does not exist");
        return 0;
    }
}

} // lightbeam_sensor

void onPlay()
{
    g_simulationView = g_tensorApi->createSimulationView(g_stageID);

    // First create the sensors and find the sensor parents to create physics views
    for (const pxr::UsdPrim& prim : g_stage->Traverse())
    {
        if (prim.IsA<pxr::IsaacSensorIsaacImuSensor>())
        {
            // Add the root prim
            g_isaacSensorManager->onComponentAdd(prim);
            omni::isaac::sensor::ImuSensor* imuSensor = dynamic_cast<omni::isaac::sensor::ImuSensor*>(
                g_isaacSensorManager->getComponent(prim.GetPath().GetString()));

            //  if the imu has no valid parent, return
            if (imuSensor != nullptr)
            {
                std::string parentPath = imuSensor->getParentPrim().GetPath().GetString();

                if (std::find(g_rigidBodyPaths.begin(), g_rigidBodyPaths.end(), parentPath) == g_rigidBodyPaths.end())
                {
                    g_rigidBodyPaths.push_back(parentPath);
                }
            }
        }
        else if (prim.IsA<pxr::IsaacSensorIsaacContactSensor>())
        {
            // Add the root prim
            g_isaacSensorManager->onComponentAdd(prim);
        }
        else if (prim.IsA<pxr::IsaacSensorIsaacLightBeamSensor>())
        {
            // Add the root prim
            g_isaacSensorManager->onComponentAdd(prim);
        }
    }

    // Then create physics views
    if (!g_rigidBodyPaths.empty())
    {
        g_rigidBodyView = g_simulationView->createRigidBodyView(g_rigidBodyPaths);
    }
    else
    {
        g_rigidBodyView = nullptr;
    }

    for (size_t i = 0; i < g_rigidBodyPaths.size(); i++)
    {
        g_rigidBodyToDataBufferMap[g_rigidBodyPaths[i]] = i * 6;
    }

    g_rigidBodyDataBuffer.resize(6 * g_rigidBodyPaths.size(), 0);
    rigidBodyData.dtype = omni::physics::tensors::TensorDataType::eFloat32;
    rigidBodyData.numDims = 2;
    rigidBodyData.dims[0] = static_cast<int>(g_rigidBodyPaths.size());
    rigidBodyData.dims[1] = 6;
    rigidBodyData.data = g_rigidBodyDataBuffer.data();
    rigidBodyData.ownData = true;

    // pass in the view data and index to the sensor
    for (const pxr::UsdPrim& prim : g_stage->Traverse())
    {
        omni::isaac::sensor::ImuSensor* imuSensor = g_isaacSensorManager->getImuSensor(prim);
        if (imuSensor != nullptr)
        {
            size_t sensorDataIndex = g_rigidBodyToDataBufferMap[imuSensor->getParentPrim().GetPath().GetString()];
            imuSensor->initialize(&g_rigidBodyDataBuffer, sensorDataIndex);
        }
    }
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    g_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    g_stageID = stageId;
    if (!g_stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    if (g_isaacSensorManager)
    {
        g_isaacSensorManager->initialize(g_stage);
        g_isaacSensorManager->initComponents();
    }
}

static void onStop(void* userData)
{
    if (g_isaacSensorManager)
    {
        g_isaacSensorManager->onStop();
        g_isaacSensorManager->deleteAllComponents();
    }
    firstFrame = true;
    if (g_simulationView != nullptr)
    {
        g_simulationView->release(true);
        g_simulationView = nullptr;
        g_rigidBodyView = nullptr;
    }
    g_rigidBodyPaths.clear();
    g_rigidBodyDataBuffer.clear();
    g_rigidBodyToDataBufferMap.clear();
}

void onComponentChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    if (g_stage && g_isaacSensorManager)
    {
        g_isaacSensorManager->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPhysicsStep(float dt, void* userData)
{
    if (g_isaacSensorManager)
    {
        if (firstFrame)
        {
            onPlay();
            firstFrame = false;
        }

        if (g_rigidBodyView != nullptr)
        {
            g_rigidBodyView->getVelocities(&rigidBodyData);
        }

        g_isaacSensorManager->onPhysicsStep(static_cast<double>(dt));
    }
}


static void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    if (g_isaacSensorManager)
    {
        g_isaacSensorManager->onComponentRemove(primPath);
    }
}

CARB_EXPORT void carbOnPluginStartup()
{
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();
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

    g_tensorApi = carb::getCachedInterface<omni::physics::tensors::TensorApi>();
    if (!g_tensorApi)
    {
        CARB_LOG_ERROR("*** Failed to acquire Tensor Api interface\n");
        return;
    }

    g_settings = carb::getCachedInterface<carb::settings::ISettings>();
    if (!g_settings)
    {
        CARB_LOG_ERROR("*** Failed to acquire Carb Setting interface\n");
        return;
    }
    static constexpr char setting[] = "/physics/suppressReadback";
    g_settings->setBool(setting, false);

    g_isaacSensorManager = std::make_unique<omni::isaac::sensor::IsaacSensorManager>(g_physx);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Isaac Sensor Interface";
    desc.onAttach = onAttach;
    desc.onDetach = onStop;
    desc.onPrimRemove = onPrimRemove;
    desc.onStop = onStop;
    desc.onPrimOrPropertyChange = onComponentChange;
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
    g_isaacSensorManager.reset();
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
    iface.getSensorReading = contact_sensor::CsGetSensorReading;
    iface.decodeBodyName = contact_sensor::CsDecodeBodyName;
    iface.isContactSensor = contact_sensor::isContactSensor; // Checks if the path is a contact sensor
}

void fillInterface(omni::isaac::sensor::ImuSensorInterface& iface)
{
    using namespace omni::isaac::sensor;

    memset(&iface, 0, sizeof(iface));

    iface.getSensorReading = imu_sensor::IsGetSensorReading;
    iface.isImuSensor = imu_sensor::isImuSensor;
}

void fillInterface(omni::isaac::sensor::LightBeamSensorInterface& iface)
{
    using namespace omni::isaac::sensor;

    memset(&iface, 0, sizeof(iface));

    iface.isLightBeamSensor = lightbeam_sensor::isLightBeamSensor;
    iface.getBeamHitData = lightbeam_sensor::getBeamHitData;
    iface.getNumRays = lightbeam_sensor::getNumRays;
    iface.getLinearDepthData = lightbeam_sensor::getLinearDepthData;
    iface.getHitPosData = lightbeam_sensor::getHitPosData;
}

#ifdef _WIN32
#    pragma warning(pop)
#endif
