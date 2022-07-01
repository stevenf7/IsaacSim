// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "IsaacApplication.h"

#include "../Actuator/DifferentialBaseSimulator.h"
#include "../Actuator/HolonomicBaseSimulator.h"
#include "../Actuator/JointControl.h"
#include "../Actuator/ScissorLiftSimulator.h"
#include "../Actuator/SurfaceGripper.h"
#include "../Actuator/TwoFingerGripper.h"
#include "../Actuator/VehicleSimulator.h"
#include "../Monitor/ContactMonitor.h"
#include "../Monitor/RigidBodiesSink.h"
#include "../Scenario/ScenarioFromMessage.h"
#include "../Scenario/SceneLoader.h"
#include "../Sensor/CameraComponent.h"
#include "../Sensor/LidarComponent.h"
#include "../Sensor/OccupancyGridMapComponent.h"
#include "../Sensor/UltrasonicComponent.h"
#include "../Visualizer/PolylineVisualizer.h"
#include "core/logger.hpp"
#include "omni/isaac/utils/ScopedTimer.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
IsaacApplication::IsaacApplication(IsaacCApi* isaacCApiPtr,
                                   omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                                   carb::dictionary::ISerializer* jsonSerializer,
                                   carb::dictionary::IDictionary* iDict)
{
    mIsaacCApiPtr = isaacCApiPtr;
    mDynamicControlPtr = dynamicControlPtr;
    mJsonSerializer = jsonSerializer;
    mIDict = iDict;
    mTasking = carb::getCachedInterface<carb::tasking::ITasking>();
    mTaskCounter = mTasking->createCounter();
    mSettings = carb::getCachedInterface<carb::settings::ISettings>();
    mSettings->setDefaultInt("/exts/omni.isaac.robot_engine_bridge/IsaacSDKLogLevel", 3);
    mViewportInterface = carb::getCachedInterface<omni::kit::IViewport>();
}


IsaacApplication::~IsaacApplication()
{
    mTasking->wait(mTaskCounter);
    mTasking->destroyCounter(mTaskCounter);

    deleteAllComponents();
    stop();
    destroy();
    mIsaacCApiPtr = nullptr;
    mSceneLoaderComponent = nullptr;
}

void IsaacApplication::initialize(pxr::UsdStageWeakPtr stage)
{
    utils::BridgeApplicationBase<IsaacComponent>::initialize(stage);

    mSceneLoaderComponent = std::make_unique<SceneLoader>(mDynamicControlPtr, mJsonSerializer, mIDict);
    pxr::RobotEngineBridgeSchemaRobotEngineBridgeComponent prim;
    mSceneLoaderComponent->initialize(mIsaacCApiPtr, mAppHandle, prim, mStage);

    mViewportManager = std::make_unique<utils::ViewportManager>(mViewportInterface);
}

isaac_error_t IsaacApplication::create(std::string assetPath,
                                       std::string appFile,
                                       std::vector<const char*> modulePaths,
                                       std::vector<const char*> jsonFiles)
{
    if (mAppHandle == 0)
    {
        int logLevel = mSettings->get<int>("/exts/omni.isaac.robot_engine_bridge/IsaacSDKLogLevel");
        ::isaac::logger::SetSeverity(static_cast<::isaac::logger::Severity>(logLevel));
        mError =
            (mIsaacCApiPtr->isaac_create_application)(assetPath.c_str(), appFile.c_str(), &modulePaths[0],
                                                      modulePaths.size(), &jsonFiles[0], jsonFiles.size(), &mAppHandle);
    }
    else
    {
        CARB_LOG_WARN("Application Already Created, Destroy before creating again");
        return isaac_error_t::isaac_error_unknown;
    }

    if (mError != isaac_error_t::isaac_error_success)
    {
        mAppHandle = 0;
        CARB_LOG_ERROR("Application Was Not Created Successfully");
        return mError;
    }
    for (auto& component : mComponents)
    {
        component.second.get()->setAppHandle(mAppHandle);
    }
    mSceneLoaderComponent->setAppHandle(mAppHandle);
    return isaac_error_t::isaac_error_success;
}

isaac_error_t IsaacApplication::start()
{
    if (mAppHandle == 0)
    {
        CARB_LOG_ERROR("Cannot Start application that is not created");
        return isaac_error::isaac_error_unknown;
    }

    mError = (mIsaacCApiPtr->isaac_start_application)(mAppHandle);

    if (mError != isaac_error_t::isaac_error_success)
    {
        CARB_LOG_ERROR("Application Was Not Started Successfully");
        return mError;
    }
    mRunning = true;
    return isaac_error_t::isaac_error_success;
}

