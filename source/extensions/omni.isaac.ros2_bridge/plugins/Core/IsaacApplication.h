// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "IsaacComponent.h"
#include "RosNode.h"
#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/bridge/ViewportManager.h"
#include "omni/isaac/ros/RosApplication.h"

#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IViewport.h>
#include <rosBridgeSchema/rosBridgeComponent.h>

#include <chrono>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>


namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
class IsaacApplication : public ros_base::RosApplication<IsaacComponent>
{
public:
    /**
     * @brief Construct a new Application object
     *
     * @param dynamicControlPtr
     */
    IsaacApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
        : ros_base::RosApplication<IsaacComponent>(dynamicControlPtr)
    {
    }


    virtual void onComponentAdd(const pxr::UsdPrim& prim);
};
}
}
}
