// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosManager.h"

#include "RosGlobals.h"
#include "tf2_msgs/TFMessage.h"

#include <carb/settings/ISettings.h>

#include <ros/console.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


RosManager::RosManager(RosGlobals* globals)
{
    ros::M_string args;
    if (!ros::isInitialized())
    {
        ros::init(args, "KitRosBridge");
        ros::Time::init();
    }
    else
    {
        CARB_LOG_WARN("Ros already initialized");
    }

    while (!ros::master::check())
    {
        CARB_LOG_ERROR("Waiting for ROS master node... please run roscore");
        ros::Duration(0.5).sleep();
    }
    if (ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Error))
    {
        ros::console::notifyLoggerLevelsChanged();
    }
    globals_ = globals;
    SimState = std::make_unique<RosState>(globals_);
}

RosManager::~RosManager()
{
    SimState = nullptr;
    for (auto& node : ros_nodes_)
    {
        if (node)
        {
            node = nullptr;
        }
    }
}


void RosManager::start()
{
    SimState->start();
    tf_listener_ = std::make_unique<tf2_ros::TransformListener>(tf_buffer_);
}

void RosManager::stop()
{
    SimState->stop();
    tf_listener_ = nullptr;
}

void RosManager::tick(const float dt)
{
    SimState->tick(dt);
    for (auto& node : ros_nodes_)
    {
        if (node)
        {
            node->tick(dt);
        }
    }
}

IsaacHandle RosManager::addNode()
{
    std::unique_ptr<RosNode> node = std::make_unique<RosNode>(globals_);
    node->start();
    ros_nodes_.push_back(std::move(node));
    CARB_LOG_INFO("Node %d Created", ros_nodes_.size() - 1);

    return ros_nodes_.size() - 1;
}

bool RosManager::deleteNode(const IsaacHandle node_handle)
{

    if (node_handle >= 0 && size_t(node_handle) < ros_nodes_.size())
    {
        ros_nodes_[node_handle].reset();
    }
    return true;
}

