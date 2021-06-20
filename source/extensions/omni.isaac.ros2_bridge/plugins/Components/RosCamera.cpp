// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosCamera.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/msg/clock.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_srvs/srv/empty.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/image_encodings.hpp"
#include "isaac_ros2_messages/msg/isaac_bounding_box.hpp"
#include "isaac_ros2_messages/msg/isaac_bounding_box_array.hpp"
#include "isaac_ros2_messages/msg/bounding_box3_d.hpp"
#include "isaac_ros2_messages/msg/bounding_box3_d_array.hpp"

#include <boost/algorithm/string.hpp>
#include <omni/kit/ViewportWindowUtils.h>

#include <time.h>
#include <carb/cuda/CudaRuntime.h>

#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);

RosCamera::RosCamera(utils::ViewportManager* viewportManager)
{

    mViewportManager = viewportManager;
    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    mViewportInterface = mFramework->acquireInterface<omni::kit::IViewport>();
    if (!mViewportInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::kit::IViewport interface");
        return;
    }

    mSyntheticDataInterface = mFramework->acquireInterface<omni::syntheticdata::SyntheticData>();
    if (!mSyntheticDataInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::syntheticdata::SyntheticData interface");
        return;
    }

    mSensorsInterface = mFramework->acquireInterface<carb::sensors::Sensors>();
    if (!mSensorsInterface)
    {
        CARB_LOG_ERROR("Failed to acquire carb::sensors::Sensors interface");
        return;
    }
}
RosCamera::~RosCamera()
{
    CARB_LOG_INFO("RosCamera Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCameraInfoPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mRgbPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mDepthPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mInstancePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSemanticPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLabelPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox2DPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox3DPubTopic);
    onStop();
}

void RosCamera::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}

void RosCamera::onStart()
{
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    mPrevResolution = pxr::GfVec2i(0, 0);

    onComponentChange();

    // Wait until start is called to configure viewports
    if (mDoStart)
        updateViewportSettings();
}
void RosCamera::onStop()
{
    if (mRgbSensor)
    {
        mSyntheticDataInterface->destroySensor(mRgbSensor);
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }
    if (mDepthSensor)
    {
        mSyntheticDataInterface->destroySensor(mDepthSensor);
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }
    if (mSegmentationSensor)
    {
        mSyntheticDataInterface->destroySensor(mSegmentationSensor);
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
    }
    if (mSemanticSensor)
    {
        mSyntheticDataInterface->destroySensor(mSemanticSensor);
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
    }
    if (mBoundingBox2DSensor)
    {
        mSyntheticDataInterface->destroySensor(mBoundingBox2DSensor);
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }
    if (mBoundingBox3DSensor)
    {
        mSyntheticDataInterface->destroySensor(mBoundingBox3DSensor);
        mBoundingBox3DSensor = nullptr;
        mBoundingBox3DSensorData = nullptr;
    }
}

