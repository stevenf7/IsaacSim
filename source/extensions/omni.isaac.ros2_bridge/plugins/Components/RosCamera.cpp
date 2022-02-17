// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "isaac_ros2_messages/msg/bounding_box3_d.hpp"
#include "isaac_ros2_messages/msg/bounding_box3_d_array.hpp"
#include "isaac_ros2_messages/msg/isaac_bounding_box.hpp"
#include "isaac_ros2_messages/msg/isaac_bounding_box_array.hpp"
#include "pcl_conversions/pcl_conversions.h"
#include "rosgraph_msgs/msg/clock.hpp"
#include "sensor_msgs/image_encodings.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/cuda/CudaRuntime.h>

#include <boost/algorithm/string.hpp>
#include <omni/isaac/ros/RosCamera.h>
#include <omni/isaac/ros/Utils.h>
#include <omni/kit/ViewportWindowUtils.h>

#include <cuda.h>
#include <time.h>
namespace omni
{
namespace isaac
{
namespace ros2_bridge
{

RosCamera::RosCamera(utils::ViewportManager* viewportManager)
{

    mViewportManager = viewportManager;
    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }


    mSyntheticDataInterface = mFramework->acquireInterface<omni::syntheticdata::SyntheticData>();
    if (!mSyntheticDataInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::syntheticdata::SyntheticData interface");
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
    mFramework->releaseInterface(mSyntheticDataInterface);
}

void RosCamera::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}

void RosCamera::onStart()
{
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    mCameraSensor = std::make_unique<utils::camera_sensor::CameraSensor>(mViewportManager);

    onComponentChange();
}
void RosCamera::onStop()
{
    mCameraSensor.reset();
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

    if (mEnablePointCloud)
    {
        mRosNode->createPublisher<sensor_msgs::msg::PointCloud2>(
            mPrim.GetPath().GetString(), mPointCloudPubTopic, mQueueSize, &RosCamera::depthToPointCloudCallback, this);
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
    mCameraPrim = pxr::UsdGeomCamera(mStage->GetPrimAtPath(mCameraPath));

    if (!mCameraPrim)
    {
        CARB_LOG_ERROR("%s is not a USD Camera", mCameraPath.GetString().c_str());
        mCameraSensor.reset();
        return;
    }
    if (mCameraSensor)
    {
        mCameraSensor->updateViewportSettings(mCameraPath, mPrim.GetPath(), mResolution, mDoStart, mEnableRgb,
                                              mEnableDepth, mEnablePointCloud, mEnableSegmentation,
                                              mEnableBoundingBox2D, mEnableBoundingBox3D);
    }
}

void RosCamera::cameraInfoPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Info Pub");
    if (!mCameraSensor)
    {
        return;
    }
    pxr::GfVec2f clipRange;

    mCameraPrim.GetClippingRangeAttr().Get(&clipRange);

    carb::sensors::SensorInfo imgInfo = mCameraSensor->getSensorInfo();

    // We have to ignore the vertical aperture number because our pixels are square
    // Compute it directly from the image size and horizontal aperture

    // verticalAperture =
    //    static_cast<float>(imgInfo.tex.height) / static_cast<float>(imgInfo.tex.width) * horizontalAperture;

    sensor_msgs::msg::CameraInfo cam_info_msg;
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
    ;

    ros_base::getCameraIntrinsics(mCameraPrim, imgInfo, fx, fy, cx, cy, fthetaPolyA, fthetaPolyB, fthetaPolyC,
                                  fthetaPolyD, fthetaPolyE, projectionType);

    cam_info_msg.k = { fx, 0, cx, 0, fy, cy, 0, 0, 1 };

    cam_info_msg.p = { fx, 0, cx, mStereoOffset[0], 0, fy, cy, mStereoOffset[1], 0, 0, 1, 0 };

    cam_info_msg.d = { fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE };
    cam_info_msg.distortion_model = projectionType.GetString();


    static_cast<rclcpp::Publisher<sensor_msgs::msg::CameraInfo, std::allocator<void>>*>(pub)->publish(cam_info_msg);
}

void RosCamera::rgbPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera RGB Pub");
    if (!mEnableRgb || !mCameraSensor)
    {
        return;
    }
    const carb::sensors::SensorInfo& rgbInfo = mCameraSensor->getSensorInfo(carb::sensors::SensorType::eRgb);

