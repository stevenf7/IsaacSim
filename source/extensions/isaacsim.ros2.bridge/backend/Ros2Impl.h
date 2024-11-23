// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#if !defined(_WIN32)
#    include "isaac_ros_nitros_bridge_interfaces/msg/nitros_bridge_image.h"
#endif

#include "ackermann_msgs/msg/ackermann_drive_stamped.h"
#include "builtin_interfaces/msg/time.h"
#include "geometry_msgs/msg/transform_stamped.h"
#include "geometry_msgs/msg/twist.h"
#include "nav_msgs/msg/odometry.h"
#include "rosidl_runtime_c/action_type_support_struct.h"
#include "rosidl_runtime_c/primitives_sequence_functions.h"
#include "rosidl_runtime_c/string_functions.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"
#include "sensor_msgs/msg/image.h"
#include "sensor_msgs/msg/imu.h"
#include "sensor_msgs/msg/joint_state.h"
#include "sensor_msgs/msg/laser_scan.h"
#include "sensor_msgs/msg/point_cloud2.h"
#include "sensor_msgs/msg/point_field.h"
#include "tf2_msgs/msg/tf_message.h"
#include "vision_msgs/msg/detection2_d.h"
#include "vision_msgs/msg/detection2_d_array.h"
#include "vision_msgs/msg/detection3_d.h"
#include "vision_msgs/msg/detection3_d_array.h"
#include "vision_msgs/msg/object_hypothesis_with_pose.h"

#include <include/Ros2FactoryImpl.h>
#include <nlohmann/json.hpp>
#include <omni/physics/tensors/IArticulationView.h>
#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rosgraph_msgs/msg/clock.h>
#include <std_msgs/msg/header.h>
#include <std_msgs/msg/string.h>
namespace isaacsim
{
namespace ros2
{
namespace bridge
{

class Ros2MessageInterfaceImpl : public Ros2MessageInterface
{
public:
    Ros2MessageInterfaceImpl(std::string pkgName,
                             std::string msgSubfolder,
                             std::string msgName,
                             BackendMessageType messageType = BackendMessageType::eMessage,
                             bool showLoadingError = false);
    void writeRosTime(const int64_t nanoseconds, builtin_interfaces__msg__Time& time);
    void writeRosString(const std::string& input, rosidl_runtime_c__String& output);
    void writeRosHeader(const std::string& frameId, const int64_t nanoseconds, std_msgs__msg__Header& header);
};

class Ros2ClockMessageImpl : public Ros2ClockMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2ClockMessageImpl();
    virtual ~Ros2ClockMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void readData(double& timeStamp);
    virtual void writeData(double timeStamp);
};

class Ros2ImuMessageImpl : public Ros2ImuMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2ImuMessageImpl();
    virtual ~Ros2ImuMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(double timeStamp, std::string& frameId);
    virtual void writeAcceleration(bool covariance, const std::vector<double>& acceleration);
    virtual void writeVelocity(bool covariance, const std::vector<double>& velocity);
    virtual void writeOrientation(bool covariance, const std::vector<double>& orientation);
};

class Ros2CameraInfoMessageImpl : public Ros2CameraInfoMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2CameraInfoMessageImpl();
    virtual ~Ros2CameraInfoMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeResolution(const uint32_t height, const uint32_t width);
    virtual void writeIntrinsicMatrix(const double array[], const int arraySize);
    virtual void writeProjectionMatrix(const double array[], const int arraySize);
    virtual void writeRectificationMatrix(const double array[], const int arraySize);
    virtual void writeDistortionParameters(std::vector<double>& array, const std::string& distortionModel);
};

class Ros2ImageMessageImpl : public Ros2ImageMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2ImageMessageImpl();
    virtual ~Ros2ImageMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
};

class Ros2NitrosBridgeImageMessageImpl : public Ros2NitrosBridgeImageMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2NitrosBridgeImageMessageImpl();
    virtual ~Ros2NitrosBridgeImageMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
    virtual void writeData(const std::vector<int32_t>& imageData);
};

class Ros2BoundingBox2DMessageImpl : public Ros2BoundingBox2DMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2BoundingBox2DMessageImpl();
    virtual ~Ros2BoundingBox2DMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2BoundingBox3DMessageImpl : public Ros2BoundingBox3DMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2BoundingBox3DMessageImpl();
    virtual ~Ros2BoundingBox3DMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2OdometryMessageImpl : public Ros2OdometryMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2OdometryMessageImpl();
    virtual ~Ros2OdometryMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeData(std::string& childFrame,
                           const pxr::GfVec3d& linearVelocity,
                           const pxr::GfVec3d& angularVelocity,
                           const pxr::GfVec3f& robotFront,
                           const pxr::GfVec3f& robotSide,
                           double unitScale,
                           bool zUp,
                           const pxr::GfVec3d& position,
                           const pxr::GfQuatd& orientation);
};