void RosCamera::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosCamera& typedPrim = (pxr::RosBridgeSchemaRosCamera)mPrim;

    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCameraInfoPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mRgbPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mDepthPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mInstancePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSemanticPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLabelPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox2DPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox3DPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetCameraInfoPubTopicAttr(), mCameraInfoPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbPubTopicAttr(), mRgbPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthPubTopicAttr(), mDepthPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetInstancePubTopicAttr(), mInstancePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetSemanticPubTopicAttr(), mSemanticPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetLabelPubTopicAttr(), mLabelPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DPubTopicAttr(), mBoundingBox2DPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DPubTopicAttr(), mBoundingBox3DPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetFrameIdAttr(), mFrameId);

    isaac::utils::safeGetAttribute(typedPrim.GetResolutionAttr(), mResolution);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbEnabledAttr(), mEnableRgb);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthEnabledAttr(), mEnableDepth);
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationEnabledAttr(), mEnableSegmentation);
    std::string filterClassList2D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DEnabledAttr(), mEnableBoundingBox2D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DClassListAttr(), filterClassList2D);
    std::string filterClassList3D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DEnabledAttr(), mEnableBoundingBox3D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DClassListAttr(), filterClassList3D);
    isaac::utils::safeGetAttribute(typedPrim.GetStereoOffsetAttr(), mStereoOffset);


    if (mEnableRgb || mEnableDepth || mEnableSegmentation || mEnableBoundingBox2D || mEnableBoundingBox3D)
    {
        mRosNode->createPublisher<sensor_msgs::msg::CameraInfo>(
            mPrim.GetPath().GetString(), mCameraInfoPubTopic, mQueueSize, &RosCamera::cameraInfoPubCallback, this);
    }
    if (mEnableRgb)
    {
        mRosNode->createPublisher<sensor_msgs::msg::Image>(
            mPrim.GetPath().GetString(), mRgbPubTopic, mQueueSize, &RosCamera::rgbPubCallback, this);
    }
    if (mEnableDepth)
    {
        mRosNode->createPublisher<sensor_msgs::msg::Image>(
            mPrim.GetPath().GetString(), mDepthPubTopic, mQueueSize, &RosCamera::depthPubCallback, this);
    }
    if (mEnableSegmentation)
    {
        mRosNode->createPublisher<sensor_msgs::msg::Image>(
            mPrim.GetPath().GetString(), mInstancePubTopic, mQueueSize, &RosCamera::instancePubCallback, this);
        mRosNode->createPublisher<sensor_msgs::msg::Image>(
            mPrim.GetPath().GetString(), mSemanticPubTopic, mQueueSize, &RosCamera::semanticPubCallback, this);
        mRosNode->createPublisher<std_msgs::msg::String>(
            mPrim.GetPath().GetString(), mLabelPubTopic, mQueueSize, &RosCamera::labelPubCallback, this);
    }
    if (mEnableBoundingBox2D)
    {
        mRosNode->createPublisher<isaac_ros2_messages::msg::IsaacBoundingBoxArray>(
            mPrim.GetPath().GetString(), mBoundingBox2DPubTopic, mQueueSize, &RosCamera::boundingbox2dPubCallback, this);
    }
    if (mEnableBoundingBox3D)
    {
        mRosNode->createPublisher<isaac_ros2_messages::msg::BoundingBox3DArray>(
            mPrim.GetPath().GetString(), mBoundingBox3DPubTopic, mQueueSize, &RosCamera::boundingbox3dPubCallback, this);
    }

    mBoundingBox2DClassList.clear();
    if (filterClassList2D != "")
        boost::split(mBoundingBox2DClassList, filterClassList2D, [](char c) { return c == ','; });

    mBoundingBox3DClassList.clear();
    if (filterClassList3D != "")
        boost::split(mBoundingBox3DClassList, filterClassList3D, [](char c) { return c == ','; });

    mCameraPath = pxr::SdfPath("/OmniverseKit_Persp");
    pxr::SdfPathVector targets;
    typedPrim.GetCameraPrimRel().GetTargets(&targets);
    if (targets.size() > 0)
    {
        mCameraPath = targets[0];
    }
    mCameraPrim = mStage->GetPrimAtPath(mCameraPath);

    if (!mDoStart)
        updateViewportSettings();
}

void RosCamera::updateViewportSettings()
{
    std::string primPath = mPrim.GetPath().GetString();
    if (mViewportWindow != nullptr)
    {
        mViewportWindow = nullptr;
        mViewportManager->unregisterViewport(primPath);
    }
    if (mViewportWindow == nullptr)
    {

        std::string viewportWindowName = mViewportManager->getViewport();
        mViewportWindow = mViewportInterface->getViewportWindow(
            mViewportInterface->getViewportWindowInstance(viewportWindowName.c_str()));
        mViewportManager->registerViewport(viewportWindowName, primPath);
    }

    mViewportWindow->setActiveCamera(mCameraPath.GetString().c_str());
    if (mResolution[0] != 0 && mResolution[1] != 0 && mResolution != mPrevResolution)
    {
        if (mDoStart)
        {
            mViewportWindow->setTextureResolution(mResolution[0], mResolution[1]);
            mPrevResolution = mResolution;
        }
        else
            CARB_LOG_WARN("Resolution will change once you stop and start simulation");
    }

    if (mEnableRgb)
    {
        mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb, mViewportWindow);
    }
    else
    {
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }

    if (mEnableDepth)
    {

        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
    }
    else
    {
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }

    if (mEnableSegmentation)
    {
        mSemanticSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        mSegmentationSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
    }
    else
    {
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
    }

    if (mEnableBoundingBox2D)
    {
        mBoundingBox2DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
    }
    else
    {
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }

    if (mEnableBoundingBox3D)
    {
        mBoundingBox3DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
    }
    else
    {
        mBoundingBox3DSensor = nullptr;
        mBoundingBox3DSensorData = nullptr;
    }
}

