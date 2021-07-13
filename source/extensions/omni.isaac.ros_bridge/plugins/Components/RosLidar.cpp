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

#include "RosLidar.h"

#include "geometry_msgs/Point32.h"
#include "pcl_ros/point_cloud.h"
#include "rosgraph_msgs/Clock.h"
#include "sensor_msgs/LaserScan.h"
#include "sensor_msgs/PointCloud2.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

RosLidar::RosLidar()
{
    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    mLidarSensorInterface = mFramework->acquireInterface<omni::isaac::range_sensor::LidarSensorInterface>();
    if (!mLidarSensorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        return;
    }
}
RosLidar::~RosLidar()
{
    CARB_LOG_INFO("RosLidar Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLaserScanPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPointCloudPubTopic);
}

void RosLidar::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosLidar::onStart()
{
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    onComponentChange();
}
void RosLidar::onStop()
{
}
void RosLidar::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosLidar& typedPrim = (pxr::RosBridgeSchemaRosLidar)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLaserScanPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPointCloudPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetLaserScanPubTopicAttr(), mLaserScanPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetLaserScanEnabledAttr(), mEnableLaserScan);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudPubTopicAttr(), mPointCloudPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudEnabledAttr(), mEnablePointCloud);
    isaac::utils::safeGetAttribute(typedPrim.GetFrameIdAttr(), mFrameId);

    mRosNode->createPublisher<sensor_msgs::LaserScan>(
        mPrim.GetPath().GetString(), mLaserScanPubTopic, mQueueSize, &RosLidar::pubCallback, this);
    mRosNode->createPublisher<sensor_msgs::PointCloud2>(
        mPrim.GetPath().GetString(), mPointCloudPubTopic, mQueueSize, &RosLidar::pointCloudPubCallback, this);


    pxr::SdfPathVector targets;
    typedPrim.GetLidarPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mLidarPath = targets[0];

    pxr::UsdPrim prim = mStage->GetPrimAtPath(targets[0]);
    if (!prim.IsA<pxr::RangeSensorSchemaLidar>())
    {
        CARB_LOG_ERROR("Prim is not a Lidar Prim");
        return;
    }
    mLidarPrim = pxr::RangeSensorSchemaLidar(prim);
    if (!mLidarSensorInterface->isLidarSensor(targets[0].GetString().c_str()))
    {
        CARB_LOG_ERROR("Prim is not registered with Lidar extension");
        return;
    }
}

void RosLidar::pubCallback(ros::Publisher* pub)
{
    // Lidar prim hasn't been assigned yet
    if (mLidarPath == pxr::SdfPath("/"))
    {
        CARB_LOG_ERROR(
            "No Lidar prim reference assigned, Please Create->Isaac->Sensors->Lidar and then assign the relationship to this prim");
        return;
    }
    if (!mLidarSensorInterface->isLidarSensor(mLidarPath.GetString().c_str()))
    {
        CARB_LOG_ERROR("Invalid Lidar Reference, Prim is not registered with Lidar extension");
        return;
    }

    if (!mEnableLaserScan)
    {
        return;
    }

    bool highLod = false;
    isaac::utils::safeGetAttribute(mLidarPrim.GetHighLodAttr(), highLod);

    if (highLod)
    {
        CARB_LOG_WARN(
            "High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting or uncheck LaserScanEnabled");
        return;
    }
    sensor_msgs::LaserScan laser_msg;
    laser_msg.header.seq = 0;
    laser_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        laser_msg.header.stamp.fromSec(mTimeSeconds);
    }
    else
    {
        laser_msg.header.stamp.fromNSec(mSystemTimeNanoSeconds);
    }

    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numRows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str()); // should be 1
    if (numRows > 1)
    {
        CARB_LOG_WARN("High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan");
    }
    size_t numBeams = numColsTicked * numRows;

    float* theta = mLidarSensorInterface->getAzimuthData(mLidarPath.GetString().c_str());
    float* phi = mLidarSensorInterface->getZenithData(mLidarPath.GetString().c_str()); // should have one entry
    float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPath.GetString().c_str());
    uint8_t* intensities = mLidarSensorInterface->getIntensityData(mLidarPath.GetString().c_str());

    float maxRange = 100;
    float minRange = 0.4;
    float rotationRate = 20;
    float horizontalResolution = 0.4;

    isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);


    laser_msg.angle_min = std::min(theta[0], theta[numColsTicked - 1]);
    laser_msg.angle_max = std::max(theta[0], theta[numColsTicked - 1]);
    laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
    laser_msg.time_increment = mTimeDelta;
    laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
    laser_msg.range_min = minRange;
    laser_msg.range_max = maxRange;
    laser_msg.ranges.resize(numBeams);
    laser_msg.intensities.resize(numBeams);
    std::memcpy(laser_msg.ranges.data(), ranges, numBeams * sizeof(float));
    // Need to convert from uint8 to float
    for (size_t i = 0; i < numBeams; i++)
    {
        laser_msg.intensities[i] = static_cast<float>(intensities[i]);
    }
    pub->publish(laser_msg);
}

void RosLidar::pointCloudPubCallback(ros::Publisher* pub)
{
    if (!mEnablePointCloud)
    {
        return;
    }

    typedef pcl::PointCloud<pcl::PointXYZ> PointCloud;
    std_msgs::Header header_msg;
    PointCloud::Ptr point_cloud_msg(new PointCloud);
    header_msg.frame_id = mFrameId;

    if (mUseSimTime)
    {
        header_msg.stamp.fromSec(mTimeSeconds);
    }
    else
    {
        header_msg.stamp.fromNSec(mSystemTimeNanoSeconds);
    }

    carb::Float3* lidarData = mLidarSensorInterface->getPointCloud(mLidarPath.GetString().c_str());
    int rows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str());
    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());

    pcl_conversions::toPCL(header_msg, point_cloud_msg->header);

    point_cloud_msg->height = rows;
    point_cloud_msg->width = numColsTicked;

    std::vector<int> points;

    for (int i = 0; i < rows * numColsTicked; i++)
    {
        pcl::PointXYZ points;
        points.x = lidarData[i].x * mUnitScale;
        points.y = lidarData[i].y * mUnitScale;
        points.z = lidarData[i].z * mUnitScale;

        point_cloud_msg->points.push_back(points);
    }

    pub->publish(point_cloud_msg);
}


}
}
}