    const int color_channels = 3;
    const size_t color_step = rgbInfo.tex.width * color_channels * sizeof(uint8_t);

    sensor_msgs::msg::Image color_msg;
    color_msg.header.frame_id = mFrameId;
    setRosTimeStamp(color_msg.header.stamp);

    color_msg.width = rgbInfo.tex.width;
    color_msg.height = rgbInfo.tex.height;
    color_msg.step = color_step;
    color_msg.encoding = sensor_msgs::image_encodings::RGB8;
    color_msg.data.resize(rgbInfo.tex.height * color_step);
    uint8_t* rgb = &color_msg.data[0];
    if (mCameraSensor->getRGB(rgb))
    {
        static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(color_msg);
    }
}
void RosCamera::depthPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Depth Pub");
    if (!mEnableDepth || !mCameraSensor)
    {
        return;
    }

    const carb::sensors::SensorInfo& depthInfo =
        mCameraSensor->getSensorInfo(carb::sensors::SensorType::eDistanceToImagePlane);


    const int depth_channels = 1;
    const size_t depth_step = depthInfo.tex.width * depth_channels * sizeof(float);


    sensor_msgs::msg::Image depth_msg;
    depth_msg.header.frame_id = mFrameId;
    setRosTimeStamp(depth_msg.header.stamp);

    depth_msg.width = depthInfo.tex.width;
    depth_msg.height = depthInfo.tex.height;
    depth_msg.step = depth_step;
    depth_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    depth_msg.data.resize(depthInfo.tex.height * depth_step);

    uint8_t* depth = &depth_msg.data[0];
    if (mCameraSensor->getDepth(depth))
    {
        static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(depth_msg);
    }
}


void RosCamera::depthToPointCloudCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Point Cloud Pub");
    if (!mEnablePointCloud || !mCameraSensor)
    {
        return;
    }

    const carb::sensors::SensorInfo& depthInfo =
        mCameraSensor->getSensorInfo(carb::sensors::SensorType::eDistanceToImagePlane);

    float fx, fy, cy, cx, fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE;
    pxr::TfToken projectionType = pxr::TfToken("pinhole");

    ros_base::getCameraIntrinsics(mCameraPrim, depthInfo, fx, fy, cx, cy, fthetaPolyA, fthetaPolyB, fthetaPolyC,
                                  fthetaPolyD, fthetaPolyE, projectionType);


    const size_t bufferSize = depthInfo.tex.width * depthInfo.tex.height * sizeof(pcl::PointXYZ);

    sensor_msgs::msg::PointCloud2 point_cloud_msg;
    point_cloud_msg.data.resize(bufferSize);

    point_cloud_msg.header.frame_id = mFrameId;
    point_cloud_msg.width = depthInfo.tex.width;
    point_cloud_msg.height = depthInfo.tex.height;
    point_cloud_msg.is_dense = false;
    point_cloud_msg.point_step = sizeof(pcl::PointXYZ);
    point_cloud_msg.row_step = static_cast<uint32_t>(sizeof(pcl::PointXYZ) * point_cloud_msg.width);
    pcl::PCLPointCloud2 pcl_pc2;
    pcl_pc2.fields.clear();
    pcl::for_each_type<typename pcl::traits::fieldList<pcl::PointXYZ>::type>(
        pcl::detail::FieldAdder<pcl::PointXYZ>(pcl_pc2.fields));
    pcl_conversions::fromPCL(pcl_pc2.fields, point_cloud_msg.fields);
    setRosTimeStamp(point_cloud_msg.header.stamp);
    if (mCameraSensor->getPCL(&point_cloud_msg.data[0], fx, fy, cx, cy))
    {
        static_cast<rclcpp::Publisher<sensor_msgs::msg::PointCloud2, std::allocator<void>>*>(pub)->publish(
            point_cloud_msg);
    }
}

void RosCamera::instancePubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Instance Pub");
    if (!mEnableSegmentation || !mCameraSensor)
    {
        return;
    }

    const carb::sensors::SensorInfo& instanceInfo =
        mCameraSensor->getSensorInfo(carb::sensors::SensorType::eInstanceSegmentation);


    // instance (output is an image with integer labels)
    const int instance_channels = 1;
    const size_t instance_step = instanceInfo.tex.width * instance_channels * sizeof(float);

    sensor_msgs::msg::Image instance_msg;
    instance_msg.header.frame_id = mFrameId;
    setRosTimeStamp(instance_msg.header.stamp);

    instance_msg.width = instanceInfo.tex.width;
    instance_msg.height = instanceInfo.tex.height;
    instance_msg.step = instance_step;
    instance_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    instance_msg.data.resize(instanceInfo.tex.height * instance_step);

    uint8_t* instance = &instance_msg.data[0];
    if (mCameraSensor->getInstance(instance))
    {
        static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(instance_msg);
    }
}

