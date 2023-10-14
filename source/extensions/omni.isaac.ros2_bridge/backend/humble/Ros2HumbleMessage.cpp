// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "Ros2Humble.h"
#include "pxr/usd/usdPhysics/joint.h"
#include "sensor_msgs/image_encodings.hpp"

#include <carb/logging/Log.h>

#include <rcl/rcl.h>
#include <sensor_msgs/msg/camera_info.h>


// Clock message
Ros2ClockMessageHumble::Ros2ClockMessageHumble()
{
    msg = rosgraph_msgs__msg__Clock__create();
}
Ros2ClockMessageHumble::~Ros2ClockMessageHumble()
{
    if (!msg)
    {
        return;
    }
    rosgraph_msgs__msg__Clock__destroy(static_cast<rosgraph_msgs__msg__Clock*>(msg));
}
const void* Ros2ClockMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(rosgraph_msgs, msg, Clock);
}

void Ros2ClockMessageHumble::fill(double timestamp)
{
    if (!msg)
    {
        return;
    }
    rosgraph_msgs__msg__Clock* time_msg = static_cast<rosgraph_msgs__msg__Clock*>(msg);
    Ros2BackendHumble::set_timestamp(static_cast<int64_t>(timestamp * 1e9), time_msg->clock);
}

void Ros2ClockMessageHumble::setData(double& timeStamp)
{
    if (!msg)
    {
        return;
    }

    rosgraph_msgs__msg__Clock* time_msg = static_cast<rosgraph_msgs__msg__Clock*>(msg);
    timeStamp = time_msg->clock.sec + time_msg->clock.nanosec / 1e9;
}


// IMU message
Ros2ImuMessageHumble::Ros2ImuMessageHumble()
{
    msg = sensor_msgs__msg__Imu__create();
}

const void* Ros2ImuMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu);
}

void Ros2ImuMessageHumble::fillHeader(double timestamp, std::string& frame_id)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__Imu* imu_msg = static_cast<sensor_msgs__msg__Imu*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), imu_msg->header);
}

void Ros2ImuMessageHumble::fillAccel(bool covariance = false, const std::vector<double>& accel = std::vector<double>())
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__Imu* imu_msg = static_cast<sensor_msgs__msg__Imu*>(msg);

    if (covariance)
    {
        imu_msg->linear_acceleration_covariance[0] = -1;
    }
    else
    {
        imu_msg->linear_acceleration.x = accel[0];
        imu_msg->linear_acceleration.y = accel[1];
        imu_msg->linear_acceleration.z = accel[2];
    }
}

void Ros2ImuMessageHumble::fillVelo(bool covariance = false, const std::vector<double>& vel = std::vector<double>())
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__Imu* imu_msg = static_cast<sensor_msgs__msg__Imu*>(msg);

    if (covariance)
    {
        imu_msg->angular_velocity_covariance[0] = -1;
    }
    else
    {
        imu_msg->angular_velocity.x = vel[0];
        imu_msg->angular_velocity.y = vel[1];
        imu_msg->angular_velocity.z = vel[2];
    }
}

void Ros2ImuMessageHumble::fillOrient(bool covariance = false, const std::vector<double>& orient = std::vector<double>())
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__Imu* imu_msg = static_cast<sensor_msgs__msg__Imu*>(msg);

    if (covariance)
    {
        imu_msg->orientation_covariance[0] = -1;
    }
    else
    {
        imu_msg->orientation.x = orient[0];
        imu_msg->orientation.y = orient[1];
        imu_msg->orientation.z = orient[2];
        imu_msg->orientation.w = orient[3];
    }
}

Ros2ImuMessageHumble::~Ros2ImuMessageHumble()
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__Imu__destroy(static_cast<sensor_msgs__msg__Imu*>(msg));
}


// Camera Info Message
Ros2CameraInfoMessageHumble::Ros2CameraInfoMessageHumble()
{
    msg = sensor_msgs__msg__CameraInfo__create();
}

const void* Ros2CameraInfoMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, CameraInfo);
}

void Ros2CameraInfoMessageHumble::fillHeader(const double timestamp, const std::string& frame_id)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), camInfo_msg->header);
}

void Ros2CameraInfoMessageHumble::fillHeightWidth(const uint32_t height, const uint32_t width)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);

    camInfo_msg->height = height;
    camInfo_msg->width = width;
}

