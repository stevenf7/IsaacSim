// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

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

#include <include/Ros2FactoryHumble.h>
#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rosgraph_msgs/msg/clock.h>
#include <std_msgs/msg/header.h>
#include <std_msgs/msg/string.h>

class Ros2BackendHumble : public Ros2Backend
{
public:
    Ros2BackendHumble(std::string pkgName,
                      std::string msgSubfolder,
                      std::string msgName,
                      BackendMessageType messageType = BackendMessageType::eMessage);
    void set_timestamp(const int64_t nanoseconds, builtin_interfaces__msg__Time& time);
    void set_string(const std::string& input, rosidl_runtime_c__String& output);
    void set_header(const std::string& frame_id, const int64_t nanoseconds, std_msgs__msg__Header& header);
};

class Ros2ClockMessageHumble : public Ros2ClockMessage, Ros2BackendHumble
{
public:
    Ros2ClockMessageHumble();
    virtual ~Ros2ClockMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fill(double timestamp);
    virtual void setData(double& timeStamp);
};

class Ros2ImuMessageHumble : public Ros2ImuMessage, Ros2BackendHumble
{
public:
    Ros2ImuMessageHumble();
    virtual ~Ros2ImuMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(double timestamp, std::string& frame_id);
    virtual void fillAccel(bool covariance, const std::vector<double>& accel);
    virtual void fillVelo(bool covariance, const std::vector<double>& velo);
    virtual void fillOrient(bool covariance, const std::vector<double>& orient);
};

class Ros2CameraInfoMessageHumble : public Ros2CameraInfoMessage, Ros2BackendHumble
{
public:
    Ros2CameraInfoMessageHumble();
    virtual ~Ros2CameraInfoMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillHeightWidth(const uint32_t height, const uint32_t width);
    virtual void fillIntrisicArray(const double k_arr[], const int numElem);
    virtual void fillProjectionArray(const double p_arr[], const int numElem);
    virtual void fillRectificationArray(const double r_arr[], const int numElem);
    virtual void fillDistortionModel(std::vector<double>& distort_array, const std::string& distort_model);
};

class Ros2ImageMessageHumble : public Ros2ImageMessage, Ros2BackendHumble
{
public:
    Ros2ImageMessageHumble();
    virtual ~Ros2ImageMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
};

