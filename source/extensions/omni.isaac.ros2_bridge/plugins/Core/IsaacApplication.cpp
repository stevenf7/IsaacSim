// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

}
}
}