isaac_error_t IsaacApplication::stop()
{
    mRunning = false;
    if (mAppHandle != 0)
    {
        mError = (mIsaacCApiPtr->isaac_stop_application)(mAppHandle);
        if (mError != isaac_error_t::isaac_error_success)
        {
            CARB_LOG_ERROR("Application Was Not Stopped Successfully");
            return mError;
        }
        return isaac_error_t::isaac_error_success;
    }
    else
    {
        // CARB_LOG_WARN("Cannot Stop application that is not created");
        return isaac_error::isaac_error_unknown;
    }
}

isaac_error_t IsaacApplication::destroy()
{
    // Apps must be stopped before they are destroyed
    if (mRunning)
    {
        mError = stop();
        // Stop will also fail if the application is not created
        if (mError != isaac_error_t::isaac_error_success)
        {
            CARB_LOG_ERROR("Application Was Not Destroyed Successfully");
            return mError;
        }
    }

    // Only destroy an app if we have a valid handle to it
    if (mAppHandle != 0)
    {
        mError = (mIsaacCApiPtr->isaac_destroy_application)(&mAppHandle);
        if (mError != isaac_error_t::isaac_error_success)
        {
            CARB_LOG_ERROR("Application Was Not Destroyed Successfully");
            return mError;
        }
    }
    mAppHandle = 0;
    for (auto& component : mComponents)
    {
        component.second.get()->setAppHandle(mAppHandle);
    }
    // If we destroy before attaching to a stage we never initialized the scene loader component
    if (mSceneLoaderComponent)
    {
        mSceneLoaderComponent->setAppHandle(mAppHandle);
    }
    return isaac_error_t::isaac_error_success;
}

void IsaacApplication::initializeStageLoader(const std::string& inputComponent,
                                             const std::string& requestChannelName,
                                             const std::string& cameraRequestChannelName,
                                             const std::string& outputComponent,
                                             const std::string& replyChannelName)
{
    CARB_LOG_INFO("Initialize Stage Loader");

    mSceneLoaderComponent->initializeParams(
        inputComponent, requestChannelName, cameraRequestChannelName, outputComponent, replyChannelName);
}

/**
 * @brief Data used by a task thread
 *
 */
struct TaskData
{
    IsaacComponent* component;
};
/**
 * @brief Function called by each task thread
 *
 */
auto TaskFunction = [](void* taskArg)
{
    TaskData* taskData = reinterpret_cast<TaskData*>(taskArg);
    if (taskData->component->getEnabled())
    {
        taskData->component->publishAllMessages();
        // taskData->component->tick();
    }
};

void IsaacApplication::tick(double dt)
{
    if (!mAppHandle)
    {
        return;
    }
    CARB_PROFILE_ZONE(0, "REB IsaacApplication Tick");
    // omni::isaac::utils::ScopedTimer TimerApp("IsaacApplication");
    // only update time difference to bridge app if the step size is greater than zero
    if (dt > 0)
    {
        mError =
            (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &mTimeDifferenceNanoSeconds);
    }
    if (mRunning)
    {

        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                component.second->IsaacComponent::onComponentChange();
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
        }


        for (auto& component : mComponents)
        {
            component.second.get()->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
        }

#if 1
        // omni::isaac::utils::ScopedTimer TimerApp("  Publish");
        TaskData* taskArray = new TaskData[mComponents.size()];
        int index = 0;
        for (auto& component : mComponents)
        {
            taskArray[index].component = component.second.get();

            mTasking->addTask(carb::tasking::Priority::eHigh, mTaskCounter, TaskFunction, (void*)(taskArray + index));
            index++;
        }

        for (auto& component : mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second->tick();
            }
        }

        mTasking->wait(mTaskCounter);
        delete[] taskArray;

#else

        for (auto& component : mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second->publishAllMessages();
                component.second->tick();
            }
        }
#endif


        mSceneLoaderComponent->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
        mSceneLoaderComponent->tick();
    }
    // TODO: do this before or after tick?
    mTimeSeconds += dt;
    mTimeNanoSeconds = mTimeSeconds * 1e9;
}

void IsaacApplication::onStop()
{

    for (auto& component : mComponents)
    {
        component.second->onStop();
        component.second->mDoStart = true;
    }
}

