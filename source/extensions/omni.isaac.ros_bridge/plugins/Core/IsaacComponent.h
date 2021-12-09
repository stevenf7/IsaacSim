// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "RosNode.h"
#include "omni/isaac/bridge/Component.h"
#include "omni/isaac/ros/RosComponent.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/profiler/Profile.h>

#include <rosBridgeSchema/rosBridgeComponent.h>

#include <chrono>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <typename PrimType, typename NodeType>
class IsaacComponentBase : public ros_base::RosComponentBase<PrimType, NodeType>
{
public:
    virtual ~IsaacComponentBase()
    {
    }

protected:
    /**
     * @brief Set the Ros Time Stamp object
     *
     * @param stamp
     */
    void setRosTimeStamp(ros::Time& stamp)
    {
        // This is a global flag set for all ROS components
        if (this->mUseSimTime)
        {
            if (this->mUsePhysicsStepSimTime)
            {
                stamp.fromSec(this->mPhysicsTimeSeconds);
            }
            else
            {
                stamp.fromSec(this->mTimeSeconds);
            }
        }
        else
        {
            stamp.fromNSec(this->mSystemTimeNanoSeconds);
        }
    }
};


typedef IsaacComponentBase<pxr::RosBridgeSchemaRosBridgeComponent, RosNode> IsaacComponent;


}
}
}
