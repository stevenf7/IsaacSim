

#pragma once


// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>
#include <functional>

#include "ros/callback_queue.h"
#include "ros/ros.h"
#include "../Core/RosMessenger.h"


namespace omni
{
namespace isaac
{
namespace ros_bridge
{
class RosPeriodic : public RosMessenger
{
public:
    explicit RosPeriodic()
    {
        event_type = eRosEventPeriodic;
    }
    ~RosPeriodic()
    {
        tickCallback_ = nullptr;
    }
    RosPeriodic(const RosPeriodic&) = delete;
    RosPeriodic& operator=(const RosPeriodic&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node, void (Callback::*callbackFn)(), Callback* object)
    {
        tickCallback_ = std::bind(callbackFn, object);
    }
    void tick()
    {
        tickCallback_();
    }

private:
    std::function<void()> tickCallback_ = nullptr;
};
}
}
}
