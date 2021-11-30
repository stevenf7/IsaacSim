// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "IMUSensor.h"

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <physicsSchemaTools/UsdTools.h>
#include <usdPhysics/scene.h>

#include <PxActor.h>
#include <PxArticulationLink.h>
#include <PxRigidDynamic.h>
#include <map>
#include <string>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.imu_sensor.plugin", "Isaac IMU Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::imu_sensor::IMUSensorInterface)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::physx::IPhysxSceneQuery, omni::kit::IStageUpdate)

using namespace pxr;

static pxr::UsdStageWeakPtr gStage = nullptr;
static omni::physx::IPhysx* gPhysXInterface = nullptr;
static omni::isaac::imu_sensor::IMUManager* gIMUManager = nullptr;
static omni::kit::IStageUpdate* gStageUpdate = nullptr;
static omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;

namespace omni
{
namespace isaac
{
namespace imu_sensor
{
// assumes second arg is a format string literal
#define IS_LOG(level, fmt, ...)                                                                                        \
    {                                                                                                                  \
        CARB_LOG(level, fmt, ##__VA_ARGS__);                                                                           \
    }

// these assume the first arg is a format string literal
#define IS_LOG_VERBOSE(fmt, ...) IS_LOG(carb::logging::kLevelVerbose, fmt, ##__VA_ARGS__)
#define IS_LOG_INFO(fmt, ...) IS_LOG(carb::logging::kLevelInfo, fmt, ##__VA_ARGS__)
#define IS_LOG_WARN(fmt, ...) IS_LOG(carb::logging::kLevelWarn, fmt, ##__VA_ARGS__)
#define IS_LOG_ERROR(fmt, ...) IS_LOG(carb::logging::kLevelError, fmt, ##__VA_ARGS__)
#define IS_LOG_FATAL(fmt, ...) IS_LOG(carb::logging::kLevelFatal, fmt, ##__VA_ARGS__)

inline float lerp(const float& start, const float& end, const float t)
{
    return start + ((end - start) * t);
}

IMUSensor::IMUSensor(pxr::TfToken body) : bodyID(body)
{
    reset();
}

void IMUSensor::initialize(IsProperties props)
{
    mProps = props;
    // gravity that the IMU experience in world frame
    double unitScale = UsdGeomGetStageMetersPerUnit(gStage);
    mGravity = pxr::GfVec3d(0, 0, 9.80665 / unitScale);
    // If a scene exists we try reading gravity from it
    pxr::UsdPrimRange range = gStage->Traverse();
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::UsdPhysicsScene>())
        {
            pxr::UsdPhysicsScene scene(prim);

            // Only load the attribute if it exists
            isaac::utils::safeGetAttribute(scene.GetGravityMagnitudeAttr(), mGravity);
        }
    }
}

void IMUSensor::reset()
{
    mCurrentTime = 0.0f;
    mCurrent = 0;
    for (int i = 0; i < RAW_BUFFER_SIZE; i++)
    {
        mRawBuffer[i] = IsRawData();
    }
    mReadingPair[0] = mReadingPair[1] = IsReading();
    mProcessedReadings = false;
    mSensorReadings.clear();
}

// read bodyID's lin vel and ang vel, save them in mRawReadingList
void IMUSensor::update(float time, float dt)
{
    // IS_LOG_INFO("Sensor Update %f", time);
    pxr::SdfPath actor(bodyID.GetString().c_str());

    ::physx::PxRigidBody* rigid = nullptr;
    // follow logics are from source/extensions/omni.isaac.dynamic_control/plugins/DcPhysx.cpp
    ::physx::PxActor* pxActor = (::physx::PxActor*)gPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTActor);
    if (pxActor)
    {
        ::physx::PxActorType::Enum type = pxActor->getType();
        if (type == ::physx::PxActorType::eRIGID_DYNAMIC /*|| type == PxActorType::eARTICULATION_LINK*/)
        {
            rigid = static_cast<::physx::PxRigidBody*>(pxActor);
        }
    }
    else
    {
        ::physx::PxArticulationLink* link =
            (::physx::PxArticulationLink*)gPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTLink);
        if (link)
        {
            rigid = static_cast<::physx::PxRigidBody*>(link);
        }
    }

