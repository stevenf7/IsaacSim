// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "geometry_msgs/Point32.h"
#include "omni/isaac/utils/UsdUtilities.h"
#include "pcl_ros/point_cloud.h"
#include "sensor_msgs/PointCloud2.h"

#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/ros/RosNode.h>
#include <rangeSensorSchema/lidar.h>

#include <OgnROS1PublishPointCloudDatabase.h>


class OgnROS1PublishPointCloud : public RosNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishPointCloudDatabase::sInternalState<OgnROS1PublishPointCloud>(nodeObj);

        state.mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();

        if (!state.mLidarSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
            return;
        }
    }

    static bool compute(OgnROS1PublishPointCloudDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();


        auto& state = db.internalState<OgnROS1PublishPointCloud>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            const char* primPath = db.inputs.lidarPrim.path();

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            // Verify we have a valid lidar prim
            pxr::UsdPrim targetPrim = stage->GetPrimAtPath(pxr::SdfPath(primPath));
            if (!targetPrim.IsA<pxr::RangeSensorSchemaLidar>())
            {
                db.logError("Prim is not a Lidar Prim");
                return false;
            }

            state.mLidarPrim = pxr::RangeSensorSchemaLidar(targetPrim);

            if (!state.mLidarSensorInterface->isLidarSensor(primPath))
            {
                db.logError("Prim is not registered with Lidar extension");
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::PointCloud2>(topicName, db.inputs.queueSize()));

            state.mLidarPrimPath = primPath;

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);
            return true;
        }

        state.publishLidar(db);
        return true;
    }


    void publishLidar(OgnROS1PublishPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar Point Cloud Pub");

        float maxRange = 100;
        float minRange = 0.4;
        float rotationRate = 0.0;
        float horizontalResolution = 0.4;
        float horizontalFov = 360;
        float verticalResolution = 4.0;
        float verticalFov = 40;

        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalFovAttr(), horizontalFov);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalResolutionAttr(), verticalResolution);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalFovAttr(), verticalFov);


        carb::Float3* lidarData = mLidarSensorInterface->getPointCloud(mLidarPrimPath);
        float* theta = mLidarSensorInterface->getAzimuthData(mLidarPrimPath);
        float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPrimPath);

        if (!theta || !ranges || !lidarData)
        {
            return;
        }

        // int rows = mLidarSensorInterface->getNumRows(mLidarPrimPath);
        int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPrimPath);
        int numCols = mLidarSensorInterface->getNumCols(mLidarPrimPath);
        int numRows = mLidarSensorInterface->getNumRows(mLidarPrimPath);
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

            // Setup ROS PointCloud2 Message
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

            if (db.inputs.timeStamp() >= 0.0)
            {
                point_cloud_msg.header.stamp.fromSec(db.inputs.timeStamp());
            }
            else
            {
                db.logWarning(
                    "Timestamp is invalid. Timestamp will be neglected for all published ROS PointCloud2 messages");
            }

            mPublisher->publish(point_cloud_msg);

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

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishPointCloudDatabase::sInternalState<OgnROS1PublishPointCloud>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mResetPCL = true;
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;

    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;
    pxr::RangeSensorSchemaLidar mLidarPrim;

    const char* mLidarPrimPath = nullptr;

    std::string mFrameId = "sim_lidar";
    std::vector<pcl::PointXYZ> mPointsData;

    bool mResetPCL = true;
    size_t mNumBeamsRemainingPCL;

    float mPrevRotationRatePCL;
    float mPrevHorizontalResolutionPCL;
    float mPrevHorizontalFovPCL;
    float mPrevVerticalResolutionPCL;
    float mPrevVerticalFovPCL;

    double mUnitScale;
};

REGISTER_OGN_NODE()
