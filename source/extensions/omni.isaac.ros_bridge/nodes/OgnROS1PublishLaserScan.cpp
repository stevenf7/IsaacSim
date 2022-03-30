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

#include "omni/isaac/utils/UsdUtilities.h"
#include "sensor_msgs/LaserScan.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/ros/RosNode.h>
#include <rangeSensorSchema/lidar.h>

#include <OgnROS1PublishLaserScanDatabase.h>


class OgnROS1PublishLaserScan : public RosNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishLaserScanDatabase::sInternalState<OgnROS1PublishLaserScan>(nodeObj);

        state.mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();

        if (!state.mLidarSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
            return;
        }
    }

    static bool compute(OgnROS1PublishLaserScanDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();


        auto& state = db.internalState<OgnROS1PublishLaserScan>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeName()))
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
                state.mNodeHandle->advertise<sensor_msgs::LaserScan>(topicName, db.inputs.queueSize()));

            state.mLidarPrimPath = primPath;

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        state.publishLidar(db);
        return true;
    }


    void publishLidar(OgnROS1PublishLaserScanDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar 2D Pub");
        if (!mLidarSensorInterface->isLidarSensor(mLidarPrimPath))
        {
            db.logError("Invalid Lidar Reference, Prim is not registered with Lidar extension");
            return;
        }

        bool highLod = false;
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHighLodAttr(), highLod);

        if (highLod)
        {
            db.logError(
                "High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting or uncheck LaserScanEnabled");
            return;
        }
        sensor_msgs::LaserScan laser_msg;
        laser_msg.header.seq = 0;
        laser_msg.header.frame_id = mFrameId;

        int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPrimPath);
        int numRows = mLidarSensorInterface->getNumRows(mLidarPrimPath); // should be 1
        if (numRows > 1)
        {
            db.logError("High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan");
        }
        size_t numBeams = numColsTicked * numRows;

        float* theta = mLidarSensorInterface->getAzimuthData(mLidarPrimPath);
        // float* phi = mLidarSensorInterface->getZenithData(mLidarPrimPath); // should have one entry
        float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPrimPath);
        uint8_t* intensities = mLidarSensorInterface->getIntensityData(mLidarPrimPath);

        if (!theta || !ranges || !intensities)
        {
            return;
        }

        float maxRange = 100;
        float minRange = 0.4;
        float rotationRate = 0.0;
        float horizontalResolution = 0.4;
        float horizontalFov = 360.0;

        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetMaxRangeAttr(), maxRange);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetMinRangeAttr(), minRange);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalFovAttr(), horizontalFov);

        size_t numBeamsTotal = horizontalFov / horizontalResolution;

        if (horizontalResolution == 0.0)
        {
            db.logError("Lidar Prim %s: Horizontal Resolution must be greater than 0.0", mLidarPrimPath);
            return;
        }
        if (horizontalFov == 0.0)
        {
            db.logError("Lidar Prim %s: Horizontal FOV must be greater than 0.0", mLidarPrimPath);
            return;
        }
        if (horizontalFov > 360.0)
        {
            db.logError("Lidar Prim %s: Horizontal FOV must be less than or equal to 360.0", mLidarPrimPath);
            return;
        }

        uint64_t curr_sequence_num = mLidarSensorInterface->getSequenceNumber(mLidarPrimPath);

        if (curr_sequence_num < mPrevSequenceNumber)
        {
            mResetLaserScan = true;
            mPrevSequenceNumber = curr_sequence_num;
        }

        carb::Float2 azimuthRange = mLidarSensorInterface->getAzimuthRange(mLidarPrimPath);

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

            if (db.inputs.timeStamp() >= 0.0)
            {
                laser_msg.header.stamp.fromSec(db.inputs.timeStamp());
            }
            else
            {
                db.logWarning(
                    "Timestamp is invalid. Timestamp will be neglected for all published ROS LaserScan messages");
            }

            laser_msg.angle_min = azimuthRange.x;
            laser_msg.angle_max = azimuthRange.y;

            laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
            laser_msg.range_min = minRange;
            laser_msg.range_max = maxRange;

            laser_msg.ranges = mRangesData;
            laser_msg.intensities = mIntensitiesData;

            laser_msg.angle_increment = horizontalResolution * M_PI / 180.0;
            laser_msg.time_increment = (horizontalFov / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

            mPublisher->publish(laser_msg);

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

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishLaserScanDatabase::sInternalState<OgnROS1PublishLaserScan>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mResetLaserScan = true;
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;

    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;
    pxr::RangeSensorSchemaLidar mLidarPrim;

    const char* mLidarPrimPath = nullptr;

    std::string mFrameId = "sim_lidar";
    std::vector<float> mIntensitiesData;
    std::vector<float> mRangesData;

    uint64_t mPrevSequenceNumber = 0;

    bool mResetLaserScan = true;
    size_t mNumBeamsRemaining;

    float mPrevRotationRate;
    float mPrevHorizontalResolution;
    float mPrevHorizontalFov;

    size_t mBeamIdx = 0;
};

REGISTER_OGN_NODE()
