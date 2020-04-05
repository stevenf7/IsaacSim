// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosNode.h"

#include "RosGlobals.h"

#include <carb/Framework.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
RosNode::RosNode(RosGlobals* globals)
{
    globals_ = globals;
}
void RosNode::start()
{
    CARB_LOG_INFO("A Ros Node Started");
    rosnode_ = std::make_unique<ros::NodeHandle>();
    rosnode_->setCallbackQueue(&(callbackQueue_));
    // Call once after creating
    if (ros::ok())
    {
        callbackQueue_.callAvailable();
    }
}
void RosNode::stop()
{
    for (size_t i = 0; i < msgs_.size(); i++)
    {
        msgs_[i] = nullptr;
    }
    msgs_.clear();

    if (rosnode_)
    {
        rosnode_->shutdown();
    }
    rosnode_ = nullptr;
}
void RosNode::tick(const float dt)
{

    if (ros::ok())
    {
        // CARB_LOG_ERROR("Ros Node Tick");
        callbackQueue_.callAvailable();
        for (size_t i = 0; i < msgs_.size(); i++)
        {
            RosPublisher* pub = dynamic_cast<RosPublisher*>(msgs_[i].get());
            if (msgs_[i] && msgs_[i]->getEventType() == eRosEventPublish && pub)
            {

                pub->publish();
            }
            // else
            // {
            //     CARB_LOG_ERROR("Publisher not valid %s", msgs_[i]->getTopic().c_str());
            // }
            RosPeriodic* per = dynamic_cast<RosPeriodic*>(msgs_[i].get());
            if (msgs_[i] && msgs_[i]->getEventType() == eRosEventPeriodic && per)
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

bool RosNode::deleteEvent(IsaacHandle event_handle)
{
    if (event_handle >= 0 && size_t(event_handle) < msgs_.size())
    {
        msgs_[event_handle].reset();
        return true;
    }
    return false;
}

RosGlobals* RosNode::getGlobals()
{
    return globals_;
}
double RosNode::getClock()
{
    return globals_->clock;
}

void RosNode::fillDictionaryItem(int node_number, carb::dictionary::Item* sBase)
{
    carb::dictionary::IDictionary* idict = globals_->idict;

    for (size_t i = 0; i < msgs_.size(); i++)
    {
        if (!msgs_[i])
        {
            continue;
        }
        std::string node_prefix = "nodes/" + std::to_string(node_number) + "/" + std::to_string(i);

        std::string topic_path = node_prefix + "/topic";


        idict->makeStringAtPath(sBase, topic_path.c_str(), msgs_[i]->getTopic().c_str());
        if (!msgs_[i]->callback_)
        {
            CARB_LOG_ERROR("Callback Not valid");

            continue;
        }
        std::vector<std::string> prim_paths = msgs_[i]->callback_->getPaths();

        for (size_t p = 0; p < prim_paths.size(); p++)
        {
            std::string path = node_prefix + "/paths/" + std::to_string(p);
            idict->makeStringAtPath(sBase, path.c_str(), prim_paths[p].c_str());
        }

        std::string event_name = node_prefix + "/event";
        std::string message_name = node_prefix + "/message";
        std::string message_str = "";

        switch (msgs_[i]->callback_->getMessageType())
        {
        case eRosMessageNone:
            message_str = "NONE";
            break;
        case eRosMessageEmpty:
            message_str = "EMPTY";
            break;
        case eRosMessageJointState:
            message_str = "JOINT_STATE";
            break;
        case eRosMessagePose:
            message_str = "POSE";
            break;
        case eRosMessageTf:
            message_str = "TF";
            break;
        case eRosMessageImage:
            message_str = "IMAGE";
            break;
        case eRosMessageCameraInfo:
            message_str = "CAMERA_INFO";
            break;
        case eRosMessageBoundingBox:
            message_str = "BOUNDING_BOX";
            break;
        case eRosMessageRangeScan:
            message_str = "RANGE_SCAN";
            break;
        }

        idict->makeStringAtPath(sBase, message_name.c_str(), message_str.c_str());

        std::string event_str = "";
        switch (msgs_[i]->getEventType())
        {
        case eRosEventNone:
            event_str = "NONE";
            break;
        case eRosEventPublish:
            event_str = "PUBLISH";
            break;
        case eRosEventSubscribe:
            event_str = "SUBSCRIBE";
            break;
        case eRosEventService:
            event_str = "SERVICE";
            break;
        case eRosEventPeriodic:
            event_str = "PERIODIC";
            break;
        }

        idict->makeStringAtPath(sBase, event_name.c_str(), event_str.c_str());

        std::string queue_name = node_prefix + "/queue_size";
        idict->makeIntAtPath(sBase, queue_name.c_str(), msgs_[i]->getQueueSize());
    }
}

}
}
}