void Ros2CameraInfoMessageHumble::fillIntrisicArray(const double k_arr[], const int numElem)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);
    memcpy(camInfo_msg->k, k_arr, numElem * sizeof(double));
}

void Ros2CameraInfoMessageHumble::fillDistortionModel(std::vector<double>& distort_array, const std::string& distort_model)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);
    if (distort_array.size() > 0)
    {
        camInfo_msg->d.data = (double*)malloc(distort_array.size() * sizeof(double));

        camInfo_msg->d.size = distort_array.size();
        camInfo_msg->d.capacity = distort_array.size();
        memcpy(camInfo_msg->d.data, distort_array.data(), distort_array.size() * sizeof(double));
    }
    Ros2BackendHumble::set_string(distort_model, camInfo_msg->distortion_model);
}

void Ros2CameraInfoMessageHumble::fillProjectionArray(const double p_arr[], const int numElem)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);
    memcpy(camInfo_msg->p, p_arr, numElem * sizeof(double));
}

void Ros2CameraInfoMessageHumble::fillRectificationArray(const double r_arr[], const int numElem)
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo* camInfo_msg = static_cast<sensor_msgs__msg__CameraInfo*>(msg);
    memcpy(camInfo_msg->r, r_arr, numElem * sizeof(double));
}


Ros2CameraInfoMessageHumble::~Ros2CameraInfoMessageHumble()
{
    if (!msg)
    {
        return;
    }

    sensor_msgs__msg__CameraInfo__destroy(static_cast<sensor_msgs__msg__CameraInfo*>(msg));
}


// Image message
Ros2ImageMessageHumble::Ros2ImageMessageHumble()
{
    msg = sensor_msgs__msg__Image__create();
}


const void* Ros2ImageMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Image);
}
void Ros2ImageMessageHumble::fillHeader(const double timestamp, const std::string& frame_id)
{
    if (!msg)
        return;

    sensor_msgs__msg__Image* img_msg = static_cast<sensor_msgs__msg__Image*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), img_msg->header);
}


void Ros2ImageMessageHumble::generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding)
{
    if (!msg)
        return;

    sensor_msgs__msg__Image* img_msg = static_cast<sensor_msgs__msg__Image*>(msg);
    img_msg->height = height;
    img_msg->width = width;
    Ros2BackendHumble::set_string(encoding, img_msg->encoding);

    int channels = 0;
    int bitDepth = 0;
    try
    {
        channels = sensor_msgs::image_encodings::numChannels(encoding);
        bitDepth = sensor_msgs::image_encodings::bitDepth(encoding);
    }
    catch (std::exception& e)
    {
        CARB_LOG_ERROR("%s", e.what());
        return;
    }
    int byteDepth = bitDepth / 8;

    uint32_t step = width * channels * byteDepth;
    img_msg->step = step;
    totalBytes = step * height;
    data.resize(totalBytes);
    img_msg->data.size = totalBytes;
    img_msg->data.capacity = totalBytes;
    img_msg->data.data = &data[0];
}

Ros2ImageMessageHumble::~Ros2ImageMessageHumble()
{
    if (!msg)
        return;
    sensor_msgs__msg__Image* img_msg = static_cast<sensor_msgs__msg__Image*>(msg);
    // Lifetime of memory is not managed by the message as we use a std vector
    img_msg->data.size = 0;
    img_msg->data.capacity = 0;
    img_msg->data.data = nullptr;
    sensor_msgs__msg__Image__destroy(img_msg);
}


// 2D bounding box detection message array
struct Bbox2DData
{
    uint32_t semanticId;
    int32_t x_min;
    int32_t y_min;
    int32_t x_max;
    int32_t y_max;
    float occlusionRatio;
};

Ros2BoundingBox2DMessageHumble::Ros2BoundingBox2DMessageHumble()
{
    msg = vision_msgs__msg__Detection2DArray__create();
}

const void* Ros2BoundingBox2DMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(vision_msgs, msg, Detection2DArray);
}

void Ros2BoundingBox2DMessageHumble::fillHeader(const double timestamp, const std::string& frame_id)
{
    if (!msg)
        return;

    vision_msgs__msg__Detection2DArray* detection_msg = static_cast<vision_msgs__msg__Detection2DArray*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), detection_msg->header);
}

