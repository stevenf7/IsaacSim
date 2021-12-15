// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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
#include "pcl_ros/point_cloud.h"

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <rangeSensorSchema/lidar.h>
#include <rosBridgeSchema/rosLidar.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosLidar : public IsaacComponent
{

public:
    RosLidar();
    // Virtual so that it can be called when object is destroyed
    virtual ~RosLidar();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onStart();
    virtual void onStop();
    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);
    void pointCloudPubCallback(ros::Publisher* pub);

private:
    bool mEnableLaserScan = true;
    std::string mLaserScanPubTopic = "/laser_scan";
    int mQueueSize = 0;
    pxr::SdfPath mLidarPath = pxr::SdfPath("/");
    omni::isaac::range_sensor::RangeSensorHandle mRangeSensorHandle = omni::isaac::range_sensor::kInvalidHandle;
    carb::Framework* mFramework = nullptr;
    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;
    pxr::RangeSensorSchemaLidar mLidarPrim;
    std::string mFrameId = "sim_lidar";
    bool mEnablePointCloud = false;
    std::string mPointCloudPubTopic = "/point_cloud";

    std::vector<float> mIntensitiesData;
    std::vector<float> mRangesData;
    std::vector<pcl::PointXYZ> mPointsData;
    size_t mNumBeamsRemaining;
    float mAngleMin;
    bool mResetLaserScan = true;

    float mPrevRotationRate;
    float mPrevHorizontalResolution;
    float mPrevHorizontalFov;
    float mPrevVerticalResolution;
    float mPrevVerticalFov;


    double mUnitScale;
};
}
}
}