    // only when rigid is valid can we start to generate sensor data
    if (rigid)
    {
        // both velocities are in world frame, need to convert them to sensor frame
        ::physx::PxVec3 ang_vel = rigid->getAngularVelocity();
        ::physx::PxVec3 lin_vel = rigid->getLinearVelocity();

        /*  *transform velocities in the rigid body frame to that in the sensor frame according to mProps*
         *  notation used here follows book "Modern Robotics" (Kevin Lynch)
         *  we denote world frame as w, body frame as a, sensor frame as b
         *  R_ab rotates a vector in frame b into frame a
         *  R_ab and q_ab are the same rotation, R is the rotation matrix while q is the quaternion
         *  we use T_wa to represent R_wa, p_wa together in a 4x4 homogeneous matrix
         *
         *  p_wb represents the position of b in frame w
         *  for example, p_wa is the global position of frame a,
         *  and p_ab is the transformation from body frame to sensor frame
         *
         *  so the global position of sensor frame is p_wb = p_wa + Rwa*p_ab
         *  global rotation of sensor frame is R_wb = R_wa*R_ab
         *  velocities of body frame in world frame are w_wa(w) and v_wa(v)
         *  velocity of sensor frame in world frame: v_wb = v_wa + R_wa*skew(w_a)*p_ab = v + skew(w)*R_wa*p_ab
         *
         *  finally, velocity of sensor frame in sensor frame  v_b = R_wb^T*v_wb
         *  w_b is the body angular velocity of frame b in frame b, w_b = R_wb^T*w_wa
         */
        pxr::GfVec3d w(ang_vel.x, ang_vel.y, ang_vel.z); // w_wa
        pxr::GfVec3d v(lin_vel.x, lin_vel.y, lin_vel.z); // v_wa
        ::physx::PxTransform T_wa = rigid->getGlobalPose();
        pxr::GfVec3d p_wa(T_wa.p.x, T_wa.p.y, T_wa.p.z);
        pxr::GfRotation R_wa(pxr::GfQuatd(T_wa.q.w, pxr::GfVec3d(T_wa.q.x, T_wa.q.y, T_wa.q.z)));
        pxr::GfVec3d p_ab(mProps.position.x, mProps.position.y, mProps.position.z);
        pxr::GfQuatd q_ab(
            mProps.orientation.w, pxr::GfVec3d(mProps.orientation.x, mProps.orientation.y, mProps.orientation.z));
        pxr::GfRotation R_ab(q_ab);
        pxr::GfRotation R_wb = R_wa * R_ab;
        pxr::GfVec3d p_wab = R_wa.TransformDir(p_ab);
        // velocity of sensor frame in world frame
        pxr::GfVec3d v_wb = v + GfMatrix3d(0, -w[2], w[1], w[2], 0, -w[0], -w[1], w[0], 0) * p_wab; // convert w to a
                                                                                                    // skew-symmetric
                                                                                                    // form
        // velocity of sensor frame in sensor frame
        pxr::GfVec3d v_b = R_wb.GetInverse().TransformDir(v_wb);
        // angular velocity of sensor frame in sensor frame
        pxr::GfVec3d w_b = R_wb.GetInverse().TransformDir(w);


        // gravity that the IMU experience in sensor frame
        pxr::GfVec3d g_b = R_wb.GetInverse().TransformDir(mGravity);

        // we then finite diff v_b to get a_b, to reduce noise, average multiple finite diffs
        // save raw data into a buffer list , buffer 0 always saves the latest velocities
        for (int i = RAW_BUFFER_SIZE - 1; i > 0; i--)
        {
            mRawBuffer[i].time = mRawBuffer[i - 1].time;
            mRawBuffer[i].dt = mRawBuffer[i - 1].dt;
            mRawBuffer[i].lin_vel_x = mRawBuffer[i - 1].lin_vel_x;
            mRawBuffer[i].lin_vel_y = mRawBuffer[i - 1].lin_vel_y;
            mRawBuffer[i].lin_vel_z = mRawBuffer[i - 1].lin_vel_z;
            mRawBuffer[i].ang_vel_x = mRawBuffer[i - 1].ang_vel_x;
            mRawBuffer[i].ang_vel_y = mRawBuffer[i - 1].ang_vel_y;
            mRawBuffer[i].ang_vel_z = mRawBuffer[i - 1].ang_vel_z;
        }

        mRawBuffer[0] = IsRawData();
        mRawBuffer[0].time = time;
        mRawBuffer[0].dt = dt;
        mRawBuffer[0].lin_vel_x = (float)(v_b[0]);
        mRawBuffer[0].lin_vel_y = (float)(v_b[1]);
        mRawBuffer[0].lin_vel_z = (float)(v_b[2]);
        mRawBuffer[0].ang_vel_x = (float)(w_b[0]);
        mRawBuffer[0].ang_vel_y = (float)(w_b[1]);
        mRawBuffer[0].ang_vel_z = (float)(w_b[2]);

        // signal processing
        mCurrent ^= 1;
        mReadingPair[mCurrent].time = time;
        // ang_vel output strategy: average past ANG_VEL_AVERAGE_NUM timesteps
        float tmp_sum_x = 0, tmp_sum_y = 0, tmp_sum_z = 0;
        for (int i = 0; i < ANG_VEL_AVERAGE_NUM; i++)
        {
            tmp_sum_x += mRawBuffer[i].ang_vel_x;
            tmp_sum_y += mRawBuffer[i].ang_vel_y;
            tmp_sum_z += mRawBuffer[i].ang_vel_z;
        }
        mReadingPair[mCurrent].ang_vel_x = tmp_sum_x / ANG_VEL_AVERAGE_NUM;
        mReadingPair[mCurrent].ang_vel_y = tmp_sum_y / ANG_VEL_AVERAGE_NUM;
        mReadingPair[mCurrent].ang_vel_z = tmp_sum_z / ANG_VEL_AVERAGE_NUM;
        // lin acc output strategy: average LIN_ACC_AVERAGE_NUM finite diffs
        // say if LIN_ACC_AVERAGE_NUM = 2, we do (([0] - [2]) / (2dt) + ([1] - [3]) / (2dt))/2
        tmp_sum_x = 0;
        tmp_sum_y = 0;
        tmp_sum_z = 0;
        for (int i = 0; i < LIN_ACC_AVERAGE_NUM; i++)
        {
            dt = mRawBuffer[i].time - mRawBuffer[i + LIN_ACC_AVERAGE_NUM].time;
            if (dt > 1e-10)
            {
                tmp_sum_x += (mRawBuffer[i].lin_vel_x - mRawBuffer[i + LIN_ACC_AVERAGE_NUM].lin_vel_x) / dt;
                tmp_sum_y += (mRawBuffer[i].lin_vel_y - mRawBuffer[i + LIN_ACC_AVERAGE_NUM].lin_vel_y) / dt;
                tmp_sum_z += (mRawBuffer[i].lin_vel_z - mRawBuffer[i + LIN_ACC_AVERAGE_NUM].lin_vel_z) / dt;
            }
        }
        // average acc
        mReadingPair[mCurrent].lin_acc_x = tmp_sum_x / LIN_ACC_AVERAGE_NUM;
        mReadingPair[mCurrent].lin_acc_y = tmp_sum_y / LIN_ACC_AVERAGE_NUM;
        mReadingPair[mCurrent].lin_acc_z = tmp_sum_z / LIN_ACC_AVERAGE_NUM;
        // add gravity
        mReadingPair[mCurrent].lin_acc_x += (float)(g_b[0]);
        mReadingPair[mCurrent].lin_acc_y += (float)(g_b[1]);
        mReadingPair[mCurrent].lin_acc_z += (float)(g_b[2]);

        mProcessedReadings = false;
    }
}