void Ros2BoundingBox2DMessageHumble::fillBboxData(const void* bboxArray, const size_t numBoxes)
{
    if (!msg)
        return;

    vision_msgs__msg__Detection2DArray* detection_msg = static_cast<vision_msgs__msg__Detection2DArray*>(msg);

    // Set the detection sequence size and object pose sequence size
    vision_msgs__msg__Detection2D__Sequence__init(&detection_msg->detections, numBoxes);


    const Bbox2DData* bboxData = reinterpret_cast<const Bbox2DData*>(bboxArray);

    for (size_t i = 0; i < numBoxes; i++)
    {
        const Bbox2DData& box = bboxData[i];

        detection_msg->detections.data[i].bbox.center.theta = 0;
        detection_msg->detections.data[i].bbox.center.position.x = (box.x_max + box.x_min) / 2.0;
        detection_msg->detections.data[i].bbox.center.position.y = (box.y_max + box.y_min) / 2.0;
        detection_msg->detections.data[i].bbox.size_x = box.x_max - box.x_min;
        detection_msg->detections.data[i].bbox.size_y = box.y_max - box.y_min;
        // TODO: Detection sub message header for all detections
        // detection_msg->detections.data[i].header

        vision_msgs__msg__ObjectHypothesisWithPose__Sequence__init(&detection_msg->detections.data[i].results, 1);

        detection_msg->detections.data[i].results.data[0].hypothesis.score = 1.0;
        Ros2BackendHumble::set_string(
            std::to_string(box.semanticId), detection_msg->detections.data[i].results.data[0].hypothesis.class_id);
    }
}

Ros2BoundingBox2DMessageHumble::~Ros2BoundingBox2DMessageHumble()
{
    if (!msg)
        return;

    vision_msgs__msg__Detection2DArray__destroy(static_cast<vision_msgs__msg__Detection2DArray*>(msg));
}

struct Bbox3DData
{
    uint32_t semanticId;
    float x_min;
    float y_min;
    float z_min;
    float x_max;
    float y_max;
    float z_max;
    pxr::GfMatrix4f transform;
    float occlusionRatio;
};

// 3D Detection array
Ros2BoundingBox3DMessageHumble::Ros2BoundingBox3DMessageHumble()
{
    msg = vision_msgs__msg__Detection3DArray__create();
}

const void* Ros2BoundingBox3DMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(vision_msgs, msg, Detection3DArray);
}

void Ros2BoundingBox3DMessageHumble::fillHeader(const double timestamp, const std::string& frame_id)
{
    if (!msg)
        return;

    vision_msgs__msg__Detection3DArray* detection_msg = static_cast<vision_msgs__msg__Detection3DArray*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), detection_msg->header);
}

void Ros2BoundingBox3DMessageHumble::fillBboxData(const void* bboxArray, size_t numBoxes)
{
    if (!msg)
        return;


    vision_msgs__msg__Detection3DArray* detection_msg = static_cast<vision_msgs__msg__Detection3DArray*>(msg);

    vision_msgs__msg__Detection3D__Sequence__init(&detection_msg->detections, numBoxes);

    const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(bboxArray);

    for (size_t i = 0; i < numBoxes; i++)
    {
        const Bbox3DData& box = bboxData[i];
        auto mat = pxr::GfMatrix4d(box.transform);
        auto transform = pxr::GfTransform(mat);

        auto trans = transform.GetTranslation();
        auto rot = transform.GetRotation().GetQuaternion();
        auto scale = transform.GetScale();

        // TODO: Detection sub message header for all detections
        // detection_msg->detections.data[i].header

        detection_msg->detections.data[i].bbox.center.position.x = trans[0];
        detection_msg->detections.data[i].bbox.center.position.y = trans[1];
        detection_msg->detections.data[i].bbox.center.position.z = trans[2];

        auto imag = rot.GetImaginary();

        detection_msg->detections.data[i].bbox.center.orientation.x = imag[0];
        detection_msg->detections.data[i].bbox.center.orientation.y = imag[1];
        detection_msg->detections.data[i].bbox.center.orientation.z = imag[2];
        detection_msg->detections.data[i].bbox.center.orientation.w = rot.GetReal();

        detection_msg->detections.data[i].bbox.size.x = (box.x_max - box.x_min) * scale[0];
        detection_msg->detections.data[i].bbox.size.y = (box.x_max - box.x_min) * scale[1];
        detection_msg->detections.data[i].bbox.size.z = (box.x_max - box.x_min) * scale[2];

        vision_msgs__msg__ObjectHypothesisWithPose__Sequence__init(&detection_msg->detections.data[i].results, 1);

        detection_msg->detections.data[i].results.data[0].hypothesis.score = 1.0;
        Ros2BackendHumble::set_string(
            std::to_string(box.semanticId), detection_msg->detections.data[i].results.data[0].hypothesis.class_id);
    }
}

