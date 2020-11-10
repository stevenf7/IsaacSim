// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosLidar.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"
#include "geometry_msgs/Point32.h"
#include "sensor_msgs/LaserScan.h"
#include "sensor_msgs/PointCloud.h"
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

    mLidarInterface = mFramework->acquireInterface<omni::isaac::lidar::LidarInterface>();
    if (!mLidarInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::lidar interface");
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
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);

    onComponentChange();
}

void RosLidar::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosLidar& typedPrim = (pxr::RosBridgeSchemaRosLidar)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLaserScanPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPointCloudPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetLaserScanPubTopicAttr(), mLaserScanPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudPubTopicAttr(), mPointCloudPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetPointCloudEnabledAttr(), mEnablePointCloud);
    isaac::utils::safeGetAttribute(typedPrim.GetFrameIdAttr(), mFrameId);

    mRosNode->createPublisher<sensor_msgs::LaserScan>(
        mPrim.GetPath().GetString(), mLaserScanPubTopic, mQueueSize, &RosLidar::pubCallback, this);
    mRosNode->createPublisher<sensor_msgs::PointCloud>(
        mPrim.GetPath().GetString(), mPointCloudPubTopic, mQueueSize, &RosLidar::pointCloudPubCallback, this);


    pxr::SdfPathVector targets;
    typedPrim.GetLidarPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mLidarPath = targets[0];

    pxr::UsdPrim prim = mStage->GetPrimAtPath(targets[0]);
    if (!prim.IsA<pxr::LidarSchemaLidar>())
    {
        CARB_LOG_ERROR("Prim is not a Lidar Prim");
        return;
    }
    mLidarPrim = pxr::LidarSchemaLidar(prim);
    if (!mLidarInterface->isLidar(targets[0].GetString().c_str()))
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
    if (!mLidarInterface->isLidar(mLidarPath.GetString().c_str()))
    {
        CARB_LOG_ERROR("Invalid Lidar Reference, Prim is not registered with Lidar extension");
        return;
    }
    bool highLod = false;
    isaac::utils::safeGetAttribute(mLidarPrim.GetHighLodAttr(), highLod);
    if (highLod)
    {
        CARB_LOG_ERROR("High LOD not supported, only 2D Lidar Supported. Please disable High LOD setting");
        return;
    }
    sensor_msgs::LaserScan laser_msg;
    laser_msg.header.seq = 0;
    laser_msg.header.frame_id = mFrameId;
    laser_msg.header.stamp.fromSec(mTimeSeconds);

    int numColsTicked = mLidarInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    int numRows = mLidarInterface->getNumRows(mLidarPath.GetString().c_str()); // should be 1
    if (numRows > 1)
    {
        CARB_LOG_ERROR("High LOD not supported, only 2D Lidar Supported");
    }
    int numBeams = numColsTicked * numRows;

    float* theta = mLidarInterface->getAzimuthData(mLidarPath.GetString().c_str());
    float* phi = mLidarInterface->getZenithData(mLidarPath.GetString().c_str()); // should have one entry
    float* ranges = mLidarInterface->getLinearDepthData(mLidarPath.GetString().c_str());

    float maxRange = 100;
    float minRange = 0.4;
    float rotationRate = 20;
    float horizontalResolution = 0.4;

    isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
    isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
    isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);


    laser_msg.angle_min = theta[0];
    laser_msg.angle_max = theta[numColsTicked - 1];
    laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
    laser_msg.time_increment = mTimeDelta;
    laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
    laser_msg.range_min = minRange;
    laser_msg.range_max = maxRange;
    laser_msg.ranges.resize(numBeams);
    std::memcpy(laser_msg.ranges.data(), ranges, numBeams * sizeof(float));

    pub->publish(laser_msg);
}

void RosLidar::pointCloudPubCallback(ros::Publisher* pub)
{
    if (!mEnablePointCloud)
    {
        return;
    }
    sensor_msgs::PointCloud point_cloud_msg;
    point_cloud_msg.header.seq = 0;
    point_cloud_msg.header.frame_id = mFrameId;
    point_cloud_msg.header.stamp.fromSec(mTimeSeconds);

    carb::Float3* lidarData = mLidarInterface->getPointCloud(mLidarPath.GetString().c_str());
    int rows = mLidarInterface->getNumRows(mLidarPath.GetString().c_str());
    int numColsTicked = mLidarInterface->getNumColsTicked(mLidarPath.GetString().c_str());
    for (int i = 0; i < rows * numColsTicked; i++)
    {
        geometry_msgs::Point32 points;
        points.x = lidarData[i].x * mUnitScale;
        points.y = lidarData[i].y * mUnitScale;
        points.z = lidarData[i].z * mUnitScale;
        point_cloud_msg.points.push_back(points);
    }
    pub->publish(point_cloud_msg);
}


}
}
}
