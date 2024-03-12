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
#include "rosidl_runtime_c/primitives_sequence_functions.h"
#include "rosidl_runtime_c/string_functions.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
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

#include <include/Ros2FactoryFoxy.h>
#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rosgraph_msgs/msg/clock.h>
#include <std_msgs/msg/header.h>
#include <std_msgs/msg/string.h>

class Ros2BackendFoxy : public Ros2Backend
{
public:
    Ros2BackendFoxy(std::string pkgName, std::string msgSubfolder, std::string msgName);
    void set_timestamp(const int64_t nanoseconds, builtin_interfaces__msg__Time& time);
    void set_string(const std::string& input, rosidl_runtime_c__String& output);
    void set_header(const std::string& frame_id, const int64_t nanoseconds, std_msgs__msg__Header& header);
};

class Ros2ClockMessageFoxy : public Ros2ClockMessage, Ros2BackendFoxy
{
public:
    Ros2ClockMessageFoxy();
    virtual ~Ros2ClockMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fill(double timestamp);
    virtual void setData(double& timeStamp);
};

class Ros2ImuMessageFoxy : public Ros2ImuMessage, Ros2BackendFoxy
{
public:
    Ros2ImuMessageFoxy();
    virtual ~Ros2ImuMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(double timestamp, std::string& frame_id);
    virtual void fillAccel(bool covariance, const std::vector<double>& accel);
    virtual void fillVelo(bool covariance, const std::vector<double>& velo);
    virtual void fillOrient(bool covariance, const std::vector<double>& orient);
};

class Ros2CameraInfoMessageFoxy : public Ros2CameraInfoMessage, Ros2BackendFoxy
{
public:
    Ros2CameraInfoMessageFoxy();
    virtual ~Ros2CameraInfoMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillHeightWidth(const uint32_t height, const uint32_t width);
    virtual void fillIntrisicArray(const double k_arr[], const int numElem);
    virtual void fillProjectionArray(const double p_arr[], const int numElem);
    virtual void fillRectificationArray(const double r_arr[], const int numElem);
    virtual void fillDistortionModel(std::vector<double>& distort_array, const std::string& distort_model);
};

class Ros2ImageMessageFoxy : public Ros2ImageMessage, Ros2BackendFoxy
{
public:
    Ros2ImageMessageFoxy();
    virtual ~Ros2ImageMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding);
};

class Ros2BoundingBox2DMessageFoxy : public Ros2BoundingBox2DMessage, Ros2BackendFoxy
{
public:
    Ros2BoundingBox2DMessageFoxy();
    virtual ~Ros2BoundingBox2DMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2BoundingBox3DMessageFoxy : public Ros2BoundingBox3DMessage, Ros2BackendFoxy
{
public:
    Ros2BoundingBox3DMessageFoxy();
    virtual ~Ros2BoundingBox3DMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes);
};

class Ros2OdomMessageFoxy : public Ros2OdomMessage, Ros2BackendFoxy
{
public:
    Ros2OdomMessageFoxy();
    virtual ~Ros2OdomMessageFoxy();
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

class Ros2RawTfTreeMessageFoxy : public Ros2RawTfTreeMessage, Ros2BackendFoxy
{
public:
    Ros2RawTfTreeMessageFoxy();
    virtual ~Ros2RawTfTreeMessageFoxy();
    virtual const void* getTypeSupportHandle();
    // virtual void fillHeader(const double timestamp, const std::string& frame_id);
    virtual void fillData(const double timestamp,
                          const std::string& headerFrame,
                          const std::string& childFrame,
                          const pxr::GfVec3d& translation,
                          const pxr::GfQuatd& rotation);
};

class Ros2SemanticLabelMessageFoxy : public Ros2SemanticLabelMessage, Ros2BackendFoxy
{
public:
    Ros2SemanticLabelMessageFoxy();
    virtual ~Ros2SemanticLabelMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const std::string& data);
};

