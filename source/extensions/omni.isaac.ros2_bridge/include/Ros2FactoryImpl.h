// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <include/Ros2Factory.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{

class Ros2FactoryImpl : public Ros2Factory
{
public:
    virtual std::shared_ptr<Ros2ContextHandle> createContextHandle();
    virtual std::shared_ptr<Ros2NodeHandle> createNodeHandle(const char* name,
                                                             const char* namespaceName,
                                                             Ros2ContextHandle* contextHandle);
    virtual std::shared_ptr<Ros2Publisher> createPublisher(Ros2NodeHandle* nodeHandle,
                                                           const char* topicName,
                                                           const void* typeSupport,
                                                           const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Subscriber> createSubscriber(Ros2NodeHandle* nodeHandle,
                                                             const char* topicName,
                                                             const void* typeSupport,
                                                             const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Service> createService(Ros2NodeHandle* nodeHandle,
                                                       const char* serviceName,
                                                       const void* typeSupport,
                                                       const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Client> createClient(Ros2NodeHandle* nodeHandle,
                                                     const char* serviceName,
                                                     const void* typeSupport,
                                                     const Ros2QoSProfile& qos);

    virtual std::shared_ptr<Ros2ClockMessage> createClockMessage();
    virtual std::shared_ptr<Ros2ImuMessage> createImuMessage();
    virtual std::shared_ptr<Ros2CameraInfoMessage> createCameraInfoMessage();
    virtual std::shared_ptr<Ros2ImageMessage> createImageMessage();
    virtual std::shared_ptr<Ros2NitrosBridgeImageMessage> createNitrosBridgeImageMessage();
    virtual std::shared_ptr<Ros2BoundingBox2DMessage> createBoundingBox2DMessage();
    virtual std::shared_ptr<Ros2BoundingBox3DMessage> createBoundingBox3DMessage();
    virtual std::shared_ptr<Ros2OdometryMessage> createOdometryMessage();
    virtual std::shared_ptr<Ros2RawTfTreeMessage> createRawTfTreeMessage();
    virtual std::shared_ptr<Ros2SemanticLabelMessage> createSemanticLabelMessage();
    virtual std::shared_ptr<Ros2JointStateMessage> createJointStateMessage();
    virtual std::shared_ptr<Ros2PointCloudMessage> createPointCloudMessage();
    virtual std::shared_ptr<Ros2LaserScanMessage> createLaserScanMessage();
    virtual std::shared_ptr<Ros2TfTreeMessage> createTfTreeMessage();
    virtual std::shared_ptr<Ros2TwistMessage> createTwistMessage();
    virtual std::shared_ptr<Ros2AckermannDriveStampedMessage> createAckermannDriveStampedMessage();
    virtual std::shared_ptr<Ros2Message> createDynamicMessage(const std::string& pkgName,
                                                              const std::string& msgSubfolder,
                                                              const std::string& msgName,
                                                              BackendMessageType messageType = BackendMessageType::eMessage);

    virtual bool validateTopicName(const std::string& topicName);
    virtual bool validateNamespaceName(const std::string& namespaceName);
    virtual bool validateNodeName(const std::string& nodeName);
};

} // namespace ros2_bridge
} // namespace isaac
} // namespace omni

#ifdef _MSC_VER
extern "C" __declspec(dllexport) omni::isaac::ros2_bridge::Ros2Factory* createFactory();
#else
extern "C" omni::isaac::ros2_bridge::Ros2Factory* createFactory();
#endif