class Ros2RawTfTreeMessageImpl : public Ros2RawTfTreeMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2RawTfTreeMessageImpl();
    virtual ~Ros2RawTfTreeMessageImpl();
    virtual const void* getTypeSupportHandle();
    // virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeData(const double timeStamp,
                           const std::string& frameId,
                           const std::string& childFrame,
                           const pxr::GfVec3d& translation,
                           const pxr::GfQuatd& rotation);
};

class Ros2SemanticLabelMessageImpl : public Ros2SemanticLabelMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2SemanticLabelMessageImpl();
    virtual ~Ros2SemanticLabelMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeData(const std::string& data);
};

class Ros2JointStateMessageImpl : public Ros2JointStateMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2JointStateMessageImpl();
    virtual ~Ros2JointStateMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeData(const double& timeStamp,
                           omni::physics::tensors::IArticulationView* articulation,
                           pxr::UsdStageWeakPtr stage,
                           std::vector<float>& jointPosition,
                           std::vector<float>& jointVelocity,
                           std::vector<float>& jointEffort,
                           std::vector<uint8_t>& dofTypes,
                           const double& stageUnits);

    virtual void readData(std::vector<char*>& jointNames,
                          double* jointPositions,
                          double* jointVelocities,
                          double* jointEfforts,
                          double& timeStamp);

    virtual size_t getNumJoints();
    virtual bool checkValid();
};

class Ros2PointCloudMessageImpl : public Ros2PointCloudMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2PointCloudMessageImpl();
    virtual ~Ros2PointCloudMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void generateBuffer(const double& timeStamp,
                                const std::string& frameId,
                                const size_t& width,
                                const size_t& height,
                                const uint32_t& pointStep);
};

class Ros2LaserScanMessageImpl : public Ros2LaserScanMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2LaserScanMessageImpl();
    virtual ~Ros2LaserScanMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeData(const double& timeStamp,
                           const std::string& frameId,
                           const pxr::GfVec2f& azimuthRange,
                           const float& rotationRate,
                           const pxr::GfVec2f& depthRange,
                           size_t buffSize,
                           float* rangeData,
                           float* intensitiesData,
                           float horizontalResolution,
                           float horizontalFov) override;
};

class Ros2TfTreeMessageImpl : public Ros2TfTreeMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2TfTreeMessageImpl();
    virtual ~Ros2TfTreeMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void writeData(const double& timeStamp, std::vector<TfTransformStamped>& transforms);
    virtual void readData(std::vector<TfTransformStamped>& transforms);
};

class Ros2TwistMessageImpl : public Ros2TwistMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2TwistMessageImpl();
    virtual ~Ros2TwistMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void readData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity);
};

class Ros2AckermannDriveStampedMessageImpl : public Ros2AckermannDriveStampedMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2AckermannDriveStampedMessageImpl();
    virtual ~Ros2AckermannDriveStampedMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void readData(double& timeStamp,
                          std::string& frameId,
                          double& steeringAngle,
                          double& steeringAngleVelocity,
                          double& speed,
                          double& acceleration,
                          double& jerk);
    virtual void writeHeader(const double timeStamp, const std::string& frameId);
    virtual void writeData(const double& steeringAngle,
                           const double& steeringAngleVelocity,
                           const double& speed,
                           const double& acceleration,
                           const double& jerk);
};

class Ros2ContextHandleImpl : public Ros2ContextHandle
{
public:
    virtual ~Ros2ContextHandleImpl()
    {
        shutdown();
    }
    virtual void* getContext();
    virtual void init(int argc, char const* const* argv, bool setDomainId = false, size_t domainId = 0);
    virtual bool isValid();
    virtual bool shutdown(const char* shutdownReason = nullptr);

private:
    rcl_init_options_t m_initOptions;
    std::shared_ptr<rcl_context_t> m_context;
};

class Ros2NodeHandleImpl : public Ros2NodeHandle
{
public:
    Ros2NodeHandleImpl(const char* name, const char* namespaceName, Ros2ContextHandle* contextHandle);
    virtual ~Ros2NodeHandleImpl();
    virtual Ros2ContextHandle* getContextHandle();
    virtual void* getNode();

private:
    Ros2ContextHandle* m_contextHandle;
    std::shared_ptr<rcl_node_t> m_node;
};

class Ros2PublisherImpl : public Ros2Publisher
{
public:
    Ros2PublisherImpl(Ros2NodeHandle* nodeHandle, const char* topicName, const void* typeSupport, const Ros2QoSProfile& qos);
    virtual ~Ros2PublisherImpl();
    virtual void publish(const void* msg);
    virtual size_t getSubscriptionCount();
    virtual bool isValid()
    {
        return m_publisher != nullptr;
    }

private:
    Ros2NodeHandle* m_nodeHandle;
    std::shared_ptr<rcl_publisher_t> m_publisher = nullptr;
};