size_t IMUSensor::getNumReadings()
{
    if (!mProcessedReadings)
    {
        size_t size;
        getSensorReadings(size);
    }
    return mSensorReadings.size();
}

IsReading* IMUSensor::getSensorReadings(size_t& num_readings)
{
    if (mProps.sensorPeriod > 0)
    {
        if (!mProcessedReadings)
        {
            float start = mReadingPair[!mCurrent].time;
            float end = mReadingPair[mCurrent].time;
            mSensorReadings.clear();
            // when sensorPeriod is much shorter than simulation dt, more than 1 readings are returned
            while (mCurrentTime < end)
            {
                float time_pos = (mCurrentTime - start) / (end - start);
                IsReading reading;
                reading.time = mCurrentTime;
                reading.lin_acc_x = lerp(mReadingPair[!mCurrent].lin_acc_x, mReadingPair[mCurrent].lin_acc_x, time_pos);
                reading.lin_acc_y = lerp(mReadingPair[!mCurrent].lin_acc_y, mReadingPair[mCurrent].lin_acc_y, time_pos);
                reading.lin_acc_z = lerp(mReadingPair[!mCurrent].lin_acc_z, mReadingPair[mCurrent].lin_acc_z, time_pos);

                reading.ang_vel_x = lerp(mReadingPair[!mCurrent].ang_vel_x, mReadingPair[mCurrent].ang_vel_x, time_pos);
                reading.ang_vel_y = lerp(mReadingPair[!mCurrent].ang_vel_y, mReadingPair[mCurrent].ang_vel_y, time_pos);
                reading.ang_vel_z = lerp(mReadingPair[!mCurrent].ang_vel_z, mReadingPair[mCurrent].ang_vel_z, time_pos);

                mSensorReadings.push_back(reading);
                mCurrentTime += mProps.sensorPeriod;
            }
            mProcessedReadings = true;
        }
    }
    else
    {
        mSensorReadings.clear();
        mSensorReadings.push_back(mReadingPair[mCurrent]);
    }
    num_readings = mSensorReadings.size();
    // IS_LOG_INFO("Num Readings :%ld", num_readings);
    return mSensorReadings.data();
}