void RosCamera::cameraInfoPubCallback(rclcpp::PublisherBase* pub)
{
    if (mViewportWindow == nullptr)
        return;
    const char* cameraPath = mViewportWindow->getActiveCamera();
    if (!cameraPath)
        return;

    pxr::SdfPath path(cameraPath);
    pxr::UsdPrim prim = mStage->GetPrimAtPath(path);

    pxr::UsdGeomCamera cameraPrim(prim);

    float focalLength;
    pxr::GfVec2f clipRange;
    float horizontalAperture, verticalAperture;

    cameraPrim.GetFocalLengthAttr().Get(&focalLength);
    cameraPrim.GetClippingRangeAttr().Get(&clipRange);
    cameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    cameraPrim.GetVerticalApertureAttr().Get(&verticalAperture);
    carb::sensors::SensorInfo imgInfo;
    if (mEnableRgb && mSyntheticDataInterface->isSensorInitialized(mRgbSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mRgbSensor);
    }
    else if (mEnableDepth && mSyntheticDataInterface->isSensorInitialized(mDepthSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mDepthSensor);
    }
    else if (mEnableInstance && mSyntheticDataInterface->isSensorInitialized(mInstanceSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mInstanceSensor);
    }
    else if (mEnableSegmentation && mSyntheticDataInterface->isSensorInitialized(mSegmentationSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);
    }
    else if (mEnableSemantic && mSyntheticDataInterface->isSensorInitialized(mSemanticSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mSemanticSensor);
    }
    else if (mEnableBoundingBox2D && mSyntheticDataInterface->isSensorInitialized(mBoundingBox2DSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mBoundingBox2DSensor);
    }
    else if (mEnableBoundingBox3D && mSyntheticDataInterface->isSensorInitialized(mBoundingBox3DSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mBoundingBox3DSensor);
    }
    else
    {
        return;
    }
    // We have to ignore the vertical aperture number because our pixels are square
    // Compute it directly from the image size and horizontal aperture
    verticalAperture =
        static_cast<float>(imgInfo.tex.height) / static_cast<float>(imgInfo.tex.width) * horizontalAperture;

    sensor_msgs::msg::CameraInfo cam_info_msg;
    cam_info_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        cam_info_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        cam_info_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }

    cam_info_msg.height = imgInfo.tex.height;
    cam_info_msg.width = imgInfo.tex.width;
    cam_info_msg.distortion_model = "plumb_bob";

    cam_info_msg.k = { imgInfo.tex.height * focalLength / verticalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       0,
                       imgInfo.tex.width * focalLength / horizontalAperture,
                       imgInfo.tex.width * 0.5f,
                       0,
                       0,
                       1 };
    cam_info_msg.p = { imgInfo.tex.height * focalLength / verticalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       mStereoOffset[0],
                       0,
                       imgInfo.tex.width * focalLength / horizontalAperture,
                       imgInfo.tex.width * 0.5f,
                       mStereoOffset[1],
                       0,
                       0,
                       1,
                       0 };
    cam_info_msg.d = { 0, 0, 0, 0, 0 };
    static_cast<rclcpp::Publisher<sensor_msgs::msg::CameraInfo, std::allocator<void>>*>(pub)->publish(cam_info_msg);
}

