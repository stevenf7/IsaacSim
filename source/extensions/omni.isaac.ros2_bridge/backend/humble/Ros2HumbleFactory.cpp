// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Humble.h"
#include "rmw/validate_full_topic_name.h"
#include "rmw/validate_namespace.h"
#include "rmw/validate_node_name.h"

#include <carb/logging/Log.h>

std::shared_ptr<Ros2HandleBase> Ros2FactoryHumble::CreateHandle()
{
    return std::make_shared<Ros2HandleHumble>();
}

std::shared_ptr<Ros2NodeBase> Ros2FactoryHumble::CreateNode(const char* name, const char* name_space, Ros2HandleBase* handle)
{
    return std::make_shared<Ros2NodeHumble>(name, name_space, handle);
}

std::shared_ptr<Ros2Publisher> Ros2FactoryHumble::CreatePublisher(Ros2NodeBase* node,
                                                                  const char* topic_name,
                                                                  const void* type,
                                                                  const size_t history_depth)
{
    return std::make_shared<Ros2PublisherHumble>(node, topic_name, type, history_depth);
}

std::shared_ptr<Ros2Subscriber> Ros2FactoryHumble::CreateSubscriber(Ros2NodeBase* node,
                                                                    const char* topic_name,
                                                                    const void* type,
                                                                    const size_t history_depth)
{
    return std::make_shared<Ros2SubscriberHumble>(node, topic_name, type, history_depth);
}

std::shared_ptr<Ros2Service> Ros2FactoryHumble::CreateService(Ros2NodeBase* node, const char* service_name, const void* type)
{
    return std::make_shared<Ros2ServiceHumble>(node, service_name, type);
}

std::shared_ptr<Ros2ClockMessage> Ros2FactoryHumble::CreateClockMessage()
{
    return std::make_shared<Ros2ClockMessageHumble>();
}

std::shared_ptr<Ros2ImuMessage> Ros2FactoryHumble::CreateImuMessage()
{
    return std::make_shared<Ros2ImuMessageHumble>();
}

std::shared_ptr<Ros2CameraInfoMessage> Ros2FactoryHumble::CreateCameraInfoMessage()
{
    return std::make_shared<Ros2CameraInfoMessageHumble>();
}

std::shared_ptr<Ros2ImageMessage> Ros2FactoryHumble::CreateImageMessage()
{
    return std::make_shared<Ros2ImageMessageHumble>();
}

std::shared_ptr<Ros2BoundingBox2DMessage> Ros2FactoryHumble::CreateBoundingBox2DMessage()
{
    return std::make_shared<Ros2BoundingBox2DMessageHumble>();
}

std::shared_ptr<Ros2BoundingBox3DMessage> Ros2FactoryHumble::CreateBoundingBox3DMessage()
{
    return std::make_shared<Ros2BoundingBox3DMessageHumble>();
}

std::shared_ptr<Ros2OdomMessage> Ros2FactoryHumble::CreateOdomMessage()
{
    return std::make_shared<Ros2OdomMessageHumble>();
}

std::shared_ptr<Ros2RawTfTreeMessage> Ros2FactoryHumble::CreateRawTfTreeMessage()
{
    return std::make_shared<Ros2RawTfTreeMessageHumble>();
}

std::shared_ptr<Ros2SemanticLabelMessage> Ros2FactoryHumble::CreateSemanticLabelMessage()
{
    return std::make_shared<Ros2SemanticLabelMessageHumble>();
}

std::shared_ptr<Ros2JointStateMessage> Ros2FactoryHumble::CreateJointStateMessage()
{
    return std::make_shared<Ros2JointStateMessageHumble>();
}

std::shared_ptr<Ros2PointCloudMessage> Ros2FactoryHumble::CreatePointCloudMessage()
{
    return std::make_shared<Ros2PointCloudMessageHumble>();
}

std::shared_ptr<Ros2LaserScanMessage> Ros2FactoryHumble::CreateLaserScanMessage()
{
    return std::make_shared<Ros2LaserScanMessageHumble>();
}

std::shared_ptr<Ros2TfTreeMessage> Ros2FactoryHumble::CreateTfTreeMessage()
{
    return std::make_shared<Ros2TfTreeMessageHumble>();
}

std::shared_ptr<Ros2TwistMessage> Ros2FactoryHumble::CreateTwistMessage()
{
    return std::make_shared<Ros2TwistMessageHumble>();
}

std::shared_ptr<Ros2AckermannDriveStampedMessage> Ros2FactoryHumble::CreateAckermannDriveStampedMessage()
{
    return std::make_shared<Ros2AckermannDriveStampedMessageHumble>();
}


bool Ros2FactoryHumble::validateTopic(const std::string& topicName)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_full_topic_name(topicName.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        fprintf(stderr, "[Error] Topic name %s not valid, %s\n", topicName.c_str(),
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
bool Ros2FactoryHumble::validateNodeNamespace(const std::string& nodeNamespace)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_namespace(nodeNamespace.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        fprintf(stderr, "[Error] Namespace name %s not valid, %s\n", nodeNamespace.c_str(),
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
bool Ros2FactoryHumble::validateNodeName(const std::string& nodeName)
{
    int invalid_result;
    size_t invalid_index;

    std::ignore = rmw_validate_node_name(nodeName.c_str(), &invalid_result, &invalid_index);

    if (invalid_result)
    {
        fprintf(stderr, "[Error] Node name %s not valid, %s\n", nodeName.c_str(),
                rmw_node_name_validation_result_string(invalid_result));
        return false;
    }
    return true;
}

std::shared_ptr<Ros2Message> Ros2FactoryHumble::createDynamicMessage(const std::string& pkgName,
                                                                     const std::string& msgSubfolder,
                                                                     const std::string& msgName,
                                                                     BackendMessageType messageType)
{
    return std::make_shared<Ros2DynamicMessageHumble>(pkgName, msgSubfolder, msgName, messageType);
}

Ros2Factory* createFactory()
{
    return new Ros2FactoryHumble();
}
