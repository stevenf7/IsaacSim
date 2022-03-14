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

#include <omni/isaac/ros/Utils.h>

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

    mResetLaserScan = true;
    mResetPCL = true;

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
    ros_utils::addPrefix(mRosNodePrefix, mFrameId, false);

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
    CARB_PROFILE_ZONE(0, "Lidar 2D Pub");

    if (!mEnableLaserScan)
    {
        return;
    }

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

    bool highLod = false;
    isaac::utils::safeGetAttribute(mLidarPrim.GetHighLodAttr(), highLod);

    if (highLod)
    {
        CARB_LOG_ERROR(
            "High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting or uncheck LaserScanEnabled");
        return;
    }
    sensor_msgs::LaserScan laser_msg;
    laser_msg.header.seq = 0;
    laser_msg.header.frame_id = mFrameId;

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

    if (!theta || !ranges || !intensities)
    {
        return;
    }

    float maxRange = 100;
    float minRange = 0.4;
    float rotationRate = 0.0;
    float horizontalResolution = 0.4;
    float horizontalFov = 360.0;

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
    if (horizontalFov > 360.0)
    {
        CARB_LOG_ERROR("Lidar Prim %s: Horizontal FOV must be less than or equal to 360.0", lidarPathStr);
        return;
    }

    uint64_t curr_sequence_num = mLidarSensorInterface->getSequenceNumber(mLidarPath.GetString().c_str());

    if (curr_sequence_num < mPrevSequenceNumber)
    {
        mResetLaserScan = true;
        mPrevSequenceNumber = curr_sequence_num;
    }

    carb::Float2 azimuthRange = mLidarSensorInterface->getAzimuthRange(lidarPathStr);

    if (mResetLaserScan)
    {
        mIntensitiesData.clear();
        mRangesData.clear();
        mNumBeamsRemaining = numBeamsTotal;
        mPrevRotationRate = rotationRate;
        mPrevHorizontalResolution = horizontalResolution;
        mPrevHorizontalFov = horizontalFov;

        bool foundStart = false;
        for (mBeamIdx = 0; mBeamIdx < numBeams; mBeamIdx++)
        {
            if (theta[mBeamIdx] == azimuthRange.x)
            {
                foundStart = true;
                break;
            }
        }
        if (!foundStart)
        {
            return;
        }
        mResetLaserScan = false;
    }

    if (mNumBeamsRemaining > numBeams)
    {
        for (size_t i = mBeamIdx; i < numBeams; i++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[i]));
            mRangesData.push_back(ranges[i]);
            mNumBeamsRemaining--;
        }
        mBeamIdx = 0;
    }

    else if (mNumBeamsRemaining <= numBeams)
    {

        // Save data up to maximum FOV
        size_t idx;
        for (idx = 0; idx < mNumBeamsRemaining; idx++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[idx]));
            mRangesData.push_back(ranges[idx]);
        }

        // Setup ROS Lidar Message
        setRosTimeStamp(laser_msg.header.stamp);
        laser_msg.angle_min = azimuthRange.x;
        laser_msg.angle_max = azimuthRange.y;

        laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
        laser_msg.range_min = minRange;
        laser_msg.range_max = maxRange;

        laser_msg.ranges = mRangesData;
        laser_msg.intensities = mIntensitiesData;

        laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
        laser_msg.time_increment = (horizontalFov / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

        pub->publish(laser_msg);

        mPrevSequenceNumber = curr_sequence_num;

        // Reset fields for new ROS Lidar message
        mRangesData.clear();
        mIntensitiesData.clear();

        if (idx < numBeams)
        {
            if (theta[idx] != azimuthRange.x)
            {
                mResetLaserScan = true;
                return;
            }
        }

        // Save remaining data
        size_t numBeamsOffset = numBeams - mNumBeamsRemaining;
        for (size_t j = 0; j < numBeamsOffset; j++)
        {
            mIntensitiesData.push_back(static_cast<float>(intensities[idx]));
            mRangesData.push_back(ranges[idx]);
            idx++;
        }
        mNumBeamsRemaining = numBeamsTotal - numBeamsOffset;
    }
}

void RosLidar::pointCloudPubCallback(ros::Publisher* pub)
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

    if (!theta || !ranges || !lidarData)
    {
        return;
    }

    int rows = mLidarSensorInterface->getNumRows(lidarPathStr);
    int numColsTicked = mLidarSensorInterface->getNumColsTicked(lidarPathStr);
    int numCols = mLidarSensorInterface->getNumCols(lidarPathStr);
    int numRows = mLidarSensorInterface->getNumRows(lidarPathStr);
    size_t numBeams = numColsTicked * numRows;


    if (mResetPCL)
    {
        mPointsData.clear();
        mNumBeamsRemainingPCL = numCols * numRows;
        mPrevRotationRatePCL = rotationRate;
        mPrevHorizontalResolutionPCL = horizontalResolution;
        mPrevHorizontalFovPCL = horizontalFov;
        mPrevVerticalResolutionPCL = verticalResolution;
        mPrevVerticalFovPCL = verticalFov;
        mResetPCL = false;
    }
    if (mPrevRotationRatePCL != rotationRate || mPrevHorizontalResolutionPCL != horizontalResolution ||
        mPrevHorizontalFovPCL != horizontalFov || mPrevVerticalResolutionPCL != verticalResolution ||
        mPrevVerticalFovPCL != verticalFov)
    {
        mPointsData.clear();
        mNumBeamsRemainingPCL = numCols * numRows;
        mPrevRotationRatePCL = rotationRate;
        mPrevHorizontalResolutionPCL = horizontalResolution;
        mPrevVerticalResolutionPCL = verticalResolution;
        mPrevVerticalFovPCL = verticalFov;
        if (mPrevHorizontalFovPCL != horizontalFov)
        {
            mPrevHorizontalFovPCL = horizontalFov;
        }
    }

    pcl::PointXYZ p;


    if (mNumBeamsRemainingPCL > numBeams)
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
        mNumBeamsRemainingPCL -= numBeams;
    }
    else if (mNumBeamsRemainingPCL <= numBeams)
    {

        // Save data up to maximum FOV
        size_t i = 0;
        for (i = 0; i < mNumBeamsRemainingPCL; i++)
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
        sensor_msgs::PointCloud2 point_cloud_msg;
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

        pub->publish(point_cloud_msg);

        mPointsData.clear();
        // Save remaining data
        size_t numBeamsOffset = numBeams - mNumBeamsRemainingPCL;
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
        mNumBeamsRemainingPCL = numRows * numCols - numBeamsOffset;
    }
}


}
}
}