class Ros2SubscriberImpl : public Ros2Subscriber
{
public:
    Ros2SubscriberImpl(Ros2NodeHandle* nodeHandle,
                       const char* topicName,
                       const void* typeSupport,
                       const Ros2QoSProfile& qos);
    virtual ~Ros2SubscriberImpl();
    virtual bool spin(void* msg);
    virtual bool isValid()
    {
        return m_subscription != nullptr;
    }

private:
    Ros2NodeHandle* m_nodeHandle;
    std::shared_ptr<rcl_subscription_t> m_subscription = nullptr;
    rcl_wait_set_t m_waitSet;
    bool m_waitSetInitialized = false;
};

class Ros2ServiceImpl : public Ros2Service
{
public:
    Ros2ServiceImpl(Ros2NodeHandle* nodeHandle, const char* serviceName, const void* typeSupport, const Ros2QoSProfile& qos);
    virtual ~Ros2ServiceImpl();
    virtual bool takeRequest(void* requestMsg);
    virtual bool sendResponse(void* responseMsg);
    virtual bool isValid()
    {
        return m_service != nullptr;
    }

private:
    Ros2NodeHandle* m_nodeHandle;
    std::shared_ptr<rcl_service_t> m_service = nullptr;
    rcl_wait_set_t m_waitSet;
    rmw_request_id_t m_requestId;
    bool m_waitSetInitialized = false;
};

class Ros2ClientImpl : public Ros2Client
{
public:
    Ros2ClientImpl(Ros2NodeHandle* nodeHandle, const char* serviceName, const void* typeSupport, const Ros2QoSProfile& qos);
    virtual ~Ros2ClientImpl();
    virtual bool sendRequest(void* requestMsg);
    virtual bool takeResponse(void* responseMsg);
    virtual bool isValid()
    {
        return m_client != nullptr;
    }

private:
    Ros2NodeHandle* m_nodeHandle;
    std::shared_ptr<rcl_client_t> m_client = nullptr;
    rcl_wait_set_t m_waitSet;
    rmw_request_id_t m_requestId;
    bool m_waitSetInitialized = false;
};

class Ros2DynamicMessageImpl : public Ros2DynamicMessage, Ros2MessageInterfaceImpl
{
public:
    Ros2DynamicMessageImpl(std::string pkgName,
                           std::string msgSubfolder,
                           std::string msgName,
                           BackendMessageType messageType = BackendMessageType::eMessage);
    virtual ~Ros2DynamicMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual std::string generateSummary(bool print);
    virtual const nlohmann::json& readData();
    virtual const std::vector<std::shared_ptr<void>>& readData(bool asOgnType);
    virtual void writeData(const nlohmann::json& data);
    virtual void writeData(const std::vector<std::shared_ptr<void>>& data, bool fromOgnType);

protected:
    virtual const void* getIntrospectionMembers();
    virtual void parseMessageFields(const std::string& parentName, const void* members);

    virtual void getMessageValues(const void* members, uint8_t* messageData, nlohmann::json& container);
    virtual void getMessageValues(const void* members,
                                  uint8_t* messageData,
                                  std::vector<std::shared_ptr<void>>& container,
                                  size_t& index,
                                  bool asOgnType);
    virtual void setMessageValues(const void* members, uint8_t* messageData, const nlohmann::json& container);
    virtual void setMessageValues(const void* members,
                                  uint8_t* messageData,
                                  const std::vector<std::shared_ptr<void>>& container,
                                  size_t& index,
                                  bool fromOgnType);

    template <typename ArrayType, typename RosType>
    void getArray(const rosidl_typesupport_introspection_c__MessageMember* member, uint8_t* data, nlohmann::json& array);
    template <typename ArrayType, typename RosType, typename OgnType>
    void getArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  std::shared_ptr<void>& valuePtr,
                  bool asOgnType);
    template <typename ArrayType, typename RosType>
    void getArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  std::vector<RosType>& array);

    template <typename ArrayType, auto ArrayInit, typename RosType>
    void setArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  const nlohmann::json& value);
    template <typename ArrayType, auto ArrayInit, typename RosType, typename OgnType>
    void setArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  const std::shared_ptr<void>& valuePtr,
                  bool fromOgnType);
    template <typename ArrayType, auto ArrayInit, typename RosType>
    void setArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  const std::vector<RosType>& array);

    template <typename RosType, typename OgnType>
    void getSingleValue(uint8_t* data, std::shared_ptr<void>& valuePtr, bool asOgnType);

    template <typename RosType, typename OgnType>
    void setSingleValue(uint8_t* data, const std::shared_ptr<void>& valuePtr, bool fromOgnType);

    void getArrayEmbeddedMessage(const rosidl_typesupport_introspection_c__MessageMember* member,
                                 uint8_t* data,
                                 nlohmann::json& array);

    void setArrayEmbeddedMessage(const rosidl_typesupport_introspection_c__MessageMember* member,
                                 uint8_t* data,
                                 const nlohmann::json& array);
};

class Ros2QoSProfileConverter
{
public:
    static rmw_qos_profile_t convert(const Ros2QoSProfile& qos);
};

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
