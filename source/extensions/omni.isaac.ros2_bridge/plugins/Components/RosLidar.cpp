// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/ros/Utils.h>

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
    mResetLaserScan = true;
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

    ros_utils::addPrefix(mRosNodePrefix, mLaserScanPubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mPointCloudPubTopic, true);

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
    CARB_PROFILE_ZONE(0, "Lidar 2D Pub");

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
    setRosTimeStamp(laser_msg.header.stamp);

    const char* lidarPathStr = mLidarPath.GetString().c_str();
    int numColsTicked = mLidarSensorInterface->getNumColsTicked(lidarPathStr);
    int numRows = mLidarSensorInterface->getNumRows(lidarPathStr); // should be 1
    if (numRows > 1)
    {
        CARB_LOG_ERROR("High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan");
    }
    size_t numBeams = numColsTicked * numRows;

    float* theta = mLidarSensorInterface->getAzimuthData(lidarPathStr);
    // float* phi = mLidarSensorInterface->getZenithData(lidarPathStr); // should have one entry
    float* ranges = mLidarSensorInterface->getLinearDepthData(lidarPathStr);
    uint8_t* intensities = mLidarSensorInterface->getIntensityData(lidarPathStr);

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
        CARB_LOG_ERROR("Lidar Prim %s: Horizontal Resolution must be greater than 0.0", lidarPathStr);
        return;
    }
    if (horizontalFov == 0.0)
    {
        CARB_LOG_ERROR("Lidar Prim %s: Horizontal FOV must be greater than 0.0", lidarPathStr);
        return;
    }

    if (mResetLaserScan)
    {
        mIntensitiesData.clear();
        mRangesData.clear();
        mNumBeamsRemaining = numBeamsTotal;
        mAngleMin = std::min(theta[0], theta[numColsTicked - 1]);
        mPrevRotationRate = rotationRate;
        mPrevHorizontalResolution = horizontalResolution;
        mPrevHorizontalFov = horizontalFov;
        mResetLaserScan = false;
    }

    if (mPrevRotationRate != rotationRate || mPrevHorizontalResolution != horizontalResolution ||
        mPrevHorizontalFov != horizontalFov)
    {
        mIntensitiesData.clear();
        mRangesData.clear();
        mNumBeamsRemaining = numBeamsTotal;
        mPrevRotationRate = rotationRate;
        mPrevHorizontalResolution = horizontalResolution;

        if (mPrevHorizontalFov != horizontalFov)
        {
            mAngleMin = std::min(theta[0], theta[numColsTicked - 1]);
            mPrevHorizontalFov = horizontalFov;
        }
    }

    if (mNumBeamsRemaining > numBeams)
    {
        for (size_t i = 0; i < numBeams; i++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[i]));
            mRangesData.push_back(ranges[i]);
        }
        mNumBeamsRemaining -= numBeams;
    }

    else if (mNumBeamsRemaining <= numBeams)
    {

        // Save data up to maximum FOV
        size_t i;
        for (i = 0; i < mNumBeamsRemaining; i++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[i]));
            mRangesData.push_back(ranges[i]);
        }

        // Setup ROS Lidar Message
        laser_msg.angle_min = mAngleMin;
        laser_msg.angle_max = mAngleMin + (horizontalFov * M_PI / 180.0);


        laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
        laser_msg.range_min = minRange;
        laser_msg.range_max = maxRange;

        laser_msg.ranges = mRangesData;
        laser_msg.intensities = mIntensitiesData;

        laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
        laser_msg.time_increment = (horizontalFov / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

        static_cast<rclcpp::Publisher<sensor_msgs::msg::LaserScan, std::allocator<void>>*>(pub)->publish(laser_msg);

        // Reset fields for new ROS Lidar message
        mRangesData.clear();
        mIntensitiesData.clear();

        // Save remaining data
        size_t numBeamsOffset = numBeams - mNumBeamsRemaining;
        for (size_t j = 0; j < numBeamsOffset; j++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[i]));
            mRangesData.push_back(ranges[i]);
            i++;
        }
        mNumBeamsRemaining = numBeamsTotal - numBeamsOffset;
    }
}

