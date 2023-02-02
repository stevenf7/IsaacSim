// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "Eigen/Eigen"
#include "vision_msgs/msg/detection3_d_array.hpp"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishBbox3DDatabase.h>

struct Bbox3DData
{
    uint32_t semanticId;
    float x_min;
    float y_min;
    float z_min;
    float x_max;
    float y_max;
    float z_max;
    float transform[16];
};

class OgnROS2PublishBbox3D : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sInternalState<ROS2PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS2PublishBbox3DDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishBbox3D>();
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
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!validateTopic(fullTopicName))
            {
                return false;
            }
            state.mPublisher = state.mNodeHandle->create_publisher<vision_msgs::msg::Detection3DArray>(
                topicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox3DData);
        const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());

        vision_msgs::msg::Detection3DArray msg;
        msg.header.frame_id = state.mFrameId;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS Image messages");
            return false;
        }

        msg.detections.resize(numBbox);
        for (size_t i = 0; i < numBbox; i++)
        {
            const Bbox3DData& box = bboxData[i];
            Eigen::Matrix4f mat(box.transform);
            auto transform = Eigen::Affine3f(mat);

            auto trans = transform.translation();
            auto rot = Eigen::Quaternionf(transform.rotation());

            msg.detections[i].bbox.center.position.x = trans.x();
            msg.detections[i].bbox.center.position.y = trans.y();
            msg.detections[i].bbox.center.position.z = trans.z();

            msg.detections[i].bbox.center.orientation.x = rot.x();
            msg.detections[i].bbox.center.orientation.y = rot.y();
            msg.detections[i].bbox.center.orientation.z = rot.z();
            msg.detections[i].bbox.center.orientation.w = rot.w();

            msg.detections[i].bbox.size.x = box.x_max - box.x_min;
            msg.detections[i].bbox.size.y = box.y_max - box.y_min;
            msg.detections[i].bbox.size.z = box.z_max - box.z_min;
            msg.detections[i].results.resize(1);
            msg.detections[i].results[0].id = std::to_string(box.semanticId);
            msg.detections[i].results[0].score = 1.0;
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishBbox3DDatabase::sInternalState<OgnROS2PublishBbox3D>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<vision_msgs::msg::Detection3DArray>> mPublisher;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
