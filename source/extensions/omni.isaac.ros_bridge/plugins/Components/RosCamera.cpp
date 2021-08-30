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

#include "isaac_ros_messages/BoundingBox3D.h"
#include "isaac_ros_messages/BoundingBox3DArray.h"
#include "isaac_ros_messages/IsaacBoundingBox.h"
#include "isaac_ros_messages/IsaacBoundingBoxArray.h"
#include "pcl_conversions/pcl_conversions.h"
#include "rosgraph_msgs/Clock.h"
#include "sensor_msgs/CameraInfo.h"
#include "sensor_msgs/Image.h"
#include "sensor_msgs/image_encodings.h"
#include "std_msgs/Int64.h"
#include "std_msgs/String.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/cuda/CudaRuntime.h>

#include <boost/algorithm/string.hpp>
#include <omni/isaac/ros/Utils.h>
#include <omni/kit/ViewportWindowUtils.h>

#include <cuda.h>
#include <time.h>
namespace omni
{
namespace isaac
{
namespace ros_bridge
{

extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);
extern "C" void depthToPCL(
    pcl::PointXYZ* dest, const float* src, int width, int height, float fx, float fy, float cx, float cy);

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
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPointCloudPubTopic);
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
    if (mDepthForPCLSensor)
    {
        mSyntheticDataInterface->destroySensor(mDepthForPCLSensor);
        mDepthForPCLSensor = nullptr;
        mDepthForPCLSensorData = nullptr;
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
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPointCloudPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mInstancePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSemanticPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLabelPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox2DPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox3DPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetCameraInfoPubTopicAttr(), mCameraInfoPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbPubTopicAttr(), mRgbPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthPubTopicAttr(), mDepthPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudPubTopicAttr(), mPointCloudPubTopic);
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
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudEnabledAttr(), mEnablePointCloud);
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationEnabledAttr(), mEnableSegmentation);
    std::string filterClassList2D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DEnabledAttr(), mEnableBoundingBox2D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DClassListAttr(), filterClassList2D);
    std::string filterClassList3D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DEnabledAttr(), mEnableBoundingBox3D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DClassListAttr(), filterClassList3D);
    isaac::utils::safeGetAttribute(typedPrim.GetStereoOffsetAttr(), mStereoOffset);

    ros_utils::addPrefix(mRosNodePrefix, mFrameId, false);
    ros_utils::addPrefix(mRosNodePrefix, mCameraInfoPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mRgbPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mDepthPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mPointCloudPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mInstancePubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mSemanticPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mLabelPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mBoundingBox2DPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mBoundingBox3DPubTopic, true);

    if (mEnableRgb || mEnableDepth || mEnablePointCloud || mEnableSegmentation || mEnableBoundingBox2D ||
        mEnableBoundingBox3D)
    {
        mRosNode->createPublisher<sensor_msgs::CameraInfo>(
            mPrim.GetPath().GetString(), mCameraInfoPubTopic, mQueueSize, &RosCamera::cameraInfoPubCallback, this);
    }
    if (mEnableRgb)
    {
        mRosNode->createPublisher<sensor_msgs::Image>(
            mPrim.GetPath().GetString(), mRgbPubTopic, mQueueSize, &RosCamera::rgbPubCallback, this);
    }
    if (mEnableDepth)
    {
        mRosNode->createPublisher<sensor_msgs::Image>(
            mPrim.GetPath().GetString(), mDepthPubTopic, mQueueSize, &RosCamera::depthPubCallback, this);
    }

    if (mEnablePointCloud)
    {
        mRosNode->createPublisher<sensor_msgs::PointCloud2>(
            mPrim.GetPath().GetString(), mPointCloudPubTopic, mQueueSize, &RosCamera::depthToPointCloudCallback, this);
    }
    if (mEnableSegmentation)
    {
        mRosNode->createPublisher<sensor_msgs::Image>(
            mPrim.GetPath().GetString(), mInstancePubTopic, mQueueSize, &RosCamera::instancePubCallback, this);
        mRosNode->createPublisher<sensor_msgs::Image>(
            mPrim.GetPath().GetString(), mSemanticPubTopic, mQueueSize, &RosCamera::semanticPubCallback, this);
        mRosNode->createPublisher<std_msgs::String>(
            mPrim.GetPath().GetString(), mLabelPubTopic, mQueueSize, &RosCamera::labelPubCallback, this);
    }
    if (mEnableBoundingBox2D)
    {
        mRosNode->createPublisher<isaac_ros_messages::IsaacBoundingBoxArray>(
            mPrim.GetPath().GetString(), mBoundingBox2DPubTopic, mQueueSize, &RosCamera::boundingbox2dPubCallback, this);
    }
    if (mEnableBoundingBox3D)
    {
        mRosNode->createPublisher<isaac_ros_messages::BoundingBox3DArray>(
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

    if (mEnablePointCloud)
    {
        mDepthForPCLSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
    }
    else
    {
        mDepthForPCLSensor = nullptr;
        mDepthForPCLSensorData = nullptr;
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

void getCameraIntrinsics(pxr::UsdGeomCamera cameraPrim,
                         carb::sensors::SensorInfo imgInfo,
                         float& fx,
                         float& fy,
                         float& cx,
                         float& cy,
                         float& fthetaPolyA,
                         float& fthetaPolyB,
                         float& fthetaPolyC,
                         float& fthetaPolyD,
                         float& fthetaPolyE,
                         pxr::TfToken& projectionType)
{

    float focalLength;
    cameraPrim.GetFocalLengthAttr().Get(&focalLength);

    float horizontalAperture, verticalAperture;
    cameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    verticalAperture =
        static_cast<float>(imgInfo.tex.height) / static_cast<float>(imgInfo.tex.width) * horizontalAperture;

    fx = imgInfo.tex.width * focalLength / horizontalAperture;
    fy = imgInfo.tex.height * focalLength / verticalAperture;
    cx = imgInfo.tex.width * 0.5f;
    cy = imgInfo.tex.height * 0.5;

    pxr::UsdPrim prim = cameraPrim.GetPrim();
    prim.GetAttribute(pxr::TfToken("cameraProjectionType")).Get(&projectionType);
    prim.GetAttribute(pxr::TfToken("fthetaPolyA")).Get(&fthetaPolyA);
    prim.GetAttribute(pxr::TfToken("fthetaPolyB")).Get(&fthetaPolyB);
    prim.GetAttribute(pxr::TfToken("fthetaPolyC")).Get(&fthetaPolyC);
    prim.GetAttribute(pxr::TfToken("fthetaPolyD")).Get(&fthetaPolyD);
    prim.GetAttribute(pxr::TfToken("fthetaPolyE")).Get(&fthetaPolyE);
}

void RosCamera::cameraInfoPubCallback(ros::Publisher* pub)
{
    if (mViewportWindow == nullptr)
        return;
    const char* cameraPath = mViewportWindow->getActiveCamera();
    if (!cameraPath)
        return;

    pxr::SdfPath path(cameraPath);
    pxr::UsdPrim prim = mStage->GetPrimAtPath(path);

    pxr::UsdGeomCamera cameraPrim(prim);

    pxr::GfVec2f clipRange;

    cameraPrim.GetClippingRangeAttr().Get(&clipRange);

    carb::sensors::SensorInfo imgInfo;
    if (mEnableRgb && mSyntheticDataInterface->isSensorInitialized(mRgbSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mRgbSensor);
    }
    else if (mEnableDepth && mSyntheticDataInterface->isSensorInitialized(mDepthSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mDepthSensor);
    }
    else if (mEnablePointCloud && mSyntheticDataInterface->isSensorInitialized(mDepthForPCLSensor))
    {
        imgInfo = mSensorsInterface->getSensorInfo(mDepthForPCLSensor);
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

    // verticalAperture =
    //    static_cast<float>(imgInfo.tex.height) / static_cast<float>(imgInfo.tex.width) * horizontalAperture;

    sensor_msgs::CameraInfo cam_info_msg;
    cam_info_msg.header.seq = 0;
    cam_info_msg.header.frame_id = mFrameId;
    setRosTimeStamp(cam_info_msg.header.stamp);


    cam_info_msg.height = imgInfo.tex.height;
    cam_info_msg.width = imgInfo.tex.width;
    cam_info_msg.distortion_model = "plumb_bob";


    // ROS image: conventions
    // origin of frame should be optical center of camera
    // +x should point to the right in the image
    // +y should point down in the image
    // +z should point into the plane of the image

    float fx, fy, cy, cx, fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE;
    pxr::TfToken projectionType = pxr::TfToken("pinhole");

    getCameraIntrinsics(cameraPrim, imgInfo, fx, fy, cx, cy, fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD,
                        fthetaPolyE, projectionType);

    cam_info_msg.K = { fx, 0, cx, 0, fy, cy, 0, 0, 1 };

    cam_info_msg.P = { fx, 0, cx, mStereoOffset[0], 0, fy, cy, mStereoOffset[1], 0, 0, 1, 0 };

    cam_info_msg.D = { fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE };
    cam_info_msg.distortion_model = projectionType.GetString();

    pub->publish(cam_info_msg);
}

void RosCamera::rgbPubCallback(ros::Publisher* pub)
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

    sensor_msgs::Image color_msg;
    color_msg.header.seq = 0;
    color_msg.header.frame_id = mFrameId;
    setRosTimeStamp(color_msg.header.stamp);

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
    pub->publish(color_msg);
}

void RosCamera::depthPubCallback(ros::Publisher* pub)
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


    sensor_msgs::Image depth_msg;
    depth_msg.header.seq = 0;
    depth_msg.header.frame_id = mFrameId;
    setRosTimeStamp(depth_msg.header.stamp);

    depth_msg.width = depthInfo.tex.width;
    depth_msg.height = depthInfo.tex.height;
    depth_msg.step = depth_step;
    depth_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    depth_msg.data.resize(depthInfo.tex.height * depth_step);

    uint8_t* depth = &depth_msg.data[0];
    mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
    CUDA_CHECK(cudaMemcpy(depth, mDepthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(depth_msg);
}


void RosCamera::depthToPointCloudCallback(ros::Publisher* pub)
{

    if (!mEnablePointCloud || mViewportWindow == nullptr)
    {
        return;
    }
    if (!mDepthForPCLSensor || !mSyntheticDataInterface->isSensorInitialized(mDepthForPCLSensor))
    {
        mDepthForPCLSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
        return;
    }

    const char* cameraPath = mViewportWindow->getActiveCamera();

    if (!cameraPath)
        return;

    pxr::SdfPath path(cameraPath);
    pxr::UsdPrim prim = mStage->GetPrimAtPath(path);
    pxr::UsdGeomCamera cameraPrim(prim);

    const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthForPCLSensor);

    float fx, fy, cy, cx, fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE;
    pxr::TfToken projectionType = pxr::TfToken("pinhole");

    getCameraIntrinsics(cameraPrim, depthInfo, fx, fy, cx, cy, fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD,
                        fthetaPolyE, projectionType);

    mDepthForPCLSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthForPCLSensor);

    int w = depthInfo.tex.width;
    int h = depthInfo.tex.height;

    const size_t bufferSize = depthInfo.tex.width * depthInfo.tex.height * sizeof(pcl::PointXYZ);

    pcl::PointXYZ* pclDevice = nullptr;

    typedef pcl::PointCloud<pcl::PointXYZ> PointCloud;
    PointCloud cloud;

    cloud.points.resize(w * h);

    CUDA_CHECK(cudaMalloc(&pclDevice, bufferSize));

    depthToPCL(pclDevice, (float*)mDepthForPCLSensorData, depthInfo.tex.width, depthInfo.tex.height, fx, fy, cx, cy);

    CUDA_CHECK(cudaMemcpy(&cloud.points[0], pclDevice, bufferSize, cudaMemcpyDeviceToHost));

    CUDA_CHECK(cudaFree(pclDevice));

    cloud.width = w;
    cloud.height = h;
    cloud.is_dense = false;

    sensor_msgs::PointCloud2 point_cloud_msg;

    pcl::toROSMsg(cloud, point_cloud_msg);

    point_cloud_msg.header.frame_id = mFrameId;

    setRosTimeStamp(point_cloud_msg.header.stamp);

    pub->publish(point_cloud_msg);
}

void RosCamera::instancePubCallback(ros::Publisher* pub)
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

    sensor_msgs::Image instance_msg;
    instance_msg.header.seq = 0;
    instance_msg.header.frame_id = mFrameId;
    setRosTimeStamp(instance_msg.header.stamp);

    instance_msg.width = instanceInfo.tex.width;
    instance_msg.height = instanceInfo.tex.height;
    instance_msg.step = instance_step;
    instance_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    instance_msg.data.resize(instanceInfo.tex.height * instance_step);

    uint8_t* instance = &instance_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        instance, mSegmentationSensorData, instanceInfo.tex.rowSize * instanceInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(instance_msg);
}

void RosCamera::semanticPubCallback(ros::Publisher* pub)
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

    sensor_msgs::Image semantic_msg;
    semantic_msg.header.seq = 0;
    semantic_msg.header.frame_id = mFrameId;
    setRosTimeStamp(semantic_msg.header.stamp);

    semantic_msg.width = semanticInfo.tex.width;
    semantic_msg.height = semanticInfo.tex.height;
    semantic_msg.step = semantic_step;
    semantic_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    semantic_msg.data.resize(semanticInfo.tex.height * semantic_step);

    uint8_t* semantic = &semantic_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        semantic, mSemanticSensorData, semanticInfo.tex.rowSize * semanticInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(semantic_msg);
}

void RosCamera::labelPubCallback(ros::Publisher* pub)
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
    std_msgs::String label_msg;
    label_msg.data = labels;
    pub->publish(label_msg);
}


void RosCamera::boundingbox2dPubCallback(ros::Publisher* pub)
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

        isaac_ros_messages::IsaacBoundingBoxArray bbox_msg;
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
                isaac_ros_messages::IsaacBoundingBox bbox_single;
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
        pub->publish(bbox_msg);
    }
}

void RosCamera::boundingbox3dPubCallback(ros::Publisher* pub)
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

        isaac_ros_messages::BoundingBox3DArray bbox_msg;
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
                isaac_ros_messages::BoundingBox3D bbox_single;
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
        pub->publish(bbox_msg);
    }
}


}
}
}