Ros2BoundingBox3DMessageHumble::~Ros2BoundingBox3DMessageHumble()
{
    if (!msg)
        return;

    vision_msgs__msg__Detection3DArray__destroy(static_cast<vision_msgs__msg__Detection3DArray*>(msg));
}


// Odom message implementations
Ros2OdomMessageHumble::Ros2OdomMessageHumble()
{
    msg = nav_msgs__msg__Odometry__create();
}
const void* Ros2OdomMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry);
}
void Ros2OdomMessageHumble::fillHeader(const double timestamp, const std::string& frame_id)
{
    if (!msg)
        return;

    nav_msgs__msg__Odometry* odom_msg = static_cast<nav_msgs__msg__Odometry*>(msg);
    Ros2BackendHumble::set_header(frame_id, static_cast<int64_t>(timestamp * 1e9), odom_msg->header);
}

void Ros2OdomMessageHumble::fillData(std::string& childFrame,
                                     const pxr::GfVec3d& linVel,
                                     const pxr::GfVec3d& angVel,
                                     const pxr::GfVec3f& mRobotFront,
                                     const pxr::GfVec3f& mRobotSide,
                                     double mUnitScale,
                                     bool mZUp,
                                     const pxr::GfVec3d& position,
                                     const pxr::GfQuatd& orientation)
{
    if (!msg)
        return;

    nav_msgs__msg__Odometry* odom_msg = static_cast<nav_msgs__msg__Odometry*>(msg);
    Ros2BackendHumble::set_string(childFrame, odom_msg->child_frame_id);

    float measuredSpeedFront =
        static_cast<float>(pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), mRobotFront) * mUnitScale);

    float measuredSpeedSide =
        static_cast<float>(pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), mRobotSide) * mUnitScale);

    odom_msg->twist.twist.linear.x = measuredSpeedFront;
    odom_msg->twist.twist.linear.y = measuredSpeedSide;

    if (mZUp)
    {
        odom_msg->twist.twist.angular.z = angVel[2]; // Get Z component of angular velocity
    }
    else
    {
        odom_msg->twist.twist.angular.y = angVel[1]; // Get Y component of angular velocity
    }

    odom_msg->pose.pose.position.x = position[0];
    odom_msg->pose.pose.position.y = position[1];
    odom_msg->pose.pose.position.z = position[2];

    odom_msg->pose.pose.orientation.x = orientation.GetImaginary()[0];
    odom_msg->pose.pose.orientation.y = orientation.GetImaginary()[1];
    odom_msg->pose.pose.orientation.z = orientation.GetImaginary()[2];
    odom_msg->pose.pose.orientation.w = orientation.GetReal();
}

Ros2OdomMessageHumble::~Ros2OdomMessageHumble()
{
    if (!msg)
        return;

    nav_msgs__msg__Odometry__destroy(static_cast<nav_msgs__msg__Odometry*>(msg));
}


