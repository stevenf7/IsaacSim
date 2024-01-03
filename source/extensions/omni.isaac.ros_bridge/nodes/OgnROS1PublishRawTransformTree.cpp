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

#include "tf2_msgs/TFMessage.h"

#include <OgnROS1PublishRawTransformTreeDatabase.h>
#include <RosNode.h>

class OgnROS1PublishRawTransformTree : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state =
    //     OgnROS1PublishRawTransformTreeDatabase::sInternalState<OgnROS1PublishRawTransformTree>(nodeObj);

    // }

    static bool compute(OgnROS1PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishRawTransformTree>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS TF publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<tf2_msgs::TFMessage>(topicName, db.inputs.queueSize()));


            state.mParentFrameId = db.inputs.parentFrameId();
            state.mChildFrameId = db.inputs.childFrameId();

            addFramePrefix(db.inputs.nodeNamespace(), state.mParentFrameId);
            addFramePrefix(db.inputs.nodeNamespace(), state.mChildFrameId);

            return true;
        }

        state.publishTF(db);

        return true;
    }

    void publishTF(OgnROS1PublishRawTransformTreeDatabase& db)
    {
        tf2_msgs::TFMessage tfMsg;
        geometry_msgs::TransformStamped msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
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
        auto& state = OgnROS1PublishRawTransformTreeDatabase::sInternalState<OgnROS1PublishRawTransformTree>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;

    std::string mParentFrameId = "odom";
    std::string mChildFrameId = "base_link";
};

REGISTER_OGN_NODE()
