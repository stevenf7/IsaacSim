// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "sensor_msgs/Image.h"
#include "sensor_msgs/image_encodings.h"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1PublishImageDatabase.h>

class OgnROS1PublishImage : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1PublishImageDatabase::sInternalState<OgnROS1PublishImage>(nodeObj);
    // }

    static bool compute(OgnROS1PublishImageDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishImage>();
        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }
        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            const std::string& topicName = db.inputs.topicName();
            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::Image>(topicName, db.inputs.queueSize()));

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        // publish the input string to topic
        sensor_msgs::Image msg;
        msg.header.seq = 0;
        msg.header.frame_id = state.mFrameId;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
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
        if (totalBytes != db.inputs.data.size())
        {
            db.logError(
                "image format with bit depth %d and expected size %d bytes does not match input buffer Size of %d bytes",
                bitDepth, totalBytes, db.inputs.data.size());
            return false;
        }

        msg.data.resize(totalBytes);

        const uint8_t* pointsAsCpu = reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data());

        memcpy(&msg.data[0], &pointsAsCpu[0], totalBytes);

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishImageDatabase::sInternalState<OgnROS1PublishImage>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::Publisher> mPublisher;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