// Raw Tf tree message
Ros2RawTfTreeMessageHumble::Ros2RawTfTreeMessageHumble()
{
    msg = tf2_msgs__msg__TFMessage__create();
}
const void* Ros2RawTfTreeMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(tf2_msgs, msg, TFMessage);
}
void Ros2RawTfTreeMessageHumble::fillData(const double timestamp,
                                          const std::string& headerFrame,
                                          const std::string& childFrame,
                                          const pxr::GfVec3d& translation,
                                          const pxr::GfQuatd& rotation)
{
    if (!msg)
        return;

    tf2_msgs__msg__TFMessage* tf_msg = static_cast<tf2_msgs__msg__TFMessage*>(msg);

    geometry_msgs__msg__TransformStamped__Sequence__init(&tf_msg->transforms, 1);

    Ros2BackendHumble::set_header(headerFrame, static_cast<int64_t>(timestamp * 1e9), tf_msg->transforms.data->header);
    Ros2BackendHumble::set_string(childFrame, tf_msg->transforms.data->child_frame_id);

    tf_msg->transforms.data->transform.translation.x = translation[0];
    tf_msg->transforms.data->transform.translation.y = translation[1];
    tf_msg->transforms.data->transform.translation.z = translation[2];

    tf_msg->transforms.data->transform.rotation.x = rotation.GetImaginary()[0];
    tf_msg->transforms.data->transform.rotation.y = rotation.GetImaginary()[1];
    tf_msg->transforms.data->transform.rotation.z = rotation.GetImaginary()[2];
    tf_msg->transforms.data->transform.rotation.w = rotation.GetReal();
}

Ros2RawTfTreeMessageHumble::~Ros2RawTfTreeMessageHumble()
{
    tf2_msgs__msg__TFMessage__destroy(static_cast<tf2_msgs__msg__TFMessage*>(msg));
}


// Sematic label (string type message)

Ros2SemanticLabelMessageHumble::Ros2SemanticLabelMessageHumble()
{
    msg = std_msgs__msg__String__create();
}
const void* Ros2SemanticLabelMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, String);
}

void Ros2SemanticLabelMessageHumble::fillData(const std::string& data)
{
    if (!msg)
        return;

    std_msgs__msg__String* string_msg = static_cast<std_msgs__msg__String*>(msg);

    Ros2BackendHumble::set_string(data, string_msg->data);
}

Ros2SemanticLabelMessageHumble::~Ros2SemanticLabelMessageHumble()
{
    std_msgs__msg__String__destroy(static_cast<std_msgs__msg__String*>(msg));
}


// Joint state
Ros2JointStateMessageHumble::Ros2JointStateMessageHumble()
{
    msg = sensor_msgs__msg__JointState__create();
}
const void* Ros2JointStateMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, JointState);
}

// omni::isaac::dynamic_control::DcDofState* mStates
void Ros2JointStateMessageHumble::fillData(const double& timeStamp,
                                           omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr,
                                           omni::isaac::dynamic_control::DcHandle mArticulationHandle,
                                           pxr::UsdStageWeakPtr mStage,
                                           std::vector<omni::isaac::dynamic_control::DcDofProperties>& mDofProps,
                                           std::vector<float>& mPrevJointPosition,
                                           std::vector<float>& mCalculatedJointVelocity,
                                           const double& dt,
                                           const double& stageUnits)
{
    if (!msg)
        return;

    sensor_msgs__msg__JointState* jointState_msg = static_cast<sensor_msgs__msg__JointState*>(msg);

    omni::isaac::dynamic_control::DcDofState* mStates = nullptr;

    Ros2BackendHumble::set_header("", static_cast<int64_t>(timeStamp * 1e9), jointState_msg->header);

    mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
    size_t num_dofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);
    mDofProps.resize(num_dofs);
    mDynamicControlPtr->getArticulationDofProperties(mArticulationHandle, mDofProps.data());
    mStates =
        mDynamicControlPtr->getArticulationDofStates(mArticulationHandle, omni::isaac::dynamic_control::kDcStateAll);

    mPrevJointPosition.resize(num_dofs);
    mCalculatedJointVelocity.resize(num_dofs);

    rosidl_runtime_c__String__Sequence__init(&jointState_msg->name, num_dofs);
    rosidl_runtime_c__double__Sequence__init(&jointState_msg->position, num_dofs);
    rosidl_runtime_c__double__Sequence__init(&jointState_msg->velocity, num_dofs);
    rosidl_runtime_c__double__Sequence__init(&jointState_msg->effort, num_dofs);

    if (mStates != nullptr)
    {
        for (size_t j = 0; j < num_dofs; j++)
        {
            // calculate velocity
            mCalculatedJointVelocity[j] = static_cast<float>((mStates[j].pos - mPrevJointPosition[j]) / dt);
            mPrevJointPosition[j] = mStates[j].pos;

            omni::isaac::dynamic_control::DcHandle dof = mDynamicControlPtr->getArticulationDof(mArticulationHandle, j);
            int signCheck = 1;

            if (dof)
            {
                Ros2BackendHumble::set_string(mDynamicControlPtr->getDofName(dof), jointState_msg->name.data[j]);

                const char* mParentName = mDynamicControlPtr->getRigidBodyName(mDynamicControlPtr->getDofParentBody(dof));
                const char* jointPath = mDynamicControlPtr->getDofPath(dof);
                pxr::SdfPathVector targets;
                pxr::UsdPhysicsJoint joint = pxr::UsdPhysicsJoint::Get(mStage, pxr::SdfPath(jointPath));
                joint.GetBody0Rel().GetTargets(&targets);
                const char* body0Name = targets.at(0).GetName().c_str();
                signCheck = (strcmp(mParentName, body0Name) == 0) ? 1 : -1;
            }
            if (mDofProps[j].type == omni::isaac::dynamic_control::DcDofType::eTranslation)
            {
                jointState_msg->position.data[j] =
                    omni::isaac::utils::math::roundNearest(mStates[j].pos * stageUnits * signCheck, 10000.0); // m

                jointState_msg->velocity.data[j] = omni::isaac::utils::math::roundNearest(
                    mCalculatedJointVelocity[j] * stageUnits * signCheck, 10000.0); // m/s

                jointState_msg->effort.data[j] =
                    omni::isaac::utils::math::roundNearest(mStates[j].effort * stageUnits * signCheck, 10000.0); // N
            }
            else
            {
                jointState_msg->position.data[j] =
                    omni::isaac::utils::math::roundNearest(mStates[j].pos * signCheck, 10000.0); // rad

                jointState_msg->velocity.data[j] =
                    omni::isaac::utils::math::roundNearest(mCalculatedJointVelocity[j] * signCheck, 10000.0); // rad/s

                jointState_msg->effort.data[j] = omni::isaac::utils::math::roundNearest(
                    mStates[j].effort * stageUnits * stageUnits * signCheck, 10000.0); // N*m
            }
        }
    }
}

