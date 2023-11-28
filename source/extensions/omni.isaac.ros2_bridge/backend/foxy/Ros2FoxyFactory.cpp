// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Foxy.h"
#include "rmw/validate_full_topic_name.h"
#include "rmw/validate_namespace.h"
#include "rmw/validate_node_name.h"

#include <carb/logging/Log.h>

std::shared_ptr<Ros2HandleBase> Ros2FactoryFoxy::CreateHandle()
{
    return std::make_shared<Ros2HandleFoxy>();
}

std::shared_ptr<Ros2NodeBase> Ros2FactoryFoxy::CreateNode(const char* name, const char* name_space, Ros2HandleBase* handle)
{
    return std::make_shared<Ros2NodeFoxy>(name, name_space, handle);
}

std::shared_ptr<Ros2Publisher> Ros2FactoryFoxy::CreatePublisher(Ros2NodeBase* node,
                                                                const char* topic_name,
                                                                const void* type,
                                                                const size_t history_depth)
{
    return std::make_shared<Ros2PublisherFoxy>(node, topic_name, type, history_depth);
}
std::shared_ptr<Ros2Subscriber> Ros2FactoryFoxy::CreateSubscriber(Ros2NodeBase* node,
                                                                  const char* topic_name,
                                                                  const void* type,
                                                                  const size_t history_depth)
{
    return std::make_shared<Ros2SubscriberFoxy>(node, topic_name, type, history_depth);
}
std::shared_ptr<Ros2ClockMessage> Ros2FactoryFoxy::CreateClockMessage()
{
    return std::make_shared<Ros2ClockMessageFoxy>();
}

std::shared_ptr<Ros2ImuMessage> Ros2FactoryFoxy::CreateImuMessage()
{
    return std::make_shared<Ros2ImuMessageFoxy>();
}

std::shared_ptr<Ros2CameraInfoMessage> Ros2FactoryFoxy::CreateCameraInfoMessage()
{
    return std::make_shared<Ros2CameraInfoMessageFoxy>();
}

std::shared_ptr<Ros2ImageMessage> Ros2FactoryFoxy::CreateImageMessage()
{
    return std::make_shared<Ros2ImageMessageFoxy>();
}

std::shared_ptr<Ros2BoundingBox2DMessage> Ros2FactoryFoxy::CreateBoundingBox2DMessage()
{
    return std::make_shared<Ros2BoundingBox2DMessageFoxy>();
}

std::shared_ptr<Ros2BoundingBox3DMessage> Ros2FactoryFoxy::CreateBoundingBox3DMessage()
{
    return std::make_shared<Ros2BoundingBox3DMessageFoxy>();
}

std::shared_ptr<Ros2OdomMessage> Ros2FactoryFoxy::CreateOdomMessage()
{
    return std::make_shared<Ros2OdomMessageFoxy>();
}

std::shared_ptr<Ros2RawTfTreeMessage> Ros2FactoryFoxy::CreateRawTfTreeMessage()
{
    return std::make_shared<Ros2RawTfTreeMessageFoxy>();
}

std::shared_ptr<Ros2SemanticLabelMessage> Ros2FactoryFoxy::CreateSemanticLabelMessage()
{
    return std::make_shared<Ros2SemanticLabelMessageFoxy>();
}

std::shared_ptr<Ros2JointStateMessage> Ros2FactoryFoxy::CreateJointStateMessage()
{
    return std::make_shared<Ros2JointStateMessageFoxy>();
}

std::shared_ptr<Ros2PointCloudMessage> Ros2FactoryFoxy::CreatePointCloudMessage()
{
    return std::make_shared<Ros2PointCloudMessageFoxy>();
}

std::shared_ptr<Ros2LaserScanMessage> Ros2FactoryFoxy::CreateLaserScanMessage()
{
    return std::make_shared<Ros2LaserScanMessageFoxy>();
}

std::shared_ptr<Ros2TfTreeMessage> Ros2FactoryFoxy::CreateTfTreeMessage()
{
    return std::make_shared<Ros2TfTreeMessageFoxy>();
}

std::shared_ptr<Ros2TwistMessage> Ros2FactoryFoxy::CreateTwistMessage()
{
    return std::make_shared<Ros2TwistMessageFoxy>();
}


bool Ros2FactoryFoxy::validateTopic(const std::string& topicName)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_full_topic_name(topicName.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        CARB_LOG_ERROR("Topic name %s not valid, %s", topicName.c_str(),
                       rmw_full_topic_name_validation_result_string(invalid_result));
        return false;
    }
    return true;
}
/**
 * @brief Validates a ROS namespace, returns true if valid, false if not
 *
 * @param topicName
 * @return true
 * @return false
 */
bool Ros2FactoryFoxy::validateNodeNamespace(const std::string& nodeNamespace)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_namespace(nodeNamespace.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        CARB_LOG_ERROR("Namespace name %s not valid, %s", nodeNamespace.c_str(),
                       rmw_namespace_validation_result_string(invalid_result));
        return false;
    }
    return true;
}

/**
 * @brief Validates a ROS node name, returns true if valid, false if not
 *
 * @param topicName
 * @return true
 * @return false
 */
bool Ros2FactoryFoxy::validateNodeName(const std::string& nodeName)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_node_name(nodeName.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        CARB_LOG_ERROR(
            "Node name %s not valid, %s", nodeName.c_str(), rmw_node_name_validation_result_string(invalid_result));
        return false;
    }
    return true;
}

Ros2Factory* createFactory()
{
    return new Ros2FactoryFoxy();
}
