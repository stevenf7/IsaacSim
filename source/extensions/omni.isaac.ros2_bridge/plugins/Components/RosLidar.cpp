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

#include "geometry_msgs/msg/point32.hpp"
#include "pcl_conversions/pcl_conversions.h"
#include "rosgraph_msgs/msg/clock.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
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
    resetLaserScan = true;
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

    mRosNode->createPublisher<sensor_msgs::msg::LaserScan>(
        mPrim.GetPath().GetString(), mLaserScanPubTopic, mQueueSize, &RosLidar::pubCallback, this);
    mRosNode->createPublisher<sensor_msgs::msg::PointCloud2>(
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

void RosLidar::pubCallback(rclcpp::PublisherBase* pub)
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
        CARB_LOG_ERROR(
            "High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting or uncheck LaserScanEnabled");
        return;
    }
    sensor_msgs::msg::LaserScan laser_msg;
    laser_msg.header.frame_id = mFrameId;
    if (mUseSimTime)
    {
        laser_msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        laser_msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }

    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numRows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str()); // should be 1
    if (numRows > 1)
    {
        CARB_LOG_ERROR("High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan");
    }
    size_t numBeams = numColsTicked * numRows;

    float* theta = mLidarSensorInterface->getAzimuthData(mLidarPath.GetString().c_str());
    float* phi = mLidarSensorInterface->getZenithData(mLidarPath.GetString().c_str()); // should have one entry
    float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPath.GetString().c_str());
    uint8_t* intensities = mLidarSensorInterface->getIntensityData(mLidarPath.GetString().c_str());

    float maxRange = 100;
    float minRange = 0.4;
    float rotationRate = 0.0;
    float horizontalResolution = 0.4;
    float horizontalFov = 360;

    isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalFovAttr(), horizontalFov);

    size_t numBeamsTotal = horizontalFov / horizontalResolution;

    if (horizontalResolution == 0.0)
    {
        CARB_LOG_ERROR("Lidar Prim %s: Horizontal Resolution must be greater than 0.0", mLidarPath.GetString().c_str());
        return;
    }
    if (horizontalFov == 0.0)
    {
        CARB_LOG_ERROR("Lidar Prim %s: Horizontal FOV must be greater than 0.0", mLidarPath.GetString().c_str());
        return;
    }

    if (resetLaserScan)
    {
        intensities_data.clear();
        ranges_data.clear();
        numBeamsRemaining = numBeamsTotal;
        angle_min = std::min(theta[0], theta[numColsTicked - 1]);
        prev_rotationRate = rotationRate;
        prev_horizontalResolution = horizontalResolution;
        prev_horizontalFov = horizontalFov;
        resetLaserScan = false;
    }

    if (prev_rotationRate != rotationRate || prev_horizontalResolution != horizontalResolution ||
        prev_horizontalFov != horizontalFov)
    {
        intensities_data.clear();
        ranges_data.clear();
        numBeamsRemaining = numBeamsTotal;
        prev_rotationRate = rotationRate;
        prev_horizontalResolution = horizontalResolution;

        if (prev_horizontalFov != horizontalFov)
        {
            angle_min = std::min(theta[0], theta[numColsTicked - 1]);
            prev_horizontalFov = horizontalFov;
        }
    }

    if (numBeamsRemaining > numBeams)
    {
        for (size_t i = 0; i < numBeams; i++)
        {
            intensities_data.push_back(static_cast<float>(intensities[i]));
            ranges_data.push_back(ranges[i]);
        }
        numBeamsRemaining -= numBeams;
    }

    else if (numBeamsRemaining <= numBeams)
    {

        // Save data up to maximum FOV
        size_t i;
        for (i = 0; i < numBeamsRemaining; i++)
        {
            intensities_data.push_back(static_cast<float>(intensities[i]));
            ranges_data.push_back(ranges[i]);
        }

        // Setup ROS Lidar Message
        laser_msg.angle_min = angle_min;
        laser_msg.angle_max = angle_min + (horizontalFov * M_PI / 180.0);


        laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
        laser_msg.range_min = minRange;
        laser_msg.range_max = maxRange;

        laser_msg.ranges = ranges_data;
        laser_msg.intensities = intensities_data;

        laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
        laser_msg.time_increment = (horizontalFov / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

        static_cast<rclcpp::Publisher<sensor_msgs::msg::LaserScan, std::allocator<void>>*>(pub)->publish(laser_msg);

        // Reset fields for new ROS Lidar message
        ranges_data.clear();
        intensities_data.clear();

        // Save remaining data
        size_t numBeamsOffset = numBeams - numBeamsRemaining;
        for (size_t j = 0; j < numBeamsOffset; j++)
        {
            intensities_data.push_back(static_cast<float>(intensities[i]));
            ranges_data.push_back(ranges[i]);
            i++;
        }
        numBeamsRemaining = numBeamsTotal - numBeamsOffset;
    }
}

void RosLidar::pointCloudPubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnablePointCloud)
    {
        return;
    }
    typedef pcl::PointCloud<pcl::PointXYZ> PointCloud;
    std_msgs::msg::Header header_msg;
    PointCloud point_cloud;
    header_msg.frame_id = mFrameId;

    if (mUseSimTime)
    {
        header_msg.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        header_msg.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }


    carb::Float3* lidarData = mLidarSensorInterface->getPointCloud(mLidarPath.GetString().c_str());
    int rows = mLidarSensorInterface->getNumRows(mLidarPath.GetString().c_str());
    int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    pcl_conversions::toPCL(header_msg, point_cloud.header);

    point_cloud.height = rows;
    point_cloud.width = numColsTicked;

    std::vector<int> points;

    for (int i = 0; i < rows * numColsTicked; i++)
    {
        pcl::PointXYZ points;
        points.x = lidarData[i].x * mUnitScale;
        points.y = lidarData[i].y * mUnitScale;
        points.z = lidarData[i].z * mUnitScale;

        point_cloud.points.push_back(points);
    }

    sensor_msgs::msg::PointCloud2 point_cloud_msg;
    pcl::toROSMsg(point_cloud, point_cloud_msg);
    static_cast<rclcpp::Publisher<sensor_msgs::msg::PointCloud2, std::allocator<void>>*>(pub)->publish(point_cloud_msg);
}


}
}
}