void RosCamera::rgbPubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnableRgb || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mRgbSensor || !mSyntheticDataInterface->isSensorInitialized(mRgbSensor))
    {
        mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("%s RGB Status (tick): %d", mViewportWindow->getWindowName(),
    //               mSyntheticDataInterface->isSensorInitialized(mRgbSensor));
    const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

    const int color_channels = 3;
    const size_t color_step = rgbInfo.tex.width * color_channels * sizeof(uint8_t);

    sensor_msgs::msg::Image color_msg;
    color_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        color_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        color_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }
    color_msg.width = rgbInfo.tex.width;
    color_msg.height = rgbInfo.tex.height;
    color_msg.step = color_step;
    color_msg.encoding = sensor_msgs::image_encodings::RGB8;
    color_msg.data.resize(rgbInfo.tex.height * color_step);
    uint8_t* rgb = &color_msg.data[0];
    uint8_t* rgbDevice;
    const size_t bufferSize = rgbInfo.tex.width * rgbInfo.tex.height * 3;
    CUDA_CHECK(cudaMalloc(&rgbDevice, bufferSize));
    mRgbSensorData = mSyntheticDataInterface->getSensorDeviceData(mRgbSensor);

    rgbaToRgb(rgbDevice, (uint8_t*)mRgbSensorData, rgbInfo.tex.width, rgbInfo.tex.height, rgbInfo.tex.rowSize);
    CUDA_CHECK(cudaMemcpy(rgb, rgbDevice, bufferSize, cudaMemcpyDeviceToHost));

    CUDA_CHECK(cudaFree(rgbDevice));
    static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(color_msg);
}
void RosCamera::depthPubCallback(rclcpp::PublisherBase* pub)
{

    if (!mEnableDepth || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mDepthSensor || !mSyntheticDataInterface->isSensorInitialized(mDepthSensor))
    {
        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("%s Depth Status (tick): %d", mViewportWindow->getWindowName(),
    //               mSyntheticDataInterface->isSensorInitialized(mDepthSensor));
    const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthSensor);

    const int depth_channels = 1;
    const size_t depth_step = depthInfo.tex.width * depth_channels * sizeof(float);


    sensor_msgs::msg::Image depth_msg;
    depth_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        depth_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        depth_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }
    depth_msg.width = depthInfo.tex.width;
    depth_msg.height = depthInfo.tex.height;
    depth_msg.step = depth_step;
    depth_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    depth_msg.data.resize(depthInfo.tex.height * depth_step);

    uint8_t* depth = &depth_msg.data[0];
    mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
    CUDA_CHECK(cudaMemcpy(depth, mDepthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height, cudaMemcpyDeviceToHost));
    static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(depth_msg);
}

void RosCamera::instancePubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnableSegmentation || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mSegmentationSensor || !mSyntheticDataInterface->isSensorInitialized(mSegmentationSensor))
    {
        mSegmentationSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("Segmentation Status (tick): %d",
    // mSyntheticDataInterface->isSensorInitialized(mSegmentationSensor));
    mSegmentationSensorData = mSyntheticDataInterface->getSensorDeviceData(mSegmentationSensor);
    const carb::sensors::SensorInfo& instanceInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);


    // instance (output is an image with integer labels)
    const int instance_channels = 1;
    const size_t instance_step = instanceInfo.tex.width * instance_channels * sizeof(float);

    sensor_msgs::msg::Image instance_msg;
    instance_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        instance_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        instance_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }
    instance_msg.width = instanceInfo.tex.width;
    instance_msg.height = instanceInfo.tex.height;
    instance_msg.step = instance_step;
    instance_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    instance_msg.data.resize(instanceInfo.tex.height * instance_step);

    uint8_t* instance = &instance_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        instance, mSegmentationSensorData, instanceInfo.tex.rowSize * instanceInfo.tex.height, cudaMemcpyDeviceToHost));
    static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(instance_msg);
}

void RosCamera::semanticPubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnableSegmentation || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mSemanticSensor || !mSyntheticDataInterface->isSensorInitialized(mSemanticSensor))
    {
        mSemanticSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("Semantic Status (tick): %d", mSyntheticDataInterface->isSensorInitialized(mSemanticSensor));
    mSemanticSensorData = mSyntheticDataInterface->getSensorDeviceData(mSemanticSensor);
    const carb::sensors::SensorInfo& semanticInfo = mSensorsInterface->getSensorInfo(mSemanticSensor);

    // segmentation (output is an image with integer labels)
    const int semantic_channels = 1;
    const size_t semantic_step = semanticInfo.tex.width * semantic_channels * sizeof(float);

    sensor_msgs::msg::Image semantic_msg;
    semantic_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        semantic_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        semantic_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }
    semantic_msg.width = semanticInfo.tex.width;
    semantic_msg.height = semanticInfo.tex.height;
    semantic_msg.step = semantic_step;
    semantic_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    semantic_msg.data.resize(semanticInfo.tex.height * semantic_step);

    uint8_t* semantic = &semantic_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        semantic, mSemanticSensorData, semanticInfo.tex.rowSize * semanticInfo.tex.height, cudaMemcpyDeviceToHost));
    static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(semantic_msg);
}

