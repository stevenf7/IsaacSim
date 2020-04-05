// Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <string>
#include <vector>

namespace omni
{

namespace isaac
{

namespace ros_bridge
{

// handle to an object inside of an Isaac Plugin
typedef int IsaacHandle;

enum RosEventType
{
    eRosEventNone,
    eRosEventPublish,
    eRosEventSubscribe,
    eRosEventService,
    eRosEventPeriodic,
};

enum RosMessageType
{
    eRosMessageNone,
    eRosMessageEmpty,
    eRosMessagePose,
    eRosMessageJointState,
    eRosMessageTf,
    eRosMessageImage,
    eRosMessageCameraInfo,
    eRosMessageBoundingBox,
    eRosMessageRangeScan
};


struct RosBridge
{
    CARB_PLUGIN_INTERFACE("omni::isaac::ros_bridge::RosBridge", 0, 1);

    IsaacHandle(CARB_ABI* addRosNode)();
    IsaacHandle(CARB_ABI* addRosEvent)(IsaacHandle node_handle,
                                       const std::vector<std::string> paths,
                                       std::string topic,
                                       const int queue_size,
                                       RosMessageType message_type,
                                       RosEventType event_type);

    bool(CARB_ABI* deleteRosNode)(IsaacHandle node_handle);
    bool(CARB_ABI* deleteRosEvent)(IsaacHandle node_handle, IsaacHandle event_handle);

    void(CARB_ABI* setClockState)(const bool state);
    std::string(CARB_ABI* getJsonString)();
    void(CARB_ABI* parseJsonString)(std::string);
};
}
}
}
