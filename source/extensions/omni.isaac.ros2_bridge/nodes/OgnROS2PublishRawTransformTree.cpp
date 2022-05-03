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

#include "tf2_msgs/msg/tf_message.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishRawTransformTreeDatabase.h>

class OgnROS2PublishRawTransformTree : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state =
    //     OgnROS2PublishRawTransformTreeDatabase::sInternalState<OgnROS2PublishRawTransformTree>(nodeObj);

    // }

    static bool compute(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishRawTransformTree>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS TF publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!validateTopic(fullTopicName))
            {
                return false;
            }

            state.mPublisher =
                state.mNodeHandle->create_publisher<tf2_msgs::msg::TFMessage>(fullTopicName, db.inputs.queueSize());

            state.mParentFrameId = db.inputs.parentFrameId();
            state.mChildFrameId = db.inputs.childFrameId();

            return true;
        }

        state.publishTF(db);

        return true;
    }

    void publishTF(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        tf2_msgs::msg::TFMessage tfMsg;
        geometry_msgs::msg::TransformStamped msg;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS TF messages");
        }

        msg.header.frame_id = mParentFrameId;
        msg.child_frame_id = mChildFrameId;


        auto& translation = db.inputs.translation();
        msg.transform.translation.x = translation[0];
        msg.transform.translation.y = translation[1];
        msg.transform.translation.z = translation[2];

        auto& rotation = db.inputs.rotation();
        msg.transform.rotation.x = rotation.GetImaginary()[0];
        msg.transform.rotation.y = rotation.GetImaginary()[1];
        msg.transform.rotation.z = rotation.GetImaginary()[2];
        msg.transform.rotation.w = rotation.GetReal();

        tfMsg.transforms.push_back(msg);
        mPublisher->publish(tfMsg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishRawTransformTreeDatabase::sInternalState<OgnROS2PublishRawTransformTree>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<tf2_msgs::msg::TFMessage>> mPublisher = nullptr;

    std::string mParentFrameId = "odom";
    std::string mChildFrameId = "base_link";
};

REGISTER_OGN_NODE()