void onPhysicsUpdate(omni::physx::SimulationStatusEvent eventStatus, void* userData)
{
    if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationStarting)
    {
        // IS_LOG_INFO("Simulation starting");
    }
    if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationEnded)
    {
        // IS_LOG_INFO("Simulation Ended");
    }
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    // cast manager back, and call its step handler
    IMUManager* imuManager = (IMUManager*)userData;
    imuManager->onPhysicsStep(timeElapsed);
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("IMU sensor could not find USD stage");
        return;
    }

    gStage = stage;
}

static void onDetach(void* userData)
{
    // cast manager back
    IMUManager* imuManager = reinterpret_cast<IMUManager*>(userData);
    imuManager->clearAllSensors();
}

static void onStop(void* userData)
{
    // cast manager back
    IMUManager* imuManager = reinterpret_cast<IMUManager*>(userData);
    imuManager->resetSensors();
}

static void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    IMUManager* imuManager = reinterpret_cast<IMUManager*>(userData);
    imuManager->removeAllSensorsFromBody(primPath.GetText());
}

void IMUManager::removeAllSensorsFromBody(const char* usdPath)
{
    pxr::SdfPath path(usdPath);
    const auto& it = mPrimSensorMap.find(path.GetToken());
    if (it != mPrimSensorMap.end())
    {
        for (auto ishandle : it->second)
        {
            mSensorHandleMap.erase(ishandle);
        }
        mPrimSensorMap.erase(it);
    }
}

IMUManager::IMUManager(omni::physx::IPhysx* physxInterface)
{
    // setup the physx simulation callback
    mStepSubscription = physxInterface->subscribePhysicsStepEvents(omni::isaac::imu_sensor::onPhysicsStep, this);
    mEventSubscription = physxInterface->subscribePhysicsSimulationEvents(onPhysicsUpdate, this);


    // mStageCallbackPtr = carb::events::createSubscriptionToPop()
}

