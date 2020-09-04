// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "IsaacApplication.h"

#include "../Actuator/DifferentialBaseSimulator.h"
#include "../Actuator/HolonomicBaseSimulator.h"
#include "../Actuator/VehicleSimulator.h"
#include "../Actuator/JointControl.h"
#include "../Actuator/ScissorLiftSimulator.h"
#include "../Actuator/SurfaceGripper.h"
#include "../Actuator/TwoFingerGripper.h"
#include "../Scenario/ScenarioFromMessage.h"
#include "../Monitor/RigidBodiesSink.h"
#include "../Scenario/SceneLoader.h"
#include "../Sensor/LidarComponent.h"
#include "../Sensor/CameraComponent.h"
#include "../Monitor/ContactMonitor.h"
#include "plugins/core/ScopedTimer.h"

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
    carb::Framework* framework = carb::getFramework();
    mTasking = framework->acquireInterface<carb::tasking::ITasking>();
    mTaskCounter = mTasking->createCounter();
}


IsaacApplication::~IsaacApplication()
{
    mTasking->yieldUntilCounter(mTaskCounter);
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
}

isaac_error_t IsaacApplication::create(std::string assetPath,
                                       std::string appFile,
                                       std::vector<const char*> modulePaths,
                                       std::vector<const char*> jsonFiles)
{
    if (mAppHandle == 0)
    {
        mError =
            (mIsaacCApiPtr->isaac_create_application)(assetPath.c_str(), appFile.c_str(), &modulePaths[0],
                                                      modulePaths.size(), &jsonFiles[0], jsonFiles.size(), &mAppHandle);
    }
    else
    {
        CARB_LOG_WARN("Application Already Created, Destroy before creating again");
    }

    if (mError != isaac_error_t::isaac_error_success)
    {
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
    if (mAppHandle == 0)
    {
        CARB_LOG_INFO("Cannot Stop application that is not created");
        return isaac_error::isaac_error_unknown;
    }
    mError = (mIsaacCApiPtr->isaac_stop_application)(mAppHandle);
    if (mError != isaac_error_t::isaac_error_success)
    {
        CARB_LOG_ERROR("Application Was Not Stopped Successfully");
        return mError;
    }
    return isaac_error_t::isaac_error_success;
}

isaac_error_t IsaacApplication::destroy()
{
    // Apps must be stopped before they are destroyed
    if (mRunning)
    {
        stop();
    }
    mError = (mIsaacCApiPtr->isaac_destroy_application)(&mAppHandle);
    if (mError != isaac_error_t::isaac_error_success)
    {
        CARB_LOG_ERROR("Application Was Not Destroyed Successfully");
        return mError;
    }
    mAppHandle = 0;
    for (auto& component : mComponents)
    {
        component.second.get()->setAppHandle(mAppHandle);
    }
    mSceneLoaderComponent->setAppHandle(mAppHandle);
    return isaac_error_t::isaac_error_success;
}

void IsaacApplication::initializeStageLoader(std::string inputComponent,
                                             std::string requestChannelName,
                                             std::string cameraRequestChannelName,
                                             std::string outputComponent,
                                             std::string replyChannelName)
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
auto TaskFunction = [](carb::tasking::ITasking* tasking, void* taskArg) {
    TaskData* taskData = reinterpret_cast<TaskData*>(taskArg);
    if (taskData->component->getEnabled())
    {
        taskData->component->publishAllMessages();
        // taskData->component->tick();
    }
};

void IsaacApplication::tick(double dt)
{
    CARB_PROFILE_ZONE(0, "REB IsaacApplication Tick");
    // omni::isaac::utils::ScopedTimer TimerApp("IsaacApplication");
    mError = (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &mTimeDifferenceNanoSeconds);
    if (mRunning)
    {
        if (mDoOnce == false)
        {
            for (auto& component : mComponents)
            {
                component.second->onStart();
            }
            mDoOnce = true;
        }
        else
        {
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

                carb::tasking::TaskDesc bigTask{};
                bigTask.priority = carb::tasking::Priority::eHigh;
                bigTask.task = TaskFunction;
                bigTask.taskArg = (void*)(taskArray + index);
                mTasking->addTask(bigTask, mTaskCounter);
                index++;
            }

            for (auto& component : mComponents)
            {
                if (component.second->getEnabled())
                {
                    component.second->tick();
                }
            }

            mTasking->yieldUntilCounter(mTaskCounter);
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
    }
    // TODO: do this before or after tick?
    mTimeSeconds += dt;
    mTimeNanoSeconds = mTimeSeconds * 1e9;
}

void IsaacApplication::onStop()
{
    utils::BridgeApplicationBase<IsaacComponent>::onStop();

    for (auto& component : mComponents)
    {
        component.second->onStop();
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
        component = std::make_unique<CameraComponent>();
        component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineCamera(prim), mStage);
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

}
}
}