void Ros2JointStateMessageHumble::getActuators(size_t& actuators)
{
    if (!msg)
        return;

    sensor_msgs__msg__JointState* jointState_msg = static_cast<sensor_msgs__msg__JointState*>(msg);

    actuators = jointState_msg->name.size;
}

bool Ros2JointStateMessageHumble::checkValid()
{
    if (!msg)
        return false;

    sensor_msgs__msg__JointState* jointState_msg = static_cast<sensor_msgs__msg__JointState*>(msg);

    const size_t num_actuators = jointState_msg->name.size;

    if (jointState_msg->position.size != num_actuators && jointState_msg->velocity.size != num_actuators &&
        jointState_msg->effort.size != num_actuators)
    {
        return false;
    }
    return true;
}

void Ros2JointStateMessageHumble::getData(std::vector<char*>& jointNames,
                                          double* positionCommand,
                                          double* velocityCommand,
                                          double* effortCommand,
                                          double& timeStamp)
{
    if (!msg)
        return;

    sensor_msgs__msg__JointState* jointState_msg = static_cast<sensor_msgs__msg__JointState*>(msg);

    const size_t num_actuators = jointState_msg->name.size;

    if (num_actuators == 0)
    {
        // db.logWarning("No joints found");
        return;
    }


    jointNames.clear(); // Make sure vector is reset before filling in names
    for (size_t i = 0; i < num_actuators; i++)
    {
        char* name = jointState_msg->name.data[i].data;
        jointNames.push_back(name);
    }

    // resize for the array was called before fillData in the subscriber callback
    if (jointState_msg->position.size == num_actuators)
    {
        std::memcpy(positionCommand, jointState_msg->position.data, num_actuators * sizeof(double));
    }
    if (jointState_msg->velocity.size == num_actuators)
    {
        std::memcpy(velocityCommand, jointState_msg->velocity.data, num_actuators * sizeof(double));
    }
    if (jointState_msg->effort.size == num_actuators)
    {
        std::memcpy(effortCommand, jointState_msg->effort.data, num_actuators * sizeof(double));
    }

    timeStamp = jointState_msg->header.stamp.sec;

    return;
}


Ros2JointStateMessageHumble::~Ros2JointStateMessageHumble()
{
    if (!msg)
        return;

    sensor_msgs__msg__JointState__destroy(static_cast<sensor_msgs__msg__JointState*>(msg));
}