void IMUManager::unSubscribeEvents(omni::physx::IPhysx* physxInterface)
{
    physxInterface->unsubscribePhysicsStepEvents(mStepSubscription);
    physxInterface->unsubscribePhysicsSimulationEvents(mEventSubscription);
}

void IMUManager::onPhysicsStep(float timeElapsed)
{
    mCurrentTime += timeElapsed;
    mCurrentDt = timeElapsed;
    // IS_LOG_INFO("Update %f, %f", mCurrentTime, timeElapsed)
    for (auto& it : mSensorHandleMap)
    {
        it.second.update(mCurrentTime, timeElapsed);
    }
}

void IMUManager::resetSensors()
{
    // IS_LOG_INFO("Reset Sensors")
    for (auto& it : mSensorHandleMap)
    {
        it.second.reset();
    }
    mCurrentTime = 0.0f;
}

IsHandle IMUManager::addSensor(const char* usdPath, IsProperties props)
{
    pxr::SdfPath path(usdPath);
    auto stage = omni::usd::UsdContext::getContext()->getStage();
    // IS_LOG_INFO("Adding sensor on %s", usdPath);
    auto targetPrim = stage->GetPrimAtPath(path);
    if (targetPrim)
    {
        // IS_LOG_INFO("Prim Found");


        // Add sensor in the list
        IsHandle newSensorHandle = ++mNextId;
        mSensorHandleMap[newSensorHandle] = IMUSensor(path.GetToken());
        mSensorHandleMap[newSensorHandle].initialize(props);
        mPrimSensorMap[path.GetToken()].push_back(newSensorHandle);
        return newSensorHandle;
    }

    return kIsInvalidHandle;
}

IsHandle* IMUManager::getSensorsOnBody(const char* usdPath, size_t& num_sensors)
{
    pxr::SdfPath path(usdPath);
    if (mPrimSensorMap.find(path.GetToken()) != mPrimSensorMap.end())
    {
        num_sensors = mPrimSensorMap[path.GetToken()].size();
        return mPrimSensorMap[path.GetToken()].data();
    }
    return nullptr;
}

bool IMUManager::removeSensor(IsHandle sensor)
{
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        mPrimSensorMap[mSensorHandleMap[sensor].getBody()].erase(
            std::remove(mPrimSensorMap[mSensorHandleMap[sensor].getBody()].begin(),
                        mPrimSensorMap[mSensorHandleMap[sensor].getBody()].end(), sensor));
        mSensorHandleMap.erase(sensor);
        return true;
    }
    return false;
}

IsReading* IMUManager::getSensorReadings(IsHandle sensor, size_t& num_readings)
{
    // IS_LOG_INFO("Get Sensor Readings %ld", sensor);
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        // IS_LOG_INFO("Sensor Found");
        return mSensorHandleMap[sensor].getSensorReadings(num_readings);
    }
    num_readings = 0;
    return nullptr;
}

IsReading IMUManager::getSensorSimReading(IsHandle sensor)
{
    // IS_LOG_INFO("Get Sensor Sim Readings %ld", sensor);
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        // IS_LOG_INFO("Sensor Found");
        return mSensorHandleMap[sensor].getSimReading();
    }
    return IsReading();
}

void IMUManager::clearAllSensors()
{
    mPrimSensorMap.clear();
    mSensorHandleMap.clear();
}


}
}
}
// end of namespace imu_sensor

