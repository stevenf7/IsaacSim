// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosNode.h"

#include <carb/Framework.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
RosNode::RosNode(std::string name)
{
    CARB_LOG_ERROR("Ros Node %s Was Created", name.c_str());
    rosnode_ = std::make_unique<ros::NodeHandle>(name);
    rosnode_->setCallbackQueue(&(callbackQueue_));
}
void RosNode::start()
{

    // Call once after creating
    // if (ros::ok())
    // {
    //     callbackQueue_.callAvailable();
    // }
}
void RosNode::stop()
{
    // for (size_t i = 0; i < mMessages.size(); i++)
    // {
    //     msg.second = nullptr;
    // }
    // mMessages.clear();

    // if (rosnode_)
    // {
    //     rosnode_->shutdown();
    // }
    // rosnode_ = nullptr;
}
void RosNode::tick()
{

    if (ros::ok())
    {
        CARB_LOG_ERROR("Ros Node Tick");
        callbackQueue_.callAvailable();
        for (auto& msg : mMessages)
        {
            RosPublisher* pub = dynamic_cast<RosPublisher*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == eRosEventPublish && pub)
            {

                pub->publish();
            }
            RosPeriodic* per = dynamic_cast<RosPeriodic*>(msg.second.get());
            if (msg.second && msg.second->getEventType() == eRosEventPeriodic && per)
            {
                per->tick();
            }
        }
    }
    else
    {
        CARB_LOG_ERROR("!ros::ok() An error has occurred within ROS.");
    }
}

// bool RosNode::deleteEvent(IsaacHandle event_handle)
// {
//     if (event_handle >= 0 && size_t(event_handle) < mMessages.size())
//     {
//         mMessages[event_handle].reset();
//         return true;
//     }
//     return false;
// }

}
}
}
