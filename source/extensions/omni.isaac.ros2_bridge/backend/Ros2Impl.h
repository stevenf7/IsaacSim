// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
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
#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rosgraph_msgs/msg/clock.h>
#include <std_msgs/msg/header.h>
#include <std_msgs/msg/string.h>

class Ros2BackendImpl : public Ros2Backend
{
public:
    Ros2BackendImpl(std::string pkgName,
                    std::string msgSubfolder,
                    std::string msgName,
                    BackendMessageType messageType = BackendMessageType::eMessage,
                    bool testLibrary = false);
    void set_timestamp(const int64_t nanoseconds, builtin_interfaces__msg__Time& time);
    void set_string(const std::string& input, rosidl_runtime_c__String& output);
    void set_header(const std::string& frame_id, const int64_t nanoseconds, std_msgs__msg__Header& header);
};

class Ros2ClockMessageImpl : public Ros2ClockMessage, Ros2BackendImpl
{
public:
    Ros2ClockMessageImpl();
    virtual ~Ros2ClockMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fill(double timestamp);
    virtual void setData(double& timeStamp);
};

class Ros2ImuMessageImpl : public Ros2ImuMessage, Ros2BackendImpl
{
public:
    Ros2ImuMessageImpl();
    virtual ~Ros2ImuMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(double timestamp, std::string& frame_id);
    virtual void fillAccel(bool covariance, const std::vector<double>& accel);
    virtual void fillVelo(bool covariance, const std::vector<double>& velo);
    virtual void fillOrient(bool covariance, const std::vector<double>& orient);
};

class Ros2CameraInfoMessageImpl : public Ros2CameraInfoMessage, Ros2BackendImpl
{
public:
    Ros2CameraInfoMessageImpl();
    virtual ~Ros2CameraInfoMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillHeightWidth(const uint32_t height, const uint32_t width);
    virtual void fillIntrisicArray(const double k_arr[], const int numElem);
    virtual void fillProjectionArray(const double p_arr[], const int numElem);
    virtual void fillRectificationArray(const double r_arr[], const int numElem);
    virtual void fillDistortionModel(std::vector<double>& distort_array, const std::string& distort_model);
};

class Ros2ImageMessageImpl : public Ros2ImageMessage, Ros2BackendImpl
{
public:
    Ros2ImageMessageImpl();
    virtual ~Ros2ImageMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
};

class Ros2NitrosBridgeImageMessageImpl : public Ros2NitrosBridgeImageMessage, Ros2BackendImpl
{
public:
    Ros2NitrosBridgeImageMessageImpl();
    virtual ~Ros2NitrosBridgeImageMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
    virtual void setData(const std::vector<int32_t>& imageData);
};

class Ros2BoundingBox2DMessageImpl : public Ros2BoundingBox2DMessage, Ros2BackendImpl
{
public:
    Ros2BoundingBox2DMessageImpl();
    virtual ~Ros2BoundingBox2DMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2BoundingBox3DMessageImpl : public Ros2BoundingBox3DMessage, Ros2BackendImpl
{
public:
    Ros2BoundingBox3DMessageImpl();
    virtual ~Ros2BoundingBox3DMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2OdomMessageImpl : public Ros2OdomMessage, Ros2BackendImpl
{
public:
    Ros2OdomMessageImpl();
    virtual ~Ros2OdomMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillData(std::string& childFrame,
                          const pxr::GfVec3d& linVel,
                          const pxr::GfVec3d& angVel,
                          const pxr::GfVec3f& mRobotFront,
                          const pxr::GfVec3f& mRobotSide,
                          double mUnitScale,
                          bool mZUp,
                          const pxr::GfVec3d& position,
                          const pxr::GfQuatd& orientation);
};

class Ros2RawTfTreeMessageImpl : public Ros2RawTfTreeMessage, Ros2BackendImpl
{
public:
    Ros2RawTfTreeMessageImpl();
    virtual ~Ros2RawTfTreeMessageImpl();
    virtual const void* getTypeSupportHandle();
    // virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillData(const double timestamp,
                          const std::string& headerFrame,
                          const std::string& childFrame,
                          const pxr::GfVec3d& translation,
                          const pxr::GfQuatd& rotation);
};

class Ros2SemanticLabelMessageImpl : public Ros2SemanticLabelMessage, Ros2BackendImpl
{
public:
    Ros2SemanticLabelMessageImpl();
    virtual ~Ros2SemanticLabelMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const std::string& data);
};

class Ros2JointStateMessageImpl : public Ros2JointStateMessage, Ros2BackendImpl
{
public:
    Ros2JointStateMessageImpl();
    virtual ~Ros2JointStateMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const double& timeStamp,
                          omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr,
                          omni::isaac::dynamic_control::DcHandle mArticulationHandle,
                          pxr::UsdStageWeakPtr mStage,
                          std::vector<omni::isaac::dynamic_control::DcDofProperties>& mDofProps,
                          std::vector<float>& mPrevJointPosition,
                          std::vector<float>& mCalculatedJointVelocity,
                          const double& dt,
                          const double& stageUnits);

    virtual void getData(std::vector<char*>& jointNames,
                         double* positionCommand,
                         double* velocityCommand,
                         double* effortCommand,
                         double& timeStamp);

    virtual void getActuators(size_t& actuators);

    virtual bool checkValid();
};


class Ros2PointCloudMessageImpl : public Ros2PointCloudMessage, Ros2BackendImpl
{
public:
    Ros2PointCloudMessageImpl();
    virtual ~Ros2PointCloudMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillMetadata(const std::string& frameId,
                              const double& timeStamp,
                              const size_t& width,
                              const size_t& height,
                              const uint32_t& point_step);
};


