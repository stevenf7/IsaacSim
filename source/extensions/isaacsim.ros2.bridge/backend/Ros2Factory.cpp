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

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

std::shared_ptr<Ros2ContextHandle> Ros2FactoryImpl::createContextHandle()
{
    return std::make_shared<Ros2ContextHandleImpl>();
}

std::shared_ptr<Ros2NodeHandle> Ros2FactoryImpl::createNodeHandle(const char* name,
                                                                  const char* namespaceName,
                                                                  Ros2ContextHandle* contextHandle)
{
    return std::make_shared<Ros2NodeHandleImpl>(name, namespaceName, contextHandle);
}

std::shared_ptr<Ros2Publisher> Ros2FactoryImpl::createPublisher(Ros2NodeHandle* nodeHandle,
                                                                const char* topicName,
                                                                const void* typeSupport,
                                                                const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2PublisherImpl>(nodeHandle, topicName, typeSupport, qos);
}

std::shared_ptr<Ros2Subscriber> Ros2FactoryImpl::createSubscriber(Ros2NodeHandle* nodeHandle,
                                                                  const char* topicName,
                                                                  const void* typeSupport,
                                                                  const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2SubscriberImpl>(nodeHandle, topicName, typeSupport, qos);
}

std::shared_ptr<Ros2Service> Ros2FactoryImpl::createService(Ros2NodeHandle* nodeHandle,
                                                            const char* serviceName,
                                                            const void* typeSupport,
                                                            const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2ServiceImpl>(nodeHandle, serviceName, typeSupport, qos);
}

std::shared_ptr<Ros2Client> Ros2FactoryImpl::createClient(Ros2NodeHandle* nodeHandle,
                                                          const char* serviceName,
                                                          const void* typeSupport,
                                                          const Ros2QoSProfile& qos)
{
    return std::make_shared<Ros2ClientImpl>(nodeHandle, serviceName, typeSupport, qos);
}

std::shared_ptr<Ros2ClockMessage> Ros2FactoryImpl::createClockMessage()
{
    return std::make_shared<Ros2ClockMessageImpl>();
}

std::shared_ptr<Ros2ImuMessage> Ros2FactoryImpl::createImuMessage()
{
    return std::make_shared<Ros2ImuMessageImpl>();
}

std::shared_ptr<Ros2CameraInfoMessage> Ros2FactoryImpl::createCameraInfoMessage()
{
    return std::make_shared<Ros2CameraInfoMessageImpl>();
}

std::shared_ptr<Ros2ImageMessage> Ros2FactoryImpl::createImageMessage()
{
    return std::make_shared<Ros2ImageMessageImpl>();
}

std::shared_ptr<Ros2NitrosBridgeImageMessage> Ros2FactoryImpl::createNitrosBridgeImageMessage()
{
#if defined(_WIN32) || defined(ROS2_BACKEND_FOXY)
    return nullptr;
#else
    return std::make_shared<Ros2NitrosBridgeImageMessageImpl>();
#endif
}

std::shared_ptr<Ros2BoundingBox2DMessage> Ros2FactoryImpl::createBoundingBox2DMessage()
{
    return std::make_shared<Ros2BoundingBox2DMessageImpl>();
}

std::shared_ptr<Ros2BoundingBox3DMessage> Ros2FactoryImpl::createBoundingBox3DMessage()
{
    return std::make_shared<Ros2BoundingBox3DMessageImpl>();
}

std::shared_ptr<Ros2OdometryMessage> Ros2FactoryImpl::createOdometryMessage()
{
    return std::make_shared<Ros2OdometryMessageImpl>();
}

std::shared_ptr<Ros2RawTfTreeMessage> Ros2FactoryImpl::createRawTfTreeMessage()
{
    return std::make_shared<Ros2RawTfTreeMessageImpl>();
}

std::shared_ptr<Ros2SemanticLabelMessage> Ros2FactoryImpl::createSemanticLabelMessage()
{
    return std::make_shared<Ros2SemanticLabelMessageImpl>();
}

std::shared_ptr<Ros2JointStateMessage> Ros2FactoryImpl::createJointStateMessage()
{
    return std::make_shared<Ros2JointStateMessageImpl>();
}

std::shared_ptr<Ros2PointCloudMessage> Ros2FactoryImpl::createPointCloudMessage()
{
    return std::make_shared<Ros2PointCloudMessageImpl>();
}

std::shared_ptr<Ros2LaserScanMessage> Ros2FactoryImpl::createLaserScanMessage()
{
    return std::make_shared<Ros2LaserScanMessageImpl>();
}

std::shared_ptr<Ros2TfTreeMessage> Ros2FactoryImpl::createTfTreeMessage()
{
    return std::make_shared<Ros2TfTreeMessageImpl>();
}

std::shared_ptr<Ros2TwistMessage> Ros2FactoryImpl::createTwistMessage()
{
    return std::make_shared<Ros2TwistMessageImpl>();
}

std::shared_ptr<Ros2AckermannDriveStampedMessage> Ros2FactoryImpl::createAckermannDriveStampedMessage()
{
    return std::make_shared<Ros2AckermannDriveStampedMessageImpl>();
}

std::shared_ptr<Ros2Message> Ros2FactoryImpl::createDynamicMessage(const std::string& pkgName,
                                                                   const std::string& msgSubfolder,
                                                                   const std::string& msgName,
                                                                   BackendMessageType messageType)
{
    return std::make_shared<Ros2DynamicMessageImpl>(pkgName, msgSubfolder, msgName, messageType);
}

bool Ros2FactoryImpl::validateTopicName(const std::string& topicName)
{
    int invalidResult;
    size_t invalidIndex;

    std::ignore = rmw_validate_full_topic_name(topicName.c_str(), &invalidResult, &invalidIndex);

    if (invalidResult)
    {
        fprintf(stderr, "[Error] Topic name %s not valid, %s\n", topicName.c_str(),
                rmw_full_topic_name_validation_result_string(invalidResult));
        return false;
    }
    return true;
}

bool Ros2FactoryImpl::validateNamespaceName(const std::string& namespaceName)
{
    int invalidResult;
    size_t invalidIndex;

    std::ignore = rmw_validate_namespace(namespaceName.c_str(), &invalidResult, &invalidIndex);

    if (invalidResult)
    {
        fprintf(stderr, "[Error] Namespace name %s not valid, %s\n", namespaceName.c_str(),
                rmw_namespace_validation_result_string(invalidResult));
        return false;
    }
    return true;
}

bool Ros2FactoryImpl::validateNodeName(const std::string& nodeName)
{
    int invalidResult;
    size_t invalidIndex;

    std::ignore = rmw_validate_node_name(nodeName.c_str(), &invalidResult, &invalidIndex);

    if (invalidResult)
    {
        fprintf(stderr, "[Error] Node name %s not valid, %s\n", nodeName.c_str(),
                rmw_node_name_validation_result_string(invalidResult));
        return false;
    }
    return true;
}

} // namespace bridge
} // namespace ros2
} // namespace isaacsim

isaacsim::ros2::bridge::Ros2Factory* createFactory()
{
    return new isaacsim::ros2::bridge::Ros2FactoryImpl();
}