IsaacHandle RosManager::addEvent(const IsaacHandle node_handle,
                                 const std::vector<std::string>& paths,
                                 std::string topic,
                                 const int queue_size,
                                 RosMessageType message_type,
                                 RosEventType event_type)
{
    IsaacHandle event_handle = -1;
    if (size_t(node_handle) >= ros_nodes_.size() || node_handle < 0)
    {
        CARB_LOG_ERROR("Invalid Node Handle");
        return -1;
    }
    if (event_type == RosEventType::eRosEventPublish)
    {
        switch (message_type)
        {
        case eRosMessageJointState:
        {
            std::unique_ptr<RosCallbackJointState> joint_state_callback =
                std::make_unique<RosCallbackJointState>(ros_nodes_[node_handle].get(), paths);


            event_handle = ros_nodes_[node_handle]->createPublisher<sensor_msgs::JointState>(
                topic, queue_size, &RosCallbackJointState::pubCallback, std::move(joint_state_callback));

            CARB_LOG_INFO("eRosMessageJointState publisher added");
            break;
        }
        case eRosMessageTf:
        {
            std::unique_ptr<RosCallbackTF> tf_callback =
                std::make_unique<RosCallbackTF>(ros_nodes_[node_handle].get(), paths, &tf_buffer_);


            event_handle = ros_nodes_[node_handle]->createPublisher<tf2_msgs::TFMessage>(
                topic, queue_size, &RosCallbackTF::pubCallback, std::move(tf_callback));

            CARB_LOG_INFO("eRosMessageTf publisher added");
            break;
        }
        case eRosMessagePose:
        {
            std::unique_ptr<RosCallbackPose> pose_callback =
                std::make_unique<RosCallbackPose>(ros_nodes_[node_handle].get(), paths);


            event_handle = ros_nodes_[node_handle]->createPublisher<geometry_msgs::PoseStamped>(
                topic, queue_size, &RosCallbackPose::pubCallback, std::move(pose_callback));

            CARB_LOG_INFO("eRosMessagePose publisher added");
            break;
        }
        default:
        {
            CARB_LOG_ERROR("Event Message Type %d Not Supported Yet!", int(message_type));
            break;
        }
        }
    }
    else if (event_type == RosEventType::eRosEventSubscribe)
    {
        switch (message_type)
        {
        case eRosMessageJointState:
        {
            std::unique_ptr<RosCallbackJointState> joint_state_callback =
                std::make_unique<RosCallbackJointState>(ros_nodes_[node_handle].get(), paths);


            event_handle = ros_nodes_[node_handle]->createSubscriber<sensor_msgs::JointState>(
                topic, queue_size, &RosCallbackJointState::subCallback, std::move(joint_state_callback));

            CARB_LOG_INFO("eRosMessageJointState subscriber added");
            break;
        }
        case eRosMessagePose:
        {
            std::unique_ptr<RosCallbackPose> pose_callback =
                std::make_unique<RosCallbackPose>(ros_nodes_[node_handle].get(), paths);


            event_handle = ros_nodes_[node_handle]->createSubscriber<geometry_msgs::PoseStamped>(
                topic, queue_size, &RosCallbackPose::subCallback, std::move(pose_callback));

            CARB_LOG_INFO("eRosMessagePose subscriber added");
            break;
        }

        default:
        {
            CARB_LOG_ERROR("Event Message Type %d Not Supported Yet!", int(message_type));
            break;
        }
        }
    }
    else if (event_type == RosEventType::eRosEventService)
    {
        switch (message_type)
        {
        case eRosMessagePose:
        {
            std::unique_ptr<RosCallbackPose> pose_callback =
                std::make_unique<RosCallbackPose>(ros_nodes_[node_handle].get(), paths);


            event_handle = ros_nodes_[node_handle]->createService<isaac_bridge::IsaacPose>(
                topic, &RosCallbackPose::srvCallback, std::move(pose_callback));

            CARB_LOG_INFO("eRosMessagePose service added");
            break;
        }
        default:
        {
            CARB_LOG_ERROR("Event Message Type %d Not Supported Yet!", int(message_type));
            break;
        }
        }
    }
    else if (event_type == RosEventType::eRosEventPeriodic)
    {
        switch (message_type)
        {
        case eRosMessageTf:
        {
            std::unique_ptr<RosCallbackTF> tf_callback =
                std::make_unique<RosCallbackTF>(ros_nodes_[node_handle].get(), paths, &tf_buffer_);

            event_handle = ros_nodes_[node_handle]->createPeriodic<tf2_msgs::TFMessage>(
                &RosCallbackTF::tickCallback, std::move(tf_callback));

            CARB_LOG_INFO("eRosMessageTF periodic added");
            break;
        }
        default:
        {
            CARB_LOG_ERROR("Event Message Type %d Not Supported Yet!", int(message_type));
            break;
        }
        }
    }


    return event_handle;
}

bool RosManager::deleteEvent(const IsaacHandle node_handle, const IsaacHandle event_handle)
{
    if (node_handle >= 0 && size_t(node_handle) < ros_nodes_.size())
    {
        ros_nodes_[node_handle]->deleteEvent(event_handle);
    }
    return true;
}


void RosManager::setClockState(const bool state)
{
    SimState->set_enable_clock(state);
}

std::string RosManager::getJsonString()
{
    CARB_LOG_INFO("RosManager::getJsonString()");

    carb::dictionary::IDictionary* idict = globals_->idict;

    carb::dictionary::Item* sBase = idict->createItem(nullptr, "<root>", carb::dictionary::ItemType::eDictionary);

    for (size_t i = 0; i < ros_nodes_.size(); i++)
    {
        if (ros_nodes_[i])
        {
            ros_nodes_[i]->fillDictionaryItem(i, sBase);
        }
    }
    idict->makeBoolAtPath(sBase, "clock", SimState->get_enable_clock());
    carb::dictionary::ISerializer* json_serializer = globals_->json_serializer;

    const char* jsonString =
        json_serializer->createStringBufferFromDictionary(sBase, carb::dictionary::kSerializerOptionMakePretty);

    std::string result(jsonString);
    json_serializer->destroyStringBuffer(jsonString);
    idict->destroyItem(sBase);

    return result;
}


