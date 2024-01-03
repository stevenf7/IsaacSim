// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "sensor_msgs/LaserScan.h"

#include <OgnROS1PublishLaserScanDatabase.h>
#include <RosNode.h>


class OgnROS1PublishLaserScan : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1PublishLaserScanDatabase::sInternalState<OgnROS1PublishLaserScan>(nodeObj);
    // }

    static bool compute(OgnROS1PublishLaserScanDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishLaserScan>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::LaserScan>(topicName, db.inputs.queueSize()));

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        return state.publishLidar(db);
    }


    bool publishLidar(OgnROS1PublishLaserScanDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar 2D Pub");

        // Setup ROS Lidar Message
        sensor_msgs::LaserScan laser_msg;
        laser_msg.header.seq = 0;
        laser_msg.header.frame_id = mFrameId;
        size_t buffSize = db.inputs.numCols() * db.inputs.numRows();

        if (buffSize == 0)
        {
            return false;
        }
        if (db.inputs.numRows() != 1)
        {
            db.logError(
                "Number of rows (%d) must be equal to 1. High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting",
                db.inputs.numRows());
            return false;
        }

        if (db.inputs.timeStamp() >= 0.0)
        {
            laser_msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS LaserScan messages");
        }

        laser_msg.angle_min = db.inputs.azimuthRange()[0];
        laser_msg.angle_max = db.inputs.azimuthRange()[1];

        float rotationRate = db.inputs.rotationRate();
        laser_msg.scan_time = rotationRate ? 1.0 / rotationRate : 0;
        laser_msg.range_min = db.inputs.depthRange()[0];
        laser_msg.range_max = db.inputs.depthRange()[1];


        if (!db.inputs.linearDepthData.isValid() || !db.inputs.intensitiesData.isValid())
        {
            db.logError("Buffers are invalid");
            return false;
        }

        if (db.inputs.linearDepthData.size() != db.inputs.intensitiesData.size())
        {
            db.logError("Linear Depth data and Intensities data sizes do not match");
            return false;
        }

        if (buffSize != db.inputs.linearDepthData.size())
        {
            db.logError("Lidar data with %d rows and %d columns does not match input buffer array size of %d",
                        db.inputs.numRows(), db.inputs.numCols(), db.inputs.linearDepthData.size());
            return false;
        }

        laser_msg.ranges.resize(buffSize);
        laser_msg.ranges.assign(db.inputs.linearDepthData().begin(), db.inputs.linearDepthData().end());

        laser_msg.intensities.resize(buffSize);
        laser_msg.intensities.assign(db.inputs.intensitiesData().begin(), db.inputs.intensitiesData().end());

        laser_msg.angle_increment = db.inputs.horizontalResolution() * M_PI / 180.0;
        laser_msg.time_increment = (db.inputs.horizontalFov() / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

        mPublisher->publish(laser_msg);
        return true;
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishLaserScanDatabase::sInternalState<OgnROS1PublishLaserScan>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;

    std::string mFrameId = "sim_lidar";
};

REGISTER_OGN_NODE()