class Ros2LaserScanMessageImpl : public Ros2LaserScanMessage, Ros2BackendImpl
{
public:
    Ros2LaserScanMessageImpl();
    virtual ~Ros2LaserScanMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const std::string& frameId,
                          const double& timeStamp,
                          const pxr::GfVec2f& azimuthRange,
                          const float& rotationRate,
                          const pxr::GfVec2f& depthRange,
                          size_t buffSize,
                          float* rangeData,
                          float* intensitiesData,
                          float horizontalResolution,
                          float horizontalFov) override;
};


class Ros2TfTreeMessageImpl : public Ros2TfTreeMessage, Ros2BackendImpl
{
public:
    Ros2TfTreeMessageImpl();
    virtual ~Ros2TfTreeMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const double& timeStamp, std::vector<tfMessageStruct>& tfMsg_vec);
    virtual void getData(std::vector<tfMessageStruct>& tfMsg_vec);
};


class Ros2TwistMessageImpl : public Ros2TwistMessage, Ros2BackendImpl
{
public:
    Ros2TwistMessageImpl();
    virtual ~Ros2TwistMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void getData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity);
};

class Ros2AckermannDriveStampedMessageImpl : public Ros2AckermannDriveStampedMessage, Ros2BackendImpl
{
public:
    Ros2AckermannDriveStampedMessageImpl();
    virtual ~Ros2AckermannDriveStampedMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual void getData(std::string& frameId,
                         double& timeStamp,
                         double& steeringAngle,
                         double& steeringAngleVelocity,
                         double& speed,
                         double& acceleration,
                         double& jerk);
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillData(const double& steeringAngle,
                          const double& steeringAngleVelocity,
                          const double& speed,
                          const double& acceleration,
                          const double& jerk);
};

class Ros2HandleImpl : public Ros2HandleBase
{
public:
    virtual ~Ros2HandleImpl()
    {
        shutdown();
    }
    virtual void* context();
    virtual void init(int argc, char const* const* argv, bool setDomainId = false, size_t domainId = 0);
    virtual bool is_valid();
    virtual bool shutdown(const char* shutdown_reason = nullptr);

private:
    rcl_init_options_t mInitOptions;
    std::shared_ptr<rcl_context_t> mContext;
};


class Ros2NodeImpl : public Ros2NodeBase
{
public:
    Ros2NodeImpl(const char* name, const char* name_space, Ros2HandleBase* rcl_handle);
    virtual ~Ros2NodeImpl();
    virtual Ros2HandleBase* handle();
    virtual void* node();

private:
    Ros2HandleBase* mHandle;
    std::shared_ptr<rcl_node_t> mNode;
};

class Ros2PublisherImpl : public Ros2Publisher
{
public:
    Ros2PublisherImpl(Ros2NodeBase* node, const char* topic_name, const void* type, const Ros2QoSProfile& qos);
    virtual ~Ros2PublisherImpl();
    virtual void publish(const void* msg);
    virtual size_t get_subscription_count();
    virtual bool isValid()
    {
        return mPub != nullptr;
    }

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_publisher_t> mPub = nullptr;
};

class Ros2SubscriberImpl : public Ros2Subscriber
{
public:
    Ros2SubscriberImpl(Ros2NodeBase* node, const char* topic_name, const void* type, const Ros2QoSProfile& qos);
    virtual ~Ros2SubscriberImpl();
    virtual bool spin(void* msg);
    virtual bool isValid()
    {
        return mSub != nullptr;
    }

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_subscription_t> mSub = nullptr;
    rcl_wait_set_t wait_set;
    bool wait_set_initialized = false;
};

class Ros2ServiceImpl : public Ros2Service
{
public:
    Ros2ServiceImpl(Ros2NodeBase* node, const char* service_name, const void* type, const Ros2QoSProfile& qos);
    virtual ~Ros2ServiceImpl();
    virtual bool getRequest(void* msg);
    virtual bool sendResponse(void* msg);
    virtual bool isValid()
    {
        return mService != nullptr;
    }

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_service_t> mService = nullptr;
    rcl_wait_set_t wait_set;
    rmw_request_id_t request_id;
    bool wait_set_initialized = false;
};

class Ros2ClientImpl : public Ros2Client
{
public:
    Ros2ClientImpl(Ros2NodeBase* node, const char* service_name, const void* type, const Ros2QoSProfile& qos);
    virtual ~Ros2ClientImpl();
    virtual bool sendRequest(void* msg);
    virtual bool getResponse(void* msg);
    virtual bool isValid()
    {
        return mClient != nullptr;
    }

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_client_t> mClient = nullptr;
    rcl_wait_set_t wait_set;
    rmw_request_id_t request_id;
    bool wait_set_initialized = false;
};

class Ros2DynamicMessageImpl : public Ros2DynamicMessage, Ros2BackendImpl
{
public:
    Ros2DynamicMessageImpl(std::string pkgName,
                           std::string msgSubfolder,
                           std::string msgName,
                           BackendMessageType messageType = BackendMessageType::eMessage);
    virtual ~Ros2DynamicMessageImpl();
    virtual const void* getTypeSupportHandle();
    virtual std::string summary(bool print);
    virtual const nlohmann::json& getData();
    virtual const std::vector<std::shared_ptr<void>>& getData(bool asOgnType);
    virtual void setData(const nlohmann::json& data);
    virtual void setData(const std::vector<std::shared_ptr<void>>& data, bool fromOgnType);

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