void IsaacApplication::onComponentAdd(const pxr::UsdPrim& prim)
{
    std::unique_ptr<IsaacComponent> component;

    if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineDifferentialBase>())
    {
        component = std::make_unique<DifferentialBaseSimulator>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineDifferentialBase(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineHolonomicBase>())
    {
        component = std::make_unique<HolonomicBaseSimulator>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineHolonomicBase(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineVehicle>())
    {
        component = std::make_unique<VehicleSimulator>();
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineVehicle(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineLidar>())
    {
        component = std::make_unique<LidarComponent>();
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineLidar(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic>())
    {
        component = std::make_unique<UltrasonicComponent>();
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineScenarioFromMessage>())
    {
        component = std::make_unique<ScenarioFromMessage>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineScenarioFromMessage(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink>())
    {
        component = std::make_unique<RigidBodiesSink>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineTeleport>())
    {
        component = std::make_unique<Teleport>(mDynamicControlPtr);
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineTeleport(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineJointControl>())
    {
        component = std::make_unique<JointControl>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineJointControl(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineScissorLift>())
    {
        component = std::make_unique<ScissorLiftSimulator>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineScissorLift(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineSurfaceGripper>())
    {
        component = std::make_unique<SurfaceGripper>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineSurfaceGripper(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineCamera>())
    {
        component = std::make_unique<CameraComponent>(mViewportManager.get());
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineCamera(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineOccupancyGridMap>())
    {
        component = std::make_unique<OccupancyGridMapComponent>();
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineOccupancyGridMap(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineContactMonitor>())
    {
        component = std::make_unique<ContactMonitor>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineContactMonitor(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineTwoFingerGripper>())
    {
        component = std::make_unique<TwoFingerGripper>(mDynamicControlPtr);
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineTwoFingerGripper(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEnginePolylineVisualizer>())
    {
        component = std::make_unique<PolylineVisualizer>();
        component->initialize(
            mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEnginePolylineVisualizer(prim), mStage);
    }
    if (component)
    {
        CARB_LOG_INFO("Create: Prim %s with type: %s", prim.GetPath().GetString().c_str(),
                      component->getPrim().GetPrim().GetTypeName().GetString().c_str());
        mComponents[prim.GetPath().GetString()] = std::move(component);
    }
}

isaac_handle_t IsaacApplication::getHandle()
{
    return mAppHandle;
}

std::string IsaacApplication::getLastError()
{
    return std::string((mIsaacCApiPtr->isaac_get_error_message(mError)));
}

bool IsaacApplication::tickComponent(const pxr::UsdPrim& prim)
{
    if (prim)
    {
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            auto* component = mComponents[prim.GetPath().GetString()].get();


            if (component->mDoStart == true)
            {
                component->onStart();
                component->mDoStart = false;
            }

            component->publishAllMessages();
            component->tick();
            return true;
        }
    }
    return false;
}


bool checkErrorCode(const isaac_error_t& code)
{
    return code == isaac_error_t::isaac_error_success;
}

bool IsaacApplication::publishJsonMessage(
    std::string node, std::string component, std::string channel, uint64_t typeID, std::string jsonString)
{

    if (!mAppHandle)
    {
        CARB_LOG_WARN("Cannot publish message unless application application was created");
        return false;
    }

    isaac_uuid_t uuid;
    isaac_error_t mError = (mIsaacCApiPtr->isaac_create_message)(mAppHandle, &uuid);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    isaac_const_json_t json = { jsonString.c_str(), jsonString.size() };
    mError = (mIsaacCApiPtr->isaac_write_message_json)(mAppHandle, &uuid, &json);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    int64_t timeDifferenceNano = 0;

    mError = (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &timeDifferenceNano);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    mError = (mIsaacCApiPtr->isaac_set_message_acqtime)(mAppHandle, &uuid, mTimeNanoSeconds + timeDifferenceNano);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    mError = (mIsaacCApiPtr->isaac_set_message_proto_id)(mAppHandle, &uuid, typeID);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    mError = (mIsaacCApiPtr->isaac_set_message_auto_convert)(
        mAppHandle, &uuid, isaac_message_convert_t::isaac_message_type_proto);
    if (!checkErrorCode(mError))
    {
        return false;
    }
    mError = (mIsaacCApiPtr->isaac_publish_message)(mAppHandle, node.c_str(), component.c_str(), channel.c_str(), &uuid);
    if (!checkErrorCode(mError))
    {
        (mIsaacCApiPtr->isaac_destroy_message)(mAppHandle, &uuid);
        return false;
    }

    return true;
}
}
}
}
