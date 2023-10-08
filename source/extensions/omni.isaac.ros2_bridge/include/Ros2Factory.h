// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/dynamic_control/DynamicControl.h>
// #include <omni/isaac/utils/LibraryLoader.h>
#include <omni/isaac/utils/Math.h>

#include <memory>
#include <string>
#include <vector>

// #include <omni/isaac/ros/Conversions.h>
// #include <omni/isaac/utils/PoseTree.h>
// #include <omni/fabric/FabricUSD.h>
// #include <omni/usd/UsdUtils.h>

class Ros2Message
{
public:
    void* ptr()
    {
        return msg;
    }
    virtual const void* getTypeSupportHandle() = 0;

protected:
    void* msg = nullptr;
};

class Ros2HandleBase
{
public:
    virtual void* context() = 0;
    virtual void init(int argc, char const* const* argv, bool setDomainId = false, size_t domainId = 0) = 0;
    virtual bool is_valid() = 0;
    virtual bool shutdown(const char* shutdown_reason = nullptr) = 0;
};

class Ros2NodeBase
{
public:
    virtual Ros2HandleBase* handle() = 0;
    virtual void* node() = 0;
};

class Ros2Publisher
{
public:
    virtual void publish(const void* msg) = 0;
};


class Ros2Subscriber
{
public:
    virtual bool spin(void* msg) = 0;
};

class Ros2Backend
{
};


class Ros2ClockMessage : public Ros2Message
{
public:
    virtual void fill(double timestamp) = 0;
    virtual void setData(double& timestamp) = 0;
};


class Ros2ImuMessage : public Ros2Message
{
public:
    // Consider using fixed size std::array instead of vectors
    virtual void fillHeader(double timestamp, std::string& frame_id) = 0;
    virtual void fillAccel(bool covariance = false, const std::vector<double>& accel = std::vector<double>()) = 0;
    virtual void fillVelo(bool covariance = false, const std::vector<double>& velo = std::vector<double>()) = 0;
    virtual void fillOrient(bool covariance = false, const std::vector<double>& orient = std::vector<double>()) = 0;
};


class Ros2CameraInfoMessage : public Ros2Message
{
public:
    virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void fillHeightWidthDistortion(const uint32_t height,
                                           const uint32_t width,
                                           const std::string& distort_model) = 0;
    virtual void fillIntrisicArray(const double k_arr[], const int numElem) = 0;
    virtual void fillProjectionArray(const double p_arr[], const int numElem) = 0;
};

class Ros2ImageMessage : public Ros2Message
{
public:
    virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding) = 0;

    void* getDataPtr()
    {
        return &data[0];
    }
    size_t getTotalBytes()
    {
        return totalBytes;
    }

protected:
    std::vector<uint8_t> data;
    size_t totalBytes = 0;
};

class Ros2BoundingBox2DMessage : public Ros2Message
{
public:
    virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes) = 0;
};

class Ros2BoundingBox3DMessage : public Ros2Message
{
public:
    virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void fillBboxData(const void* bboxArray, size_t numBoxes) = 0;
};

class Ros2JointStateMessage : public Ros2Message
{
public:
    virtual void fillData(const double& timeStamp,
                          omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr,
                          omni::isaac::dynamic_control::DcHandle mArticulationHandle,
                          pxr::UsdStageWeakPtr mStage,
                          std::vector<omni::isaac::dynamic_control::DcDofProperties>& mDofProps,
                          std::vector<float>& mPrevJointPosition,
                          std::vector<float>& mCalculatedJointVelocity,
                          const double& dt,
                          const double& stageUnits) = 0;

    virtual void getData(std::vector<char*>& jointNames,
                         double* positionCommand,
                         double* velocityCommand,
                         double* effortCommand,
                         double& timeStamp) = 0;

    virtual void getActuators(size_t& actuators) = 0;

    virtual bool checkValid() = 0;
};

class Ros2LaserScanMessage : public Ros2Message
{
public:
    virtual void fillData(const std::string& frameId,
                          const double& timeStamp,
                          const pxr::GfVec2f& azimuthRange,
                          const float& rotationRate,
                          const pxr::GfVec2f& depthRange,
                          size_t buffSize,
                          float* rangeData,
                          float* intensitiesData,
                          float horizontalResolution,
                          float horizontalFov) = 0;
};

