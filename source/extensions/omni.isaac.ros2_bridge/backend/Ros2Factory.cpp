// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "Ros2Impl.h"
#include "rmw/validate_full_topic_name.h"
#include "rmw/validate_namespace.h"
#include "rmw/validate_node_name.h"

#include <carb/logging/Log.h>

std::shared_ptr<Ros2HandleBase> Ros2FactoryImpl::CreateHandle()
{
    return std::make_shared<Ros2HandleImpl>();
}

std::shared_ptr<Ros2NodeBase> Ros2FactoryImpl::CreateNode(const char* name, const char* name_space, Ros2HandleBase* handle)
{
    return std::make_shared<Ros2NodeImpl>(name, name_space, handle);
}

std::shared_ptr<Ros2Publisher> Ros2FactoryImpl::CreatePublisher(Ros2NodeBase* node,
                                                                const char* topic_name,
                                                                const void* type,
                                                                const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2PublisherImpl>(node, topic_name, type, qos);
}

std::shared_ptr<Ros2Subscriber> Ros2FactoryImpl::CreateSubscriber(Ros2NodeBase* node,
                                                                  const char* topic_name,
                                                                  const void* type,
                                                                  const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2SubscriberImpl>(node, topic_name, type, qos);
}

std::shared_ptr<Ros2Service> Ros2FactoryImpl::CreateService(Ros2NodeBase* node,
                                                            const char* service_name,
                                                            const void* type,
                                                            const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2ServiceImpl>(node, service_name, type, qos);
}

std::shared_ptr<Ros2Client> Ros2FactoryImpl::CreateClient(Ros2NodeBase* node,
                                                          const char* service_name,
                                                          const void* type,
                                                          const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2ClientImpl>(node, service_name, type, qos);
}

std::shared_ptr<Ros2ClockMessage> Ros2FactoryImpl::CreateClockMessage()
{
    return std::make_shared<Ros2ClockMessageImpl>();
}

std::shared_ptr<Ros2ImuMessage> Ros2FactoryImpl::CreateImuMessage()
{
    return std::make_shared<Ros2ImuMessageImpl>();
}

std::shared_ptr<Ros2CameraInfoMessage> Ros2FactoryImpl::CreateCameraInfoMessage()
{
    return std::make_shared<Ros2CameraInfoMessageImpl>();
}

std::shared_ptr<Ros2ImageMessage> Ros2FactoryImpl::CreateImageMessage()
{
    return std::make_shared<Ros2ImageMessageImpl>();
}

std::shared_ptr<Ros2NitrosBridgeImageMessage> Ros2FactoryImpl::CreateNitrosBridgeImageMessage()
{
#if defined(_WIN32) || defined(ROS2_BACKEND_FOXY)
    return nullptr;
#else
    return std::make_shared<Ros2NitrosBridgeImageMessageImpl>();
#endif
}

std::shared_ptr<Ros2BoundingBox2DMessage> Ros2FactoryImpl::CreateBoundingBox2DMessage()
{
    return std::make_shared<Ros2BoundingBox2DMessageImpl>();
}

std::shared_ptr<Ros2BoundingBox3DMessage> Ros2FactoryImpl::CreateBoundingBox3DMessage()
{
    return std::make_shared<Ros2BoundingBox3DMessageImpl>();
}

std::shared_ptr<Ros2OdomMessage> Ros2FactoryImpl::CreateOdomMessage()
{
    return std::make_shared<Ros2OdomMessageImpl>();
}

std::shared_ptr<Ros2RawTfTreeMessage> Ros2FactoryImpl::CreateRawTfTreeMessage()
{
    return std::make_shared<Ros2RawTfTreeMessageImpl>();
}

std::shared_ptr<Ros2SemanticLabelMessage> Ros2FactoryImpl::CreateSemanticLabelMessage()
{
    return std::make_shared<Ros2SemanticLabelMessageImpl>();
}

std::shared_ptr<Ros2JointStateMessage> Ros2FactoryImpl::CreateJointStateMessage()
{
    return std::make_shared<Ros2JointStateMessageImpl>();
}

std::shared_ptr<Ros2PointCloudMessage> Ros2FactoryImpl::CreatePointCloudMessage()
{
    return std::make_shared<Ros2PointCloudMessageImpl>();
}

std::shared_ptr<Ros2LaserScanMessage> Ros2FactoryImpl::CreateLaserScanMessage()
{
    return std::make_shared<Ros2LaserScanMessageImpl>();
}

std::shared_ptr<Ros2TfTreeMessage> Ros2FactoryImpl::CreateTfTreeMessage()
{
    return std::make_shared<Ros2TfTreeMessageImpl>();
}

std::shared_ptr<Ros2TwistMessage> Ros2FactoryImpl::CreateTwistMessage()
{
    return std::make_shared<Ros2TwistMessageImpl>();
}

std::shared_ptr<Ros2AckermannDriveStampedMessage> Ros2FactoryImpl::CreateAckermannDriveStampedMessage()
{
    return std::make_shared<Ros2AckermannDriveStampedMessageImpl>();
}


bool Ros2FactoryImpl::validateTopic(const std::string& topicName)
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
bool Ros2FactoryImpl::validateNodeNamespace(const std::string& nodeNamespace)
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
bool Ros2FactoryImpl::validateNodeName(const std::string& nodeName)
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

std::shared_ptr<Ros2Message> Ros2FactoryImpl::createDynamicMessage(const std::string& pkgName,
                                                                   const std::string& msgSubfolder,
                                                                   const std::string& msgName,
                                                                   BackendMessageType messageType)
{
    return std::make_shared<Ros2DynamicMessageImpl>(pkgName, msgSubfolder, msgName, messageType);
}

Ros2Factory* createFactory()
{
    return new Ros2FactoryImpl();
}
