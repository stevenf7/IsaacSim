// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "IsaacApplication.h"

#include "../Actuator/DifferentialBaseSimulator.h"
#include "../Actuator/JointControl.h"
#include "../Actuator/ScissorLiftSimulator.h"
#include "../Actuator/SurfaceGripper.h"
#include "../Scenario/ScenarioFromMessage.h"
#include "../Monitor/RigidBodiesSink.h"
#include "../Scenario/SceneLoader.h"
#include "../Sensor/LidarComponent.h"
#include "../Sensor/CameraComponent.h"

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

    mSceneLoaderComponent = std::make_unique<SceneLoader>(mDynamicControlPtr, mJsonSerializer, mIDict);
    pxr::UsdPrim prim;
    mSceneLoaderComponent->initialize(mIsaacCApiPtr, mAppHandle, prim, mStage);
}


IsaacApplication::~IsaacApplication()
{
    deleteAllComponents();
    stop();
    destroy();
    mIsaacCApiPtr = nullptr;
    mSceneLoaderComponent = nullptr;
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
                                             std::string outputComponent,
                                             std::string replyChannelName)
{
    mSceneLoaderComponent->initializeParams(inputComponent, requestChannelName, outputComponent, replyChannelName);
}

void IsaacApplication::tick(double dt)
{
    CARB_PROFILE_ZONE(0, "REB IsaacApplication Tick");

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
                component.second->tick();
            }
            mSceneLoaderComponent->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
            mSceneLoaderComponent->tick();
        }
    }
    // TODO: do this before or after tick?
    mTimeSeconds += dt;
    mTimeNanoSeconds = mTimeSeconds * 1e9;
}

void IsaacApplication::onComponentAdd(const pxr::UsdPrim& prim)
{
    std::unique_ptr<IsaacComponent> component;

    if (prim.GetTypeName() == "RobotEngine_DifferentialBaseSimulator")
    {
        component = std::make_unique<DifferentialBaseSimulator>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_Lidar")
    {
        component = std::make_unique<LidarComponent>();
    }
    else if (prim.GetTypeName() == "RobotEngine_ScenarioFromMessage")
    {
        component = std::make_unique<ScenarioFromMessage>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_RigidBodiesSink")
    {
        component = std::make_unique<RigidBodiesSink>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_JointControl")
    {
        component = std::make_unique<JointControl>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_ScissorLiftSimulator")
    {
        component = std::make_unique<ScissorLiftSimulator>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_SurfaceGripper")
    {
        component = std::make_unique<SurfaceGripper>(mDynamicControlPtr);
    }
    else if (prim.GetTypeName() == "RobotEngine_Camera")
    {
        component = std::make_unique<CameraComponent>();
    }
    if (component)
    {
        CARB_LOG_WARN("Create: Prim %s", prim.GetPath().GetString().c_str());
        component->initialize(mIsaacCApiPtr, mAppHandle, prim, mStage);
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