class Ros2BoundingBox2DMessageHumble : public Ros2BoundingBox2DMessage, Ros2BackendHumble
{
public:
    Ros2BoundingBox2DMessageHumble();
    virtual ~Ros2BoundingBox2DMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2BoundingBox3DMessageHumble : public Ros2BoundingBox3DMessage, Ros2BackendHumble
{
public:
    Ros2BoundingBox3DMessageHumble();
    virtual ~Ros2BoundingBox3DMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2OdomMessageHumble : public Ros2OdomMessage, Ros2BackendHumble
{
public:
    Ros2OdomMessageHumble();
    virtual ~Ros2OdomMessageHumble();
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

class Ros2RawTfTreeMessageHumble : public Ros2RawTfTreeMessage, Ros2BackendHumble
{
public:
    Ros2RawTfTreeMessageHumble();
    virtual ~Ros2RawTfTreeMessageHumble();
    virtual const void* getTypeSupportHandle();
    // virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillData(const double timestamp,
                          const std::string& headerFrame,
                          const std::string& childFrame,
                          const pxr::GfVec3d& translation,
                          const pxr::GfQuatd& rotation);
};

class Ros2SemanticLabelMessageHumble : public Ros2SemanticLabelMessage, Ros2BackendHumble
{
public:
    Ros2SemanticLabelMessageHumble();
    virtual ~Ros2SemanticLabelMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const std::string& data);
};

class Ros2JointStateMessageHumble : public Ros2JointStateMessage, Ros2BackendHumble
{
public:
    Ros2JointStateMessageHumble();
    virtual ~Ros2JointStateMessageHumble();
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


class Ros2PointCloudMessageHumble : public Ros2PointCloudMessage, Ros2BackendHumble
{
public:
    Ros2PointCloudMessageHumble();
    virtual ~Ros2PointCloudMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillMetadata(const std::string& frameId,
                              const double& timeStamp,
                              const size_t& width,
                              const size_t& height,
                              const uint32_t& point_step);
};


class Ros2LaserScanMessageHumble : public Ros2LaserScanMessage, Ros2BackendHumble
{
public:
    Ros2LaserScanMessageHumble();
    virtual ~Ros2LaserScanMessageHumble();
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


class Ros2TfTreeMessageHumble : public Ros2TfTreeMessage, Ros2BackendHumble
{
public:
    Ros2TfTreeMessageHumble();
    virtual ~Ros2TfTreeMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const double& timeStamp, std::vector<tfMessageStruct>& tfMsg_vec);
    virtual void getData(std::vector<tfMessageStruct>& tfMsg_vec);
};


class Ros2TwistMessageHumble : public Ros2TwistMessage, Ros2BackendHumble
{
public:
    Ros2TwistMessageHumble();
    virtual ~Ros2TwistMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void getData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity);
};

class Ros2AckermannDriveStampedMessageHumble : public Ros2AckermannDriveStampedMessage, Ros2BackendHumble
{
public:
    Ros2AckermannDriveStampedMessageHumble();
    virtual ~Ros2AckermannDriveStampedMessageHumble();
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

class Ros2HandleHumble : public Ros2HandleBase
{
public:
    virtual ~Ros2HandleHumble()
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


class Ros2NodeHumble : public Ros2NodeBase
{
public:
    Ros2NodeHumble(const char* name, const char* name_space, Ros2HandleBase* rcl_handle);
    virtual ~Ros2NodeHumble();
    virtual Ros2HandleBase* handle();
    virtual void* node();

private:
    Ros2HandleBase* mHandle;
    std::shared_ptr<rcl_node_t> mNode;
};

class Ros2PublisherHumble : public Ros2Publisher
{
public:
    Ros2PublisherHumble(Ros2NodeBase* node, const char* topic_name, const void* type, const size_t history_depth);
    virtual ~Ros2PublisherHumble();
    virtual void publish(const void* msg);
    virtual size_t get_subscription_count();

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_publisher_t> mPub;
};

class Ros2SubscriberHumble : public Ros2Subscriber
{
public:
    Ros2SubscriberHumble(Ros2NodeBase* node, const char* topic_name, const void* type, const size_t history_depth);
    virtual ~Ros2SubscriberHumble();
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

class Ros2ServiceHumble : public Ros2Service
{
public:
    Ros2ServiceHumble(Ros2NodeBase* node, const char* service_name, const void* type);
    virtual ~Ros2ServiceHumble();
    virtual bool spin(void* msg);
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

class Ros2DynamicMessageHumble : public Ros2DynamicMessage, Ros2BackendHumble
{
public:
    Ros2DynamicMessageHumble(std::string pkgName,
                             std::string msgSubfolder,
                             std::string msgName,
                             BackendMessageType messageType = BackendMessageType::eMessage);
    virtual ~Ros2DynamicMessageHumble();
    virtual const void* getTypeSupportHandle();
    virtual void getData(std::vector<std::shared_ptr<const void>>& data, bool asOgnType);
    virtual void setData(const std::vector<std::shared_ptr<const void>>& data, bool fromOgnType);

protected:
    virtual const void* getIntrospectionMembers();
    virtual void parseMessageFields(const std::string& parentName, const void* members);
    virtual void parseMessageValues(const void* members,
                                    uint8_t* data,
                                    std::vector<std::shared_ptr<const void>>& messageValues,
                                    bool asOgnType);
    virtual void setMessageValues(const void* members,
                                  uint8_t* messageData,
                                  const std::vector<std::shared_ptr<const void>>& messageValues,
                                  bool fromOgnType);

    template <typename ArrayType, typename RosType, typename OgnType>
    std::shared_ptr<const void> getArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                                         uint8_t* data,
                                         bool asOgnType);

    template <typename ArrayType, auto ArrayInit, typename RosType, typename OgnType>
    void setArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                  uint8_t* data,
                  std::shared_ptr<const void> value,
                  bool fromOgnType);

    template <typename RosType, typename OgnType>
    std::shared_ptr<const void> getSingleValue(uint8_t* data, bool asOgnType);

    template <typename RosType, typename OgnType>
    void setSingleValue(uint8_t* data, std::shared_ptr<const void> value, bool fromOgnType);

    void messageValuesToJson(const void* members,
                             uint8_t* messageData,
                             const std::shared_ptr<std::vector<std::string>> messageValues);
    void embeddedMessageArrayToJson(const rosidl_typesupport_introspection_c__MessageMember* member,
                                    uint8_t* data,
                                    const std::shared_ptr<std::vector<std::string>> messageValues);
};
