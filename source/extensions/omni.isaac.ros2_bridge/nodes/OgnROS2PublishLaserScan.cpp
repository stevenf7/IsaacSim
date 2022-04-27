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

#include "sensor_msgs/msg/laser_scan.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishLaserScanDatabase.h>


class OgnROS2PublishLaserScan : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishLaserScanDatabase::sInternalState<OgnROS2PublishLaserScan>(nodeObj);
    // }

    static bool compute(OgnROS2PublishLaserScanDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishLaserScan>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!validateTopic(fullTopicName))
            {
                return false;
            }

            state.mPublisher =
                state.mNodeHandle->create_publisher<sensor_msgs::msg::LaserScan>(fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        state.publishLidar(db);
        return true;
    }


    void publishLidar(OgnROS2PublishLaserScanDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar 2D Pub");

        // Setup ROS Lidar Message
        sensor_msgs::msg::LaserScan laser_msg;
        laser_msg.header.frame_id = mFrameId;

        if (db.inputs.numRows() != 1)
        {
            db.logError(
                "Number of rows must be equal to 1. High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting");
            return;
        }

        if (db.inputs.timeStamp() >= 0.0)
        {
            laser_msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
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

        size_t buffSize = db.inputs.numCols() * db.inputs.numRows();

        if (!db.inputs.linearDepthData.isValid() || !db.inputs.intensitiesData.isValid())
        {
            db.logError("Buffers are invalid");
            return;
        }

        if (db.inputs.linearDepthData.size() != db.inputs.intensitiesData.size())
        {
            db.logError("Linear Depth data and Intensities data sizes do not match");
            return;
        }

        if (buffSize != db.inputs.linearDepthData.size())
        {
            db.logError("Lidar data with %d rows and %d columns does not match input buffer array size of %d",
                        db.inputs.numRows(), db.inputs.numCols(), db.inputs.linearDepthData.size());
            return;
        }

        laser_msg.ranges.resize(buffSize);
        laser_msg.ranges.assign(db.inputs.linearDepthData().begin(), db.inputs.linearDepthData().end());

        laser_msg.intensities.resize(buffSize);
        laser_msg.intensities.assign(db.inputs.intensitiesData().begin(), db.inputs.intensitiesData().end());

        laser_msg.angle_increment = db.inputs.horizontalResolution() * M_PI / 180.0;
        laser_msg.time_increment = (db.inputs.horizontalFov() / 360.0 * laser_msg.scan_time) / laser_msg.ranges.size();

        mPublisher->publish(laser_msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishLaserScanDatabase::sInternalState<OgnROS2PublishLaserScan>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::LaserScan>> mPublisher = nullptr;

    std::string mFrameId = "sim_lidar";
};

REGISTER_OGN_NODE()