void RosLidar::pointCloudPubCallback(rclcpp::PublisherBase* pub)
{
    CARB_PROFILE_ZONE(0, "Lidar Point Cloud Pub");
    if (!mEnablePointCloud)
    {
        return;
    }
    float maxRange = 100;
    float minRange = 0.4;
    float rotationRate = 0.0;
    float horizontalResolution = 0.4;
    float horizontalFov = 360;
    float verticalResolution = 4.0;
    float verticalFov = 40;

    isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalFovAttr(), horizontalFov);
    isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalResolutionAttr(), verticalResolution);
    isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalFovAttr(), verticalFov);


    const char* lidarPathStr = mLidarPath.GetString().c_str();

    carb::Float3* lidarData = mLidarSensorInterface->getPointCloud(lidarPathStr);
    float* theta = mLidarSensorInterface->getAzimuthData(lidarPathStr);
    float* ranges = mLidarSensorInterface->getLinearDepthData(lidarPathStr);

    int rows = mLidarSensorInterface->getNumRows(lidarPathStr);
    int numColsTicked = mLidarSensorInterface->getNumColsTicked(lidarPathStr);
    int numCols = mLidarSensorInterface->getNumCols(lidarPathStr);
    int numRows = mLidarSensorInterface->getNumRows(lidarPathStr);
    size_t numBeams = numColsTicked * numRows;


    if (mResetLaserScan)
    {
        mPointsData.clear();
        mNumBeamsRemaining = numCols * numRows;
        mAngleMin = std::min(theta[0], theta[numColsTicked - 1]);
        mPrevRotationRate = rotationRate;
        mPrevHorizontalResolution = horizontalResolution;
        mPrevHorizontalFov = horizontalFov;
        mPrevVerticalResolution = verticalResolution;
        mPrevVerticalFov = verticalFov;
        mResetLaserScan = false;
    }
    if (mPrevRotationRate != rotationRate || mPrevHorizontalResolution != horizontalResolution ||
        mPrevHorizontalFov != horizontalFov || mPrevVerticalResolution != verticalResolution ||
        mPrevVerticalFov != verticalFov)
    {
        mPointsData.clear();
        mNumBeamsRemaining = numCols * numRows;
        mPrevRotationRate = rotationRate;
        mPrevHorizontalResolution = horizontalResolution;
        mPrevVerticalResolution = verticalResolution;
        mPrevVerticalFov = verticalFov;
        if (mPrevHorizontalFov != horizontalFov)
        {
            mAngleMin = std::min(theta[0], theta[numColsTicked - 1]);
            mPrevHorizontalFov = horizontalFov;
        }
    }

    pcl::PointXYZ p;


    if (mNumBeamsRemaining > numBeams)
    {
        for (size_t i = 0; i < numBeams; i++)
        {

            if (ranges[i] >= maxRange)
            {
                continue;
            }
            p.x = lidarData[i].x * mUnitScale;
            p.y = lidarData[i].y * mUnitScale;
            p.z = lidarData[i].z * mUnitScale;

            mPointsData.push_back(p);
        }
        mNumBeamsRemaining -= numBeams;
    }
    else if (mNumBeamsRemaining <= numBeams)
    {

        // Save data up to maximum FOV
        size_t i = 0;
        for (i = 0; i < mNumBeamsRemaining; i++)
        {
            if (ranges[i] >= maxRange)
            {
                continue;
            }
            p.x = lidarData[i].x * mUnitScale;
            p.y = lidarData[i].y * mUnitScale;
            p.z = lidarData[i].z * mUnitScale;

            mPointsData.push_back(p);
        }
        sensor_msgs::msg::PointCloud2 point_cloud_msg;
        point_cloud_msg.is_dense = true;
        point_cloud_msg.header.frame_id = mFrameId;
        point_cloud_msg.height = 1;
        point_cloud_msg.point_step = sizeof(pcl::PointXYZ);
        point_cloud_msg.width = mPointsData.size();
        point_cloud_msg.row_step = point_cloud_msg.point_step * mPointsData.size();
        point_cloud_msg.data.resize(mPointsData.size() * sizeof(pcl::PointXYZ));

        std::memcpy(&point_cloud_msg.data[0], &mPointsData[0], mPointsData.size() * sizeof(pcl::PointXYZ));


        pcl::PCLPointCloud2 pcl_pc2;
        pcl_pc2.fields.clear();
        pcl::for_each_type<typename pcl::traits::fieldList<pcl::PointXYZ>::type>(
            pcl::detail::FieldAdder<pcl::PointXYZ>(pcl_pc2.fields));
        pcl_conversions::fromPCL(pcl_pc2.fields, point_cloud_msg.fields);

        setRosTimeStamp(point_cloud_msg.header.stamp);

        static_cast<rclcpp::Publisher<sensor_msgs::msg::PointCloud2, std::allocator<void>>*>(pub)->publish(
            point_cloud_msg);

        mPointsData.clear();
        // Save remaining data
        size_t numBeamsOffset = numBeams - mNumBeamsRemaining;
        for (size_t j = 0; j < numBeamsOffset; j++)
        {
            if (ranges[i] >= maxRange)
            {
                i++;
                continue;
            }
            p.x = lidarData[i].x * mUnitScale;
            p.y = lidarData[i].y * mUnitScale;
            p.z = lidarData[i].z * mUnitScale;

            mPointsData.push_back(p);
            i++;
        }
        mNumBeamsRemaining = numRows * numCols - numBeamsOffset;
    }
}


}
}
}