void RosManager::parseJsonString(std::string json_config)
{
    CARB_LOG_INFO("RosManager::parseJsonString()");
    CARB_LOG_INFO("RosManager::parseJsonString() Resetting All Nodes");
    // TODO: Delete existing Nodes

    carb::dictionary::ISerializer* json_serializer = globals_->json_serializer;
    carb::dictionary::IDictionary* idict = globals_->idict;
    carb::dictionary::Item* sBase = json_serializer->createDictionaryFromStringBuffer(json_config.c_str());

    const carb::dictionary::Item* clock_setting = idict->getItem(sBase, "clock");
    if (clock_setting)
    {
        bool state = idict->getAsBool(clock_setting);
        SimState->set_enable_clock(state);
    }

    const carb::dictionary::Item* node_list = idict->getItem(sBase, "nodes");
    for (size_t i = 0, totalNodes = idict->getItemChildCount(node_list); i < totalNodes; ++i)
    {
        const carb::dictionary::Item* event_list = idict->getItemChildByIndex(node_list, i);

        IsaacHandle node_handle = addNode();

        for (size_t j = 0, totalEvents = idict->getItemChildCount(event_list); j < totalEvents; ++j)
        {
            const carb::dictionary::Item* event_info = idict->getItemChildByIndex(event_list, j);

            // const char* jsonString = json_serializer->createStringBufferFromDictionary(
            //     eventItemDict, carb::dictionary::kSerializerOptionMakePretty);

            // printf("%s\n", jsonString);
            // json_serializer->destroyStringBuffer(jsonString);

            const carb::dictionary::Item* event_paths = idict->getItem(event_info, "paths");
            size_t arrayLength = idict->getArrayLength(event_paths);
            std::vector<std::string> paths;

            for (size_t k = 0; k < arrayLength; ++k)
            {
                paths.push_back(idict->getStringBufferAt(event_paths, k));
            }

            const carb::dictionary::Item* topicDict = idict->getItem(event_info, "topic");
            std::string topic = idict->getStringBuffer(topicDict);

            const carb::dictionary::Item* messageDict = idict->getItem(event_info, "message");
            std::string message = idict->getStringBuffer(messageDict);

            const carb::dictionary::Item* eventItemDict = idict->getItem(event_info, "event");
            std::string event = idict->getStringBuffer(eventItemDict);

            RosMessageType mtype = eRosMessageNone;
            if (message == "NONE")
            {
                mtype = eRosMessageNone;
            }
            else if (message == "EMPTY")
            {
                mtype = eRosMessageEmpty;
            }
            else if (message == "POSE")
            {
                mtype = eRosMessagePose;
            }
            else if (message == "JOINT_STATE")
            {
                mtype = eRosMessageJointState;
            }
            else if (message == "TF")
            {
                mtype = eRosMessageTf;
            }
            else if (message == "IMAGE")
            {
                mtype = eRosMessageImage;
            }
            else if (message == "CAMERA_INFO")
            {
                mtype = eRosMessageCameraInfo;
            }
            else if (message == "BOUNDING_BOX")
            {
                mtype = eRosMessageBoundingBox;
            }
            else if (message == "RANGE_SCAN")
            {
                mtype = eRosMessageRangeScan;
            }

            RosEventType mevent = eRosEventNone;
            if (event == "NONE")
            {
                mevent = eRosEventNone;
            }
            else if (event == "PUBLISH")
            {
                mevent = eRosEventPublish;
            }
            else if (event == "SUBSCRIBE")
            {
                mevent = eRosEventSubscribe;
            }
            else if (event == "SERVICE")
            {
                mevent = eRosEventService;
            }
            else if (event == "PERIODIC")
            {
                mevent = eRosEventPeriodic;
            }
            int queue_size = 100;
            addEvent(node_handle, paths, topic, queue_size, mtype, mevent);
        }
    }

    idict->destroyItem(sBase);
}
}
}
}
