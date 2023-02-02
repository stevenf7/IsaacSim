// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "vision_msgs/msg/detection2_d_array.hpp"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishBbox2DDatabase.h>

struct Bbox2DData
{
    uint32_t semanticId;
    int32_t x_min;
    int32_t y_min;
    int32_t x_max;
    int32_t y_max;
};

class OgnROS2PublishBbox2D : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sInternalState<ROS2PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS2PublishBbox2DDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishBbox2D>();
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
            state.mPublisher = state.mNodeHandle->create_publisher<vision_msgs::msg::Detection2DArray>(
                fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox2DData);
        const Bbox2DData* bboxData = reinterpret_cast<const Bbox2DData*>(db.inputs.data().data());

        vision_msgs::msg::Detection2DArray msg;
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
            const Bbox2DData& box = bboxData[i];

            msg.detections[i].bbox.center.theta = 0;
            msg.detections[i].bbox.center.position.x = (box.x_max + box.x_min) / 2.0;
            msg.detections[i].bbox.center.position.y = (box.y_max + box.y_min) / 2.0;
            msg.detections[i].bbox.size_x = box.x_max - box.x_min;
            msg.detections[i].bbox.size_y = box.y_max - box.y_min;
            msg.detections[i].results.resize(1);
            msg.detections[i].results[0].hypothesis.class_id = std::to_string(box.semanticId);
            msg.detections[i].results[0].hypothesis.score = 1.0;
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishBbox2DDatabase::sInternalState<OgnROS2PublishBbox2D>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<vision_msgs::msg::Detection2DArray>> mPublisher;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
