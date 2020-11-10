

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
class RosSubscriber : public RosMessenger
{
public:
    explicit RosSubscriber()
    {
        event_type = eRosEventSubscribe;
    }

    ~RosSubscriber()
    {
        if (sub_)
        {
            sub_->shutdown();
        }
        sub_ = nullptr;
    }

    RosSubscriber(const RosSubscriber&) = delete;
    RosSubscriber& operator=(const RosSubscriber&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node,
              const std::string& topic,
              const int queueSize,
              void (Callback::*callbackFn)(const typename MessageType::ConstPtr&),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = queueSize;
        sub_ = std::make_unique<ros::Subscriber>();
        *sub_ = node->subscribe<MessageType>(topic, queueSize, callbackFn, object);
    }
    std::unique_ptr<ros::Subscriber> sub_;

private:
};
}
}
}
