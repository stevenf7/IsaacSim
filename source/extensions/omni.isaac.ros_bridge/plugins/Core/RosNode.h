#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <functional>
#include <memory>
#include <vector>

#include "ros/callback_queue.h"
#include "ros/ros.h"
// #include "RosCallback.h"
#include "../Messenger/RosPublisher.h"
#include "../Messenger/RosSubscriber.h"
#include "../Messenger/RosService.h"
#include "../Messenger/RosPeriodic.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>


namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosNode
{
public:
    RosNode(std::string name);
    ~RosNode()
    {
        stop();
    }
    void start();
    void stop();
    void tick();
    void destroyMessage(std::string topic)
    {
        if (mMessages.find(topic) != mMessages.end())
        {
            mMessages[topic].reset();
            mMessages.erase(topic);
        }
    }
    template <typename MessageType, class Callback>
    void createPublisher(std::string uniquePrefix,
                         std::string topic,
                         const int queue_size,
                         void (Callback::*callbackFn)(ros::Publisher* pub),
                         Callback* callback)
    {
        if (topic.size() == 0)
        {
            CARB_LOG_ERROR("Publisher topic empty");
        }

        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Publisher callback not valid %s", topic.c_str());
            return;
        }
        // // if we already have a message on this topic, delete the previous one and recreate
        // if (mMessages.find(topic) != mMessages.end())
        // {
        //     mMessages[topic].reset();
        //     mMessages.erase(topic);
        // }
        if (rosnode_)
        {
            std::unique_ptr<RosPublisher> publisher = std::make_unique<RosPublisher>();
            publisher->init<MessageType>(rosnode_.get(), topic, queue_size, callbackFn, callback);
            // publisher->callback_ = std::move(callback);
            mMessages[uniquePrefix + topic] = std::move(publisher);
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Publisher on %s", topic.c_str());
        }
    }
    template <typename MessageType, class Callback>
    void createSubscriber(std::string uniquePrefix,
                          std::string topic,
                          const int queue_size,
                          void (Callback::*callbackFn)(const typename MessageType::ConstPtr&),
                          Callback* callback)
    {
        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Subscriber callback not valid");
        }
        if (rosnode_ && topic.size())
        {
            std::unique_ptr<RosSubscriber> subscriber = std::make_unique<RosSubscriber>();
            subscriber->init<MessageType>(rosnode_.get(), topic, queue_size, callbackFn, callback);
            // subscriber->callback_ = std::move(callback);
            mMessages[uniquePrefix + topic] = std::move(subscriber);
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Subscriber");
        }
    }

    template <typename MessageType, class Callback>
    void createPeriodic(const std::string& uniqueName, void (Callback::*callbackFn)(), Callback* callback)
    {

        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Periodic callback not valid");
        }
        if (rosnode_)
        {
            std::unique_ptr<RosPeriodic> periodic = std::make_unique<RosPeriodic>();
            periodic->init<MessageType>(rosnode_.get(), callbackFn, callback);
            // periodic->callback_ = std::move(callback);
            mMessages[uniqueName] = (std::move(periodic));
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Periodic publisher");
        }
    }


    template <typename MessageType, class Callback>
    void createService(std::string uniquePrefix,
                       std::string topic,
                       bool (Callback::*callbackFn)(typename MessageType::Request&, typename MessageType::Response&),
                       Callback* callback)
    {
        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Service callback not valid");
        }
        if (rosnode_ && topic.size())
        {
            std::unique_ptr<RosService> srv_ = std::make_unique<RosService>();
            srv_->init<MessageType>(rosnode_.get(), topic, callbackFn, callback);
            // srv_->callback_ = std::move(callback);
            mMessages[uniquePrefix + topic] = (std::move(srv_));
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Service");
        }
    }
    // bool deleteEvent(IsaacHandle event_handle);

private:
    std::unordered_map<std::string, std::unique_ptr<RosMessenger>> mMessages;
    std::unique_ptr<ros::NodeHandle> rosnode_ = nullptr;
    ros::CallbackQueue callbackQueue_;
};
}
}
}
