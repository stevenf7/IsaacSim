// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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
#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include "pcl_ros/point_cloud.h"
#undef BOOST_BIND_GLOBAL_PLACEHOLDERS
#include "sensor_msgs/PointCloud2.h"

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1PublishPointCloudDatabase.h>


class OgnROS1PublishPointCloud : public RosNode
{
public:
    static bool compute(OgnROS1PublishPointCloudDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishPointCloud>();

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
                state.mNodeHandle->advertise<sensor_msgs::PointCloud2>(topicName, db.inputs.queueSize()));

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

        if (!db.inputs.pointCloudData.isValid())
        {
            db.logError("Buffer is invalid");
            return;
        }
        // Setup ROS PointCloud2 Message
        sensor_msgs::PointCloud2 point_cloud_msg;
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
            point_cloud_msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS PointCloud2 messages");
        }

        mPublisher->publish(point_cloud_msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishPointCloudDatabase::sInternalState<OgnROS1PublishPointCloud>(nodeObj);
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