CARB_EXPORT void carbOnPluginStartup()
{
    using namespace omni::isaac::imu_sensor;

    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        IS_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    gPhysXInterface = framework->acquireInterface<omni::physx::IPhysx>();
    if (!gPhysXInterface)
    {
        IS_LOG_ERROR("Failed to acquire PhysX` interface");
        return;
    }

    gIMUManager = new IMUManager(gPhysXInterface);

    if (gStageUpdate == nullptr)
    {
        gStageUpdate = framework->acquireInterface<omni::kit::IStageUpdate>();
        if (gStageUpdate != nullptr)
        {
            omni::kit::StageUpdateNodeDesc desc = { 0 };
            desc.displayName = "IMUManager";
            desc.userData = gIMUManager;
            desc.onAttach = onAttach;
            desc.onDetach = onDetach;
            desc.onPrimRemove = onPrimRemove;
            desc.onStop = onStop;

            gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
            if (gStageUpdateNode == nullptr)
            {
                framework->releaseInterface(gStageUpdate);
                gStageUpdate = nullptr;
            }
        }
    }
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (gIMUManager)
    {
        if (gPhysXInterface)
            gIMUManager->unSubscribeEvents(gPhysXInterface);
        delete gIMUManager;
        gIMUManager = nullptr;
    }
    if (gPhysXInterface)
    {
        carb::Framework* framework = carb::getFramework();
        if (framework)
        {
            framework->releaseInterface(gPhysXInterface);
        }
    }
    if (gStageUpdate != nullptr)
    {
        if (gStageUpdateNode != nullptr)
        {
            gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
            gStageUpdateNode = nullptr;
        }
        carb::Framework* framework = carb::getFramework();
        if (framework)
        {
            framework->releaseInterface(gStageUpdate);
        }
        gStageUpdate = nullptr;
    }
}

using namespace omni::isaac::imu_sensor;

CARB_EXPORT size_t IsGetNumSensorsOnBody(const char* usdPath)
{
    size_t num_sensors = 0;
    if (gIMUManager)
    {
        gIMUManager->getSensorsOnBody(usdPath, num_sensors);
    }
    return num_sensors;
}

CARB_EXPORT IsHandle* IsGetSensorsOnBody(const char* usdPath, size_t& num_sensors)
{
    IsHandle* sensors = nullptr;
    num_sensors = 0;
    if (gIMUManager)
    {
        sensors = gIMUManager->getSensorsOnBody(usdPath, num_sensors);
    }

    return sensors;
}

CARB_EXPORT size_t IsGetSensorReadingsSize(const IsHandle sensor)
{
    size_t num_readings = 0;
    if (gIMUManager)
    {
        gIMUManager->getSensorReadings(sensor, num_readings);
    }
    return num_readings;
}

CARB_EXPORT IsReading* IsGetSensorReadings(const IsHandle sensor, size_t& num_readings)
{
    num_readings = 0;
    IsReading* data = nullptr;
    if (gIMUManager)
    {
        data = gIMUManager->getSensorReadings(sensor, num_readings);
    }
    return data;
}


CARB_EXPORT IsReading IsGetSensorSimReading(const IsHandle sensor)
{
    IsReading data;
    if (gIMUManager)
    {
        data = gIMUManager->getSensorSimReading(sensor);
    }
    return data;
}

CARB_EXPORT IsHandle IsAddSensorOnBody(const char* usdPath, const IsProperties props)
{
    IsHandle handle = kIsInvalidHandle;
    if (gIMUManager)
    {
        handle = gIMUManager->addSensor(usdPath, props);
        // IS_LOG_INFO("Added IMU sensor %ld", handle);
    }
    return handle;
}

CARB_EXPORT bool IsRemoveSensor(IsHandle sensor)
{
    if (gIMUManager)
    {
        return gIMUManager->removeSensor(sensor);
    }
    return false;
}

void fillInterface(omni::isaac::imu_sensor::IMUSensorInterface& iface)
{
    using namespace omni::isaac::imu_sensor;

    memset(&iface, 0, sizeof(iface));

    iface.getNumSensorsOnBody = IsGetNumSensorsOnBody;
    iface.getSensorsOnBody = IsGetSensorsOnBody;

    iface.getSensorReadingsSize = IsGetSensorReadingsSize;
    iface.getSensorReadings = IsGetSensorReadings;
    iface.getSensorSimReading = IsGetSensorSimReading;

    iface.addSensorOnBody = IsAddSensorOnBody;
    iface.removeSensor = IsRemoveSensor;
}
