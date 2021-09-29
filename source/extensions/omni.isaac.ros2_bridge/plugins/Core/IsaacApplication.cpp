// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "../Components/RosCamera.h"
#include "../Components/RosClock.h"
#include "../Components/RosDifferentialBase.h"
#include "../Components/RosJointState.h"
#include "../Components/RosLidar.h"
#include "../Components/RosPoseTree.h"
#include "../Components/RosSurfaceGripper.h"
#include "../Components/RosTeleport.h"
#include "omni/isaac/utils/ScopedTimer.h"
#include "rclcpp/rclcpp.hpp"

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
IsaacApplication::IsaacApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
{
    mDynamicControlPtr = dynamicControlPtr;
    carb::Framework* framework = carb::getFramework();
    mTasking = framework->acquireInterface<carb::tasking::ITasking>();
    mTaskCounter = mTasking->createCounter();
    mViewportInterface = framework->acquireInterface<omni::kit::IViewport>();
}


IsaacApplication::~IsaacApplication()
{
    mTasking->yieldUntilCounter(mTaskCounter);
    mTasking->destroyCounter(mTaskCounter);

    deleteAllComponents();
}

void IsaacApplication::initialize(pxr::UsdStageWeakPtr stage)
{
    utils::BridgeApplicationBase<IsaacComponent>::initialize(stage);
    mViewportManager = std::make_unique<utils::ViewportManager>(mViewportInterface);
}


void IsaacApplication::tick(double dt)
{
    // System time is calculated the start of the frame
    mSystemTimeNanoSeconds =
        std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();

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
        component.second.get()->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mSystemTimeNanoSeconds);
    }

    for (auto& component : mComponents)
    {
        if (component.second->getEnabled())
        {
            component.second->tick();
        }
    }
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
    if (prim.IsA<pxr::RosBridgeSchemaRosClock>())
    {
        component = std::make_unique<RosClock>();
        component->initialize(nullptr, pxr::RosBridgeSchemaRosClock(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosCamera>())
    {
        component = std::make_unique<RosCamera>(mViewportManager.get());
        component->initialize(nullptr, pxr::RosBridgeSchemaRosCamera(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosJointState>())
    {
        component = std::make_unique<RosJointState>(mDynamicControlPtr);
        component->initialize(nullptr, pxr::RosBridgeSchemaRosJointState(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosLidar>())
    {
        component = std::make_unique<RosLidar>();
        component->initialize(nullptr, pxr::RosBridgeSchemaRosLidar(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosPoseTree>())
    {
        component = std::make_unique<RosPoseTree>(mDynamicControlPtr);
        component->initialize(nullptr, pxr::RosBridgeSchemaRosPoseTree(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosTeleport>())
    {
        component = std::make_unique<RosTeleport>(mDynamicControlPtr);
        component->initialize(nullptr, pxr::RosBridgeSchemaRosTeleport(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosSurfaceGripper>())
    {
        component = std::make_unique<RosSurfaceGripper>(mDynamicControlPtr);
        component->initialize(nullptr, pxr::RosBridgeSchemaRosSurfaceGripper(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosDifferentialBase>())
    {
        component = std::make_unique<RosDifferentialBase>(mDynamicControlPtr);
        component->initialize(nullptr, pxr::RosBridgeSchemaRosDifferentialBase(prim), mStage);
    }
    if (component)
    {
        CARB_LOG_INFO("Create: Prim %s with type: %s", prim.GetPath().GetString().c_str(),
                      component->getPrim().GetPrim().GetTypeName().GetString().c_str());
        component->setUseSimTime(mUseSimTime);
        mComponents[prim.GetPath().GetString()] = std::move(component);
    }
}


void IsaacApplication::onPhysicsStep(float dt)
{
    for (auto& component : mComponents)
    {
        component.second->onPhysicsStep(dt);
    }
}


void IsaacApplication::setUseSimTime(const bool useSimTime)
{
    mUseSimTime = useSimTime;
    for (auto& component : mComponents)
    {
        component.second.get()->setUseSimTime(mUseSimTime);
    }
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

            component->tick();
            return true;
        }
    }
    return false;
}
}
}
}
