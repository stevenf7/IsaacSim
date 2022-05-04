// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "sensor_msgs/image_encodings.hpp"
#include "sensor_msgs/msg/image.hpp"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishImageDatabase.h>

class OgnROS2PublishImage : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishImageDatabase::sInternalState<OgnROS2PublishImage>(nodeObj);
    // }

    static bool compute(OgnROS2PublishImageDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishImage>();
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
                state.mNodeHandle->create_publisher<sensor_msgs::msg::Image>(fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        // Setup ROS Image Message
        sensor_msgs::msg::Image msg;
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

        msg.width = db.inputs.width();
        msg.height = db.inputs.height();
        if (msg.width == 0 || msg.height == 0)
        {
            db.logError("Width %d or height %d is not valid", msg.width, msg.height);
            return false;
        }

        msg.encoding = db.tokenToString(db.inputs.encoding());

        int channels = 0;
        int bitDepth = 0;
        try
        {
            channels = sensor_msgs::image_encodings::numChannels(msg.encoding);
            bitDepth = sensor_msgs::image_encodings::bitDepth(msg.encoding);
        }
        catch (std::exception& e)
        {
            db.logError("%s", e.what());
            return false;
        }
        int byteDepth = bitDepth / 8;

        msg.step = msg.width * channels * byteDepth;

        size_t totalBytes = msg.step * msg.height;
        if (totalBytes != db.inputs.data().size())
        {
            db.logError(
                "image format with bit depth %d and expected size %d bytes does not match input buffer Size of %d bytes",
                bitDepth, totalBytes, db.inputs.data().size());
            return false;
        }

        msg.data.resize(db.inputs.data().size());
        msg.data.assign(db.inputs.data().begin(), db.inputs.data().end());
        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishImageDatabase::sInternalState<OgnROS2PublishImage>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::Image>> mPublisher = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