void RosCamera::semanticPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Semantic Pub");
    if (!mEnableSegmentation || !mCameraSensor)
    {
        return;
    }

    const carb::sensors::SensorInfo& semanticInfo =
        mCameraSensor->getSensorInfo(carb::sensors::SensorType::eSemanticSegmentation);

    // segmentation (output is an image with integer labels)
    const int semantic_channels = 1;
    const size_t semantic_step = semanticInfo.tex.width * semantic_channels * sizeof(float);

    sensor_msgs::msg::Image semantic_msg;
    semantic_msg.header.frame_id = mFrameId;
    setRosTimeStamp(semantic_msg.header.stamp);

    semantic_msg.width = semanticInfo.tex.width;
    semantic_msg.height = semanticInfo.tex.height;
    semantic_msg.step = semantic_step;
    semantic_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    semantic_msg.data.resize(semanticInfo.tex.height * semantic_step);

    uint8_t* semantic = &semantic_msg.data[0];
    if (mCameraSensor->getSemantic(semantic))
    {
        static_cast<rclcpp::Publisher<sensor_msgs::msg::Image, std::allocator<void>>*>(pub)->publish(semantic_msg);
    }
}

void RosCamera::labelPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Label Pub");
    if (!mEnableSegmentation || !mCameraSensor)
    {
        return;
    }
    // TODO: do this on change instead of each frame?
    std::map<uint8_t, std::string> labelMap;
    if (!mCameraSensor->getLabels(labelMap))
    {
        return;
    }

    std::string labels;
    labels.append("{");
    int index = 0;
    for (std::map<uint8_t, std::string>::iterator it = labelMap.begin(); it != labelMap.end(); ++it)
    {
        labels.append(std::to_string(it->first));
        labels.append(": '");
        labels.append(it->second.c_str());
        labels.append("'; ");
        index++;
    }
    labels.append("}");
    std_msgs::msg::String label_msg;
    label_msg.data = labels;
    static_cast<rclcpp::Publisher<std_msgs::msg::String, std::allocator<void>>*>(pub)->publish(label_msg);
}


void RosCamera::boundingbox2dPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Bbox2d Pub");
    if (!mEnableBoundingBox2D || !mCameraSensor)
    {
        return;
    }
    size_t numBoundingBoxes = 0;
    carb::sensors::BoundingBox2DValues* data = nullptr;
    if (!mCameraSensor->getBBox2D(data, numBoundingBoxes))
    {
        return;
    }


    isaac_ros2_messages::msg::IsaacBoundingBoxArray bbox_msg;

    int numValidBoundingBoxes = 0;
    for (size_t i = 0; i < numBoundingBoxes; i++)
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
        numValidBoundingBoxes++;
    }
    if (numValidBoundingBoxes > 0)
    {
        static_cast<rclcpp::Publisher<isaac_ros2_messages::msg::IsaacBoundingBoxArray, std::allocator<void>>*>(pub)->publish(
            bbox_msg);
    }
}

void RosCamera::boundingbox3dPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Camera Bbox3d Pub");
    if (!mEnableBoundingBox3D || !mCameraSensor)
    {
        return;
    }

    size_t numBoundingBoxes = 0;
    carb::sensors::BoundingBox3DValues* data = nullptr;

    if (!mCameraSensor->getBBox3D(data, numBoundingBoxes))
    {
        return;
    }

    isaac_ros2_messages::msg::BoundingBox3DArray bbox_msg;
    int numValidBoundingBoxes = 0;
    for (size_t i = 0; i < numBoundingBoxes; i++)
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
        numValidBoundingBoxes++;
    }
    if (numValidBoundingBoxes > 0)
    {
        static_cast<rclcpp::Publisher<isaac_ros2_messages::msg::BoundingBox3DArray, std::allocator<void>>*>(pub)->publish(
            bbox_msg);
    }
}


}
}
}