void RosCamera::labelPubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnableSegmentation || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mSemanticSensor || !mSyntheticDataInterface->isSensorInitialized(mSemanticSensor))
    {
        mSemanticSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("Semantic Status (tick): %d", mSyntheticDataInterface->isSensorInitialized(mSemanticSensor));

    std::string labels;
    labels.append("{");
    for (int i = 0; i < 256; ++i)
    {
        std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(i));
        if (!semanticLabel.empty())
        {
            labels.append(std::to_string(i));
            labels.append(": '");
            labels.append(semanticLabel.c_str());
            labels.append("'; ");
        }
    }
    labels.append("}");
    std_msgs::msg::String label_msg;
    label_msg.data = labels;
    static_cast<rclcpp::Publisher<std_msgs::msg::String, std::allocator<void>>*>(pub)->publish(label_msg);
}


void RosCamera::boundingbox2dPubCallback(rclcpp::PublisherBase* pub)
{

    if (!mEnableBoundingBox2D || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mBoundingBox2DSensor || !mSyntheticDataInterface->isSensorInitialized(mBoundingBox2DSensor))
    {
        mBoundingBox2DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("Bbox 2D Status (tick): %d", mSyntheticDataInterface->isSensorInitialized(mBoundingBox2DSensor));

    mBoundingBox2DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox2DSensor);

    const carb::sensors::SensorInfo& boundingBox2DInfo = mSensorsInterface->getSensorInfo(mBoundingBox2DSensor);
    size_t bufferSize = boundingBox2DInfo.buff.size;
    int numBoundingBoxes = bufferSize / sizeof(carb::sensors::BoundingBox2DValues);


    if (bufferSize > 0)
    {

        carb::sensors::BoundingBox2DValues* data =
            reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
        int numValidBoundingBoxes = 0;
        for (int i = 0; i < numBoundingBoxes; i++)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
            // Filter bounding boxes based on semantic data
            if (mBoundingBox2DClassList.size() > 0)
            {
                if (std::find(mBoundingBox2DClassList.begin(), mBoundingBox2DClassList.end(), semanticLabel) ==
                    mBoundingBox2DClassList.end())
                {
                    data++;
                    continue;
                }
            }
            data++;
            numValidBoundingBoxes++;
        }

        isaac_ros2_messages::msg::IsaacBoundingBoxArray bbox_msg;
        if (numValidBoundingBoxes > 0)
        {
            data = reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
            int boundingBoxId = 0;
            for (int i = 0; i < numBoundingBoxes; i++)
            {
                std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                // Filter bounding boxes based on semantic data
                if (mBoundingBox2DClassList.size() > 0)
                {
                    if (std::find(mBoundingBox2DClassList.begin(), mBoundingBox2DClassList.end(), semanticLabel) ==
                        mBoundingBox2DClassList.end())
                    {
                        data++;
                        continue;
                    }
                }
                isaac_ros2_messages::msg::IsaacBoundingBox bbox_single;
                bbox_single.name = semanticLabel;
                bbox_single.confidence = 1.0;
                bbox_single.xmin = data->x_min;
                bbox_single.ymin = data->y_min;
                bbox_single.xmax = data->x_max;
                bbox_single.ymax = data->y_max;

                bbox_msg.bboxes.push_back(bbox_single);

                data++;
                boundingBoxId++;
            }
        }
        static_cast<rclcpp::Publisher<isaac_ros2_messages::msg::IsaacBoundingBoxArray, std::allocator<void>>*>(pub)->publish(
            bbox_msg);
    }
}