class Ros2OdomMessage : public Ros2Message
{
public:
    virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void fillData(std::string& childFrame,
                          const pxr::GfVec3d& linVel,
                          const pxr::GfVec3d& angVel,
                          const pxr::GfVec3f& mRobotFront,
                          const pxr::GfVec3f& mRobotSide,
                          double mUnitScale,
                          bool mZUp,
                          const pxr::GfVec3d& position,
                          const pxr::GfQuatd& orientation) = 0;
};

class Ros2PointCloudMessage : public Ros2Message
{
public:
    virtual void fillMetadata(const std::string& frameId,
                              const double& timeStamp,
                              const size_t& width,
                              const size_t& height,
                              const uint32_t& point_step) = 0;
    void* getDataPtr()
    {
        return &data[0];
    }
    size_t getTotalBytes()
    {
        return totalBytes;
    }

protected:
    std::vector<uint8_t> data;
    size_t totalBytes = 0;
};

class Ros2RawTfTreeMessage : public Ros2Message
{
public:
    // virtual void fillHeader(const double timestamp, const std::string& frame_id) = 0;
    virtual void fillData(const double timestamp,
                          const std::string& headerFrame,
                          const std::string& childFrame,
                          const pxr::GfVec3d& translation,
                          const pxr::GfQuatd& rotation) = 0;
};

class Ros2SemanticLabelMessage : public Ros2Message
{
public:
    virtual void fillData(const std::string& data) = 0;
};

class Ros2TwistMessage : public Ros2Message
{
public:
    virtual void getData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity) = 0;
};


struct tfMessageStruct
{
    double timeStamp;
    std::string parentFrame;
    std::string childFrame;

    // translation components
    double trans_x;
    double trans_y;
    double trans_z;

    // quarternion components
    double quat_x;
    double quat_y;
    double quat_z;
    double quat_w;
};

class Ros2TfTreeMessage : public Ros2Message
{
public:
    virtual void fillData(const double& timeStamp, std::vector<tfMessageStruct>& tfMsg_vec) = 0;
};


class Ros2Factory
{
public:
    // virtual void* GetTypeSupportHandle(const char* pkgName, const char* msgSubfolder, const char* msgName);
    virtual std::shared_ptr<Ros2HandleBase> CreateHandle() = 0;
    virtual std::shared_ptr<Ros2NodeBase> CreateNode(const char* name, const char* name_space, Ros2HandleBase* handle) = 0;
    virtual std::shared_ptr<Ros2Publisher> CreatePublisher(Ros2NodeBase* node,
                                                           const char* topic_name,
                                                           const void* type,
                                                           const size_t history_depth) = 0;
    virtual std::shared_ptr<Ros2Subscriber> CreateSubscriber(Ros2NodeBase* node,
                                                             const char* topic_name,
                                                             const void* type) = 0;
    virtual std::shared_ptr<Ros2ClockMessage> CreateClockMessage() = 0;

    virtual std::shared_ptr<Ros2ImuMessage> CreateImuMessage() = 0;

    virtual std::shared_ptr<Ros2CameraInfoMessage> CreateCameraInfoMessage() = 0;

    virtual std::shared_ptr<Ros2ImageMessage> CreateImageMessage() = 0;

    virtual std::shared_ptr<Ros2BoundingBox2DMessage> CreateBoundingBox2DMessage() = 0;

    virtual std::shared_ptr<Ros2BoundingBox3DMessage> CreateBoundingBox3DMessage() = 0;

    virtual std::shared_ptr<Ros2OdomMessage> CreateOdomMessage() = 0;

    virtual std::shared_ptr<Ros2RawTfTreeMessage> CreateRawTfTreeMessage() = 0;

    virtual std::shared_ptr<Ros2SemanticLabelMessage> CreateSemanticLabelMessage() = 0;

    virtual std::shared_ptr<Ros2JointStateMessage> CreateJointStateMessage() = 0;

    virtual std::shared_ptr<Ros2PointCloudMessage> CreatePointCloudMessage() = 0;

    virtual std::shared_ptr<Ros2LaserScanMessage> CreateLaserScanMessage() = 0;

    virtual std::shared_ptr<Ros2TfTreeMessage> CreateTfTreeMessage() = 0;

    virtual std::shared_ptr<Ros2TwistMessage> CreateTwistMessage() = 0;

    virtual bool validateTopic(const std::string& topicName) = 0;
    virtual bool validateNodeNamespace(const std::string& nodeNamespace) = 0;
    virtual bool validateNodeName(const std::string& nodeName) = 0;
    // protected:
    // omni::isaac::utils::MultiLibraryLoader mTypesupportLibraries;
};
