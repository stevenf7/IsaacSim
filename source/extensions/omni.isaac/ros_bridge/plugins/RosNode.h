#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <functional>

#include "ros/callback_queue.h"
#include "ros/ros.h"
#include "RosCallback.h"
#include "messenger/RosPublisher.h"
#include "messenger/RosSubscriber.h"
#include "messenger/RosService.h"
#include "messenger/RosPeriodic.h"
#include "RosGlobals.h"

#include <carb/logging/Log.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <carb/settings/ISettings.h>


namespace omni
{
namespace isaac
{
namespace ros_bridge
{

struct RosGlobals;


class RosNode
{
public:
    RosNode(RosGlobals* globals);
    ~RosNode()
    {
        stop();
    }
    void start();
    void stop();
    void tick(const float dt = 0.0f);

    template <typename MessageType, class Callback>
    IsaacHandle createPublisher(std::string topic,
                                const int queue_size,
                                void (Callback::*callbackFn)(ros::Publisher* pub),
                                std::unique_ptr<Callback> callback)
    {
        if (topic.size() == 0)
        {
            CARB_LOG_ERROR("Publisher topic empty");
        }

        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Publisher callback not valid %s", topic.c_str());
            return -1;
        }

        if (rosnode_)
        {
            std::unique_ptr<RosPublisher> pub_ = std::make_unique<RosPublisher>();
            pub_->init<MessageType>(rosnode_.get(), topic, queue_size, callbackFn, callback.get());
            pub_->callback_ = std::move(callback);
            msgs_.push_back(std::move(pub_));
            return msgs_.size() - 1;
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Publisher on %s", topic.c_str());
        }
        return -1;
    }
    template <typename MessageType, class Callback>
    IsaacHandle createSubscriber(std::string topic,
                                 const int queue_size,
                                 void (Callback::*callbackFn)(const typename MessageType::ConstPtr&),
                                 std::unique_ptr<Callback> callback)
    {
        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Subscriber callback not valid");
            return -1;
        }
        if (rosnode_ && topic.size())
        {
            std::unique_ptr<RosSubscriber> sub_ = std::make_unique<RosSubscriber>();
            sub_->init<MessageType>(rosnode_.get(), topic, queue_size, callbackFn, callback.get());
            sub_->callback_ = std::move(callback);
            msgs_.push_back(std::move(sub_));
            return msgs_.size() - 1;
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Subscriber");
        }
        return -1;
    }

    template <typename MessageType, class Callback>
    IsaacHandle createPeriodic(void (Callback::*callbackFn)(), std::unique_ptr<Callback> callback)
    {

        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Periodic callback not valid");
            return -1;
        }
        if (rosnode_)
        {
            std::unique_ptr<RosPeriodic> per_ = std::make_unique<RosPeriodic>();
            per_->init<MessageType>(rosnode_.get(), callbackFn, callback.get());
            per_->callback_ = std::move(callback);
            msgs_.push_back(std::move(per_));
            return msgs_.size() - 1;
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Subscriber");
        }
        return -1;
    }


    template <typename MessageType, class Callback>
    IsaacHandle createService(std::string topic,
                              bool (Callback::*callbackFn)(typename MessageType::Request&,
                                                           typename MessageType::Response&),
                              std::unique_ptr<Callback> callback)
    {
        if (!callback && callbackFn)
        {
            CARB_LOG_ERROR("Service callback not valid");
            return -1;
        }
        if (rosnode_ && topic.size())
        {
            std::unique_ptr<RosService> srv_ = std::make_unique<RosService>();
            srv_->init<MessageType>(rosnode_.get(), topic, callbackFn, callback.get());
            srv_->callback_ = std::move(callback);
            msgs_.push_back(std::move(srv_));
            return msgs_.size() - 1;
        }
        else
        {
            CARB_LOG_ERROR("Could Not Create Service");
        }
        return -1;
    }
    bool deleteEvent(IsaacHandle event_handle);
    RosGlobals* getGlobals();
    double getClock();
    void fillDictionaryItem(int node_number, carb::dictionary::Item* sBase);

private:
    std::vector<std::unique_ptr<RosMessenger>> msgs_;

    std::unique_ptr<ros::NodeHandle> rosnode_ = nullptr;
    ros::CallbackQueue callbackQueue_;
    RosGlobals* globals_;
};
}
}
}