// point cloud 2 message
Ros2PointCloudMessageHumble::Ros2PointCloudMessageHumble()
{
    msg = sensor_msgs__msg__PointCloud2__create();
}
const void* Ros2PointCloudMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, PointCloud2);
}
void Ros2PointCloudMessageHumble::fillMetadata(const std::string& frameId,
                                               const double& timeStamp,
                                               const size_t& width,
                                               const size_t& height,
                                               const uint32_t& point_step)
{
    if (!msg)
        return;

    sensor_msgs__msg__PointCloud2* point_cloud_msg = static_cast<sensor_msgs__msg__PointCloud2*>(msg);

    point_cloud_msg->is_dense = true;
    Ros2BackendHumble::set_header(frameId, static_cast<int64_t>(timeStamp * 1e9), point_cloud_msg->header);
    point_cloud_msg->height = 1;
    point_cloud_msg->point_step = static_cast<uint32_t>(sizeof(pxr::GfVec3f));
    point_cloud_msg->width = static_cast<uint32_t>(width);

    point_cloud_msg->row_step = point_cloud_msg->point_step * point_cloud_msg->width;

    size_t totalBytes = width * sizeof(pxr::GfVec3f);
    point_cloud_msg->data.size = totalBytes;
    point_cloud_msg->data.capacity = totalBytes;
    data.resize(totalBytes);
    point_cloud_msg->data.data = &data[0];

    sensor_msgs__msg__PointField__Sequence__init(&point_cloud_msg->fields, 3);

    Ros2BackendHumble::set_string("x", point_cloud_msg->fields.data[0].name);
    Ros2BackendHumble::set_string("y", point_cloud_msg->fields.data[1].name);
    Ros2BackendHumble::set_string("z", point_cloud_msg->fields.data[2].name);

    point_cloud_msg->fields.data[0].count = 1;
    point_cloud_msg->fields.data[1].count = 1;
    point_cloud_msg->fields.data[2].count = 1;

    point_cloud_msg->fields.data[0].datatype = sensor_msgs__msg__PointField__FLOAT32;
    point_cloud_msg->fields.data[1].datatype = sensor_msgs__msg__PointField__FLOAT32;
    point_cloud_msg->fields.data[2].datatype = sensor_msgs__msg__PointField__FLOAT32;


    point_cloud_msg->fields.data[0].offset = 0;
    point_cloud_msg->fields.data[1].offset = 4;
    point_cloud_msg->fields.data[2].offset = 8;
}

Ros2PointCloudMessageHumble::~Ros2PointCloudMessageHumble()
{
    if (!msg)
        return;
    sensor_msgs__msg__PointCloud2* point_cloud_msg = static_cast<sensor_msgs__msg__PointCloud2*>(msg);
    // memory is managed by std::vector, clear this so destruction doesn't deallocate
    point_cloud_msg->data.size = 0;
    point_cloud_msg->data.capacity = 0;
    point_cloud_msg->data.data = nullptr;
    sensor_msgs__msg__PointCloud2__destroy(point_cloud_msg);
}


// Laser scan message
Ros2LaserScanMessageHumble::Ros2LaserScanMessageHumble()
{
    msg = sensor_msgs__msg__LaserScan__create();
}
const void* Ros2LaserScanMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, LaserScan);
}
void Ros2LaserScanMessageHumble::fillData(const std::string& frameId,
                                          const double& timeStamp,
                                          const pxr::GfVec2f& azimuthRange,
                                          const float& rotationRate,
                                          const pxr::GfVec2f& depthRange,
                                          size_t buffSize,
                                          float* rangeData,
                                          float* intensitiesData,
                                          float horizontalResolution,
                                          float horizontalFov)
{
    if (!msg)
        return;

    sensor_msgs__msg__LaserScan* laser_msg = static_cast<sensor_msgs__msg__LaserScan*>(msg);

    Ros2BackendHumble::set_header(frameId, static_cast<int64_t>(timeStamp * 1e9), laser_msg->header);
    laser_msg->angle_min = azimuthRange[0];
    laser_msg->angle_max = azimuthRange[1];

    laser_msg->scan_time = rotationRate ? 1.0f / rotationRate : 0.0f;
    laser_msg->range_min = depthRange[0];
    laser_msg->range_max = depthRange[1];

    laser_msg->ranges.size = buffSize;
    laser_msg->ranges.capacity = buffSize;
    laser_msg->ranges.data = rangeData;

    laser_msg->intensities.size = buffSize;
    laser_msg->intensities.capacity = buffSize;
    laser_msg->intensities.data = intensitiesData;

    laser_msg->angle_increment = static_cast<float>(horizontalResolution * M_PI / 180.0f);
    laser_msg->time_increment = (horizontalFov / 360.0f * laser_msg->scan_time) / laser_msg->ranges.size;
}

