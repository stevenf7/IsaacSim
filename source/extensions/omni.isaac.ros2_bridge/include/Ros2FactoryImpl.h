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

class Ros2FactoryImpl : public Ros2Factory
{
public:
    virtual std::shared_ptr<Ros2HandleBase> CreateHandle();
    virtual std::shared_ptr<Ros2NodeBase> CreateNode(const char* name, const char* name_space, Ros2HandleBase* handle);
    virtual std::shared_ptr<Ros2Publisher> CreatePublisher(Ros2NodeBase* node,
                                                           const char* topic_name,
                                                           const void* type,
                                                           const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Subscriber> CreateSubscriber(Ros2NodeBase* node,
                                                             const char* topic_name,
                                                             const void* type,
                                                             const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Service> CreateService(Ros2NodeBase* node,
                                                       const char* service_name,
                                                       const void* type,
                                                       const Ros2QoSProfile& qos);
    virtual std::shared_ptr<Ros2Client> CreateClient(Ros2NodeBase* node,
                                                     const char* service_name,
                                                     const void* type,
                                                     const Ros2QoSProfile& qos);

    virtual std::shared_ptr<Ros2ClockMessage> CreateClockMessage();
    virtual std::shared_ptr<Ros2ImuMessage> CreateImuMessage();
    virtual std::shared_ptr<Ros2CameraInfoMessage> CreateCameraInfoMessage();
    virtual std::shared_ptr<Ros2ImageMessage> CreateImageMessage();
    virtual std::shared_ptr<Ros2NitrosBridgeImageMessage> CreateNitrosBridgeImageMessage();
    virtual std::shared_ptr<Ros2BoundingBox2DMessage> CreateBoundingBox2DMessage();
    virtual std::shared_ptr<Ros2BoundingBox3DMessage> CreateBoundingBox3DMessage();
    virtual std::shared_ptr<Ros2OdomMessage> CreateOdomMessage();
    virtual std::shared_ptr<Ros2RawTfTreeMessage> CreateRawTfTreeMessage();
    virtual std::shared_ptr<Ros2SemanticLabelMessage> CreateSemanticLabelMessage();
    virtual std::shared_ptr<Ros2JointStateMessage> CreateJointStateMessage();
    virtual std::shared_ptr<Ros2PointCloudMessage> CreatePointCloudMessage();
    virtual std::shared_ptr<Ros2LaserScanMessage> CreateLaserScanMessage();
    virtual std::shared_ptr<Ros2TfTreeMessage> CreateTfTreeMessage();
    virtual std::shared_ptr<Ros2TwistMessage> CreateTwistMessage();
    virtual std::shared_ptr<Ros2AckermannDriveStampedMessage> CreateAckermannDriveStampedMessage();
    virtual bool validateTopic(const std::string& topicName);
    virtual bool validateNodeNamespace(const std::string& nodeNamespace);
    virtual bool validateNodeName(const std::string& nodeName);

    virtual std::shared_ptr<Ros2Message> createDynamicMessage(const std::string& pkgName,
                                                              const std::string& msgSubfolder,
                                                              const std::string& msgName,
                                                              BackendMessageType messageType = BackendMessageType::eMessage);
};


#ifdef _MSC_VER
extern "C" __declspec(dllexport) Ros2Factory* createFactory();
#else
extern "C" Ros2Factory* createFactory();
#endif