void RosCamera::boundingbox3dPubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnableBoundingBox3D || mViewportWindow == nullptr)
    {
        return;
    }

    if (!mBoundingBox3DSensor || !mSyntheticDataInterface->isSensorInitialized(mBoundingBox3DSensor))
    {
        mBoundingBox3DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
        return;
    }
    // CARB_LOG_WARN("Bbox 3D Status (tick): %d", mSyntheticDataInterface->isSensorInitialized(mBoundingBox3DSensor));

    mBoundingBox3DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox3DSensor);

    const carb::sensors::SensorInfo& boundingBoxInfo = mSensorsInterface->getSensorInfo(mBoundingBox3DSensor);
    size_t bufferSize = boundingBoxInfo.buff.size;
    int numBoundingBoxes = bufferSize / sizeof(carb::sensors::BoundingBox3DValues);

    if (bufferSize > 0)
    {
        int numValidBoundingBoxes = 0;

        carb::sensors::BoundingBox3DValues* data =
            reinterpret_cast<carb::sensors::BoundingBox3DValues*>(mBoundingBox3DSensorData);

        for (int i = 0; i < numBoundingBoxes; i++)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
            // Filter bounding boxes based on semantic data
            if (mBoundingBox3DClassList.size() > 0)
            {
                if (std::find(mBoundingBox3DClassList.begin(), mBoundingBox3DClassList.end(), semanticLabel) ==
                    mBoundingBox3DClassList.end())
                {
                    data++;
                    continue;
                }
            }
            data++;
            numValidBoundingBoxes++;
        }

        isaac_ros2_messages::msg::BoundingBox3DArray bbox_msg;
        if (numValidBoundingBoxes > 0)
        {
            data = reinterpret_cast<carb::sensors::BoundingBox3DValues*>(mBoundingBox3DSensorData);

            int boundingBoxId = 0;
            for (int i = 0; i < numBoundingBoxes; i++)
            {
                std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                // Filter bounding boxes based on semantic data
                if (mBoundingBox3DClassList.size() > 0)
                {
                    if (std::find(mBoundingBox3DClassList.begin(), mBoundingBox3DClassList.end(), semanticLabel) ==
                        mBoundingBox3DClassList.end())
                    {
                        data++;
                        continue;
                    }
                }

                // Get pose in world space
                auto floatTransform = data->transform;
                std::vector<std::vector<float>> transformMatrix(4, std::vector<float>(4, 0));
                for (int row = 0; row < 4; row++)
                    for (int col = 0; col < 4; col++)
                        transformMatrix[row][col] = floatTransform[row][col];
                pxr::GfTransform gfTransform = pxr::GfTransform(pxr::GfMatrix4d(transformMatrix));
                pxr::GfVec3d translationValue = gfTransform.GetTranslation();
                pxr::GfQuatd rotationValue = gfTransform.GetRotation().GetQuat();
                pxr::GfVec3d scaleValue = gfTransform.GetScale() * mUnitScale;

                // Get min and max values of 3D bounding box in local space
                isaac_ros2_messages::msg::BoundingBox3D bbox_single;
                bbox_single.name = semanticLabel;
                bbox_single.confidence = 1.0;
                bbox_single.center.position.x = translationValue[0] * mUnitScale;
                bbox_single.center.position.y = translationValue[1] * mUnitScale;
                bbox_single.center.position.z = translationValue[2] * mUnitScale;

                bbox_single.center.orientation.x = rotationValue.GetImaginary()[0];
                bbox_single.center.orientation.y = rotationValue.GetImaginary()[1];
                bbox_single.center.orientation.z = rotationValue.GetImaginary()[2];
                bbox_single.center.orientation.w = rotationValue.GetReal();

                bbox_single.size.x = (data->x_max - data->x_min) * scaleValue[0];
                bbox_single.size.y = (data->y_max - data->y_min) * scaleValue[1];
                bbox_single.size.z = (data->z_max - data->z_min) * scaleValue[2];

                bbox_msg.bboxes.push_back(bbox_single);

                data++;
                boundingBoxId++;
            }
        }
        static_cast<rclcpp::Publisher<isaac_ros2_messages::msg::BoundingBox3DArray, std::allocator<void>>*>(pub)->publish(
            bbox_msg);
    }
}


}
}
}