Ros2LaserScanMessageHumble::~Ros2LaserScanMessageHumble()
{
    if (!msg)
        return;

    sensor_msgs__msg__LaserScan__destroy(static_cast<sensor_msgs__msg__LaserScan*>(msg));
}

// Full tf tree
// struct tfMessageStruct
// {
//     double timeStamp;
//     std::string parentFrame;
//     std::string childFrame;
//     geometry_msgs__msg__Transform transform;
// };

Ros2TfTreeMessageHumble::Ros2TfTreeMessageHumble()
{
    msg = tf2_msgs__msg__TFMessage__create();
    ;
}
const void* Ros2TfTreeMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(tf2_msgs, msg, TFMessage);
}
void Ros2TfTreeMessageHumble::fillData(const double& timeStamp, std::vector<tfMessageStruct>& tfMsg_vec)
{
    if (!msg)
        return;

    tf2_msgs__msg__TFMessage* tfMsg = static_cast<tf2_msgs__msg__TFMessage*>(msg);

    geometry_msgs__msg__TransformStamped__Sequence__init(&tfMsg->transforms, tfMsg_vec.size());

    for (size_t i = 0; i < tfMsg_vec.size(); i++)
    {
        // Ros2BackendHumble::set_timestamp(tfMsg_vec[i].timeStamp, tfMsg->transforms.data[i].header.stamp);
        // Ros2BackendHumble::set_string(tfMsg_vec[i].parentFrame, tfMsg->transforms.data[i].header.frame_id);
        Ros2BackendHumble::set_header(
            tfMsg_vec[i].parentFrame, static_cast<int64_t>(timeStamp * 1e9), tfMsg->transforms.data[i].header);
        Ros2BackendHumble::set_string(tfMsg_vec[i].childFrame, tfMsg->transforms.data[i].child_frame_id);

        tfMsg->transforms.data[i].transform.translation.x = tfMsg_vec[i].trans_x;
        tfMsg->transforms.data[i].transform.translation.y = tfMsg_vec[i].trans_y;
        tfMsg->transforms.data[i].transform.translation.z = tfMsg_vec[i].trans_z;

        tfMsg->transforms.data[i].transform.rotation.x = tfMsg_vec[i].quat_x;
        tfMsg->transforms.data[i].transform.rotation.y = tfMsg_vec[i].quat_y;
        tfMsg->transforms.data[i].transform.rotation.z = tfMsg_vec[i].quat_z;
        tfMsg->transforms.data[i].transform.rotation.w = tfMsg_vec[i].quat_w;
    }
}

Ros2TfTreeMessageHumble::~Ros2TfTreeMessageHumble()
{
    tf2_msgs__msg__TFMessage__destroy(static_cast<tf2_msgs__msg__TFMessage*>(msg));
}


// twist message
Ros2TwistMessageHumble::Ros2TwistMessageHumble()
{
    msg = geometry_msgs__msg__Twist__create();
}
const void* Ros2TwistMessageHumble::getTypeSupportHandle()
{
    return ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist);
}
void Ros2TwistMessageHumble::getData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity)
{
    if (!msg)
        return;

    geometry_msgs__msg__Twist* twistMsg = static_cast<geometry_msgs__msg__Twist*>(msg);

    linearVelocity[0] = twistMsg->linear.x;
    linearVelocity[1] = twistMsg->linear.y;
    linearVelocity[2] = twistMsg->linear.z;

    angularVelocity[0] = twistMsg->angular.x;
    angularVelocity[1] = twistMsg->angular.y;
    angularVelocity[2] = twistMsg->angular.z;
}

Ros2TwistMessageHumble::~Ros2TwistMessageHumble()
{
    if (!msg)
        return;

    geometry_msgs__msg__Twist__destroy(static_cast<geometry_msgs__msg__Twist*>(msg));
}
