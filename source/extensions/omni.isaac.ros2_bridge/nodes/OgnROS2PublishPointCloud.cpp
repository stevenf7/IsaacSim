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
#include "pcl_conversions/pcl_conversions.h"
#include "sensor_msgs/msg/point_cloud2.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishPointCloudDatabase.h>


class OgnROS2PublishPointCloud : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishPointCloudDatabase::sInternalState<OgnROS2PublishPointCloud>(nodeObj);
    // }

    static bool compute(OgnROS2PublishPointCloudDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishPointCloud>();

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
                state.mNodeHandle->create_publisher<sensor_msgs::msg::PointCloud2>(fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        state.publishLidar(db);
        return true;
    }


    void publishLidar(OgnROS2PublishPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar Point Cloud Pub");

        if (!db.inputs.pointCloudData.isValid())
        {
            db.logError("Buffer is invalid");
            return;
        }
        // Setup ROS PointCloud2 Message
        sensor_msgs::msg::PointCloud2 point_cloud_msg;
        point_cloud_msg.is_dense = true;
        point_cloud_msg.header.frame_id = mFrameId;
        point_cloud_msg.height = 1;
        point_cloud_msg.point_step = sizeof(GfVec3f);
        point_cloud_msg.width = db.inputs.pointCloudData.size();
        point_cloud_msg.row_step = point_cloud_msg.point_step * db.inputs.pointCloudData.size();
        point_cloud_msg.data.resize(db.inputs.pointCloudData.size() * sizeof(GfVec3f));

        std::memcpy(&point_cloud_msg.data[0], db.inputs.pointCloudData().data(),
                    db.inputs.pointCloudData.size() * sizeof(GfVec3f));

        pcl::PCLPointCloud2 pcl_pc2;
        pcl_pc2.fields.clear();
        pcl::for_each_type<typename pcl::traits::fieldList<pcl::PointXYZ>::type>(
            pcl::detail::FieldAdder<pcl::PointXYZ>(pcl_pc2.fields));
        pcl_conversions::fromPCL(pcl_pc2.fields, point_cloud_msg.fields);

        if (db.inputs.timeStamp() >= 0.0)
        {
            point_cloud_msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS PointCloud2 messages");
        }

        mPublisher->publish(point_cloud_msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishPointCloudDatabase::sInternalState<OgnROS2PublishPointCloud>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::PointCloud2>> mPublisher = nullptr;

    std::string mFrameId = "sim_lidar";
};

REGISTER_OGN_NODE()
