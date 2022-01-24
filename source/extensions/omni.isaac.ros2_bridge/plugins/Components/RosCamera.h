// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"
#include "omni/isaac/bridge/ViewportManager.h"
#include "omni/isaac/utils/Buffer.h"
#include "omni/isaac/utils/CameraSensor.h"

#include <omni/kit/IViewport.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <rosBridgeSchema/rosCamera.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{


class RosCamera : public IsaacComponent
{

public:
    RosCamera(utils::ViewportManager* viewportManager);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosCamera();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    void cameraInfoPubCallback(rclcpp::PublisherBase* pub);
    void rgbPubCallback(rclcpp::PublisherBase* pub);
    void depthPubCallback(rclcpp::PublisherBase* pub);
    void depthToPointCloudCallback(rclcpp::PublisherBase* pub);
    void semanticPubCallback(rclcpp::PublisherBase* pub);
    void instancePubCallback(rclcpp::PublisherBase* pub);
    void labelPubCallback(rclcpp::PublisherBase* pub);
    void boundingbox2dPubCallback(rclcpp::PublisherBase* pub);
    void boundingbox3dPubCallback(rclcpp::PublisherBase* pub);

private:
    carb::Framework* mFramework = nullptr;

    omni::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    utils::ViewportManager* mViewportManager = nullptr;

    pxr::SdfPath mCameraPath;
    pxr::UsdGeomCamera mCameraPrim;
    pxr::GfVec2i mResolution;

    pxr::GfVec2f mStereoOffset = pxr::GfVec2f(0.0, 0.0);

    bool mEnableRgb = false;
    bool mEnableDepth = false;
    bool mEnablePointCloud = false;
    bool mEnableSegmentation = false;
    bool mEnableBoundingBox2D = false;
    bool mEnableBoundingBox3D = false;
    std::vector<std::string> mBoundingBox2DClassList;
    std::vector<std::string> mBoundingBox3DClassList;


    double mUnitScale;

    std::string mCameraInfoPubTopic = "/camera_info";
    std::string mRgbPubTopic = "/rgb";
    std::string mDepthPubTopic = "/depth";
    std::string mPointCloudPubTopic = "/point_cloud";
    std::string mFrameId = "sim_camera";
    std::string mInstancePubTopic = "/instance";
    std::string mSemanticPubTopic = "/semantic";
    std::string mLabelPubTopic = "/label";
    std::string mBoundingBox2DPubTopic = "/bbox_2d";
    std::string mBoundingBox3DPubTopic = "/bbox_3d";
    int mQueueSize = 10;
    std::unique_ptr<utils::camera_sensor::CameraSensor> mCameraSensor;
};
}
}
}
