#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/ros_bridge/RosBridge.h>
#include "RosNode.h"
#include "RosState.h"
#include "RosCallback.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <functional>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

class RosManager
{

public:
    explicit RosManager(RosGlobals* globals);
    RosManager(const RosManager&) = delete;
    RosManager& operator=(const RosManager&) = delete;
    ~RosManager();

    void start();
    void stop();
    void tick(const float dt = 0.0f);
    IsaacHandle addNode();
    bool deleteNode(const IsaacHandle node_handle);

    IsaacHandle addEvent(const IsaacHandle node_handle,
                         const std::vector<std::string>& paths,
                         std::string topic,
                         const int queue_size,
                         RosMessageType message_type,
                         RosEventType event_type);
    bool deleteEvent(const IsaacHandle node_handle, const IsaacHandle event_handle);

    void setClockState(const bool state);
    std::string getJsonString();
    void parseJsonString(std::string json_config);

private:
    std::unique_ptr<RosState> SimState;
    RosGlobals* globals_;
    std::vector<std::unique_ptr<RosNode>> ros_nodes_;
    tf2_ros::Buffer tf_buffer_;
    std::unique_ptr<tf2_ros::TransformListener> tf_listener_;
};
}
}
}