class Ros2JointStateMessageFoxy : public Ros2JointStateMessage, Ros2BackendFoxy
{
public:
    Ros2JointStateMessageFoxy();
    virtual ~Ros2JointStateMessageFoxy();
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


class Ros2PointCloudMessageFoxy : public Ros2PointCloudMessage, Ros2BackendFoxy
{
public:
    Ros2PointCloudMessageFoxy();
    virtual ~Ros2PointCloudMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillMetadata(const std::string& frameId,
                              const double& timeStamp,
                              const size_t& width,
                              const size_t& height,
                              const uint32_t& point_step);
};


class Ros2LaserScanMessageFoxy : public Ros2LaserScanMessage, Ros2BackendFoxy
{
public:
    Ros2LaserScanMessageFoxy();
    virtual ~Ros2LaserScanMessageFoxy();
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


class Ros2TfTreeMessageFoxy : public Ros2TfTreeMessage, Ros2BackendFoxy
{
public:
    Ros2TfTreeMessageFoxy();
    virtual ~Ros2TfTreeMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void fillData(const double& timeStamp, std::vector<tfMessageStruct>& tfMsg_vec);
};


class Ros2TwistMessageFoxy : public Ros2TwistMessage, Ros2BackendFoxy
{
public:
    Ros2TwistMessageFoxy();
    virtual ~Ros2TwistMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void getData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity);
};

class Ros2AckermannDriveStampedMessageFoxy : public Ros2AckermannDriveStampedMessage, Ros2BackendFoxy
{
public:
    Ros2AckermannDriveStampedMessageFoxy();
    virtual ~Ros2AckermannDriveStampedMessageFoxy();
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

class Ros2HandleFoxy : public Ros2HandleBase
{
public:
    virtual ~Ros2HandleFoxy()
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


class Ros2NodeFoxy : public Ros2NodeBase
{
public:
    Ros2NodeFoxy(const char* name, const char* name_space, Ros2HandleBase* rcl_handle);
    virtual ~Ros2NodeFoxy();
    virtual Ros2HandleBase* handle();
    virtual void* node();

private:
    Ros2HandleBase* mHandle;
    std::shared_ptr<rcl_node_t> mNode;
};

class Ros2PublisherFoxy : public Ros2Publisher
{
public:
    Ros2PublisherFoxy(Ros2NodeBase* node, const char* topic_name, const void* type, const size_t history_depth);
    virtual ~Ros2PublisherFoxy();
    virtual void publish(const void* msg);
    virtual size_t get_subscription_count();

private:
    Ros2NodeBase* mNode;
    std::shared_ptr<rcl_publisher_t> mPub;
};

class Ros2SubscriberFoxy : public Ros2Subscriber
{
public:
    Ros2SubscriberFoxy(Ros2NodeBase* node, const char* topic_name, const void* type, const size_t history_depth);
    virtual ~Ros2SubscriberFoxy();
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

class Ros2DynamicMessageFoxy : public Ros2DynamicMessage, Ros2BackendFoxy
{
public:
    Ros2DynamicMessageFoxy(std::string pkgName, std::string msgSubfolder, std::string msgName);
    virtual ~Ros2DynamicMessageFoxy();
    virtual const void* getTypeSupportHandle();
    virtual void getData(std::vector<std::shared_ptr<const void>>& data, bool asOgnType);

protected:
    virtual void parseMessageFields(const std::string& parentName, const void* members);
    virtual void parseMessageValues(const void* members,
                                    uint8_t* data,
                                    std::vector<std::shared_ptr<const void>>& messageValues,
                                    bool asOgnType);

private:
    template <typename ArrayType, typename RosType, typename OgnType>
    std::shared_ptr<const void> getArray(const rosidl_typesupport_introspection_c__MessageMember* member,
                                         uint8_t* data,
                                         bool asOgnType);

    template <typename RosType, typename OgnType>
    std::shared_ptr<const void> getSingleValue(uint8_t* data, bool asOgnType);

    void messageValuesToJson(const void* members,
                             uint8_t* messageData,
                             const std::shared_ptr<std::vector<std::string>> messageValues);
    void embeddedMessageArrayToJson(const rosidl_typesupport_introspection_c__MessageMember* member,
                                    uint8_t* data,
                                    const std::shared_ptr<std::vector<std::string>> messageValues);
};
