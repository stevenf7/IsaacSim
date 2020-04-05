

#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>
#include <functional>

#include "ros/callback_queue.h"
#include "ros/ros.h"
#include "../RosMessenger.h"


namespace omni
{
namespace isaac
{
namespace ros_bridge
{
class RosPublisher : public RosMessenger
{
public:
    explicit RosPublisher()
    {
        event_type = eRosEventPublish;
    }
    ~RosPublisher()
    {
        if (pub_)
        {
            pub_->shutdown();
        }
        pub_ = nullptr;
        pubCallback_ = nullptr;
    }
    RosPublisher(const RosPublisher&) = delete;
    RosPublisher& operator=(const RosPublisher&) = delete;

    template <typename MessageType, class Callback>
    void init(ros::NodeHandle* node,
              const std::string& topic,
              const int queueSize,
              void (Callback::*callbackFn)(ros::Publisher* pub),
              Callback* object)
    {
        topic_ = topic;
        queue_size_ = queueSize;
        pubCallback_ = std::bind(callbackFn, object, std::placeholders::_1);
        pub_ = std::make_unique<ros::Publisher>();
        *pub_ = node->advertise<MessageType>(topic, queueSize);
    }
    void publish()
    {
        if (pub_)
        {
            pubCallback_(pub_.get());
        }
    }

private:
    std::unique_ptr<ros::Publisher> pub_;
    std::function<void(ros::Publisher* pub)> pubCallback_ = nullptr;
};
}
}
}
