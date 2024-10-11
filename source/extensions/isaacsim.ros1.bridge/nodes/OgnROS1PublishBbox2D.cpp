// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "vision_msgs/Detection2DArray.h"

#include <carb/graphics/GraphicsTypes.h>

#include <OgnROS1PublishBbox2DDatabase.h>
#include <RosNode.h>

struct Bbox2DData
{
    uint32_t semanticId;
    int32_t x_min;
    int32_t y_min;
    int32_t x_max;
    int32_t y_max;
    float occlusionRatio;
};

class OgnROS1PublishBbox2D : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = ROS1PublishBbox2DDatabase::sPerInstanceState<ROS1PublishBbox2D>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS1PublishBbox2DDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS1PublishBbox2D>();
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
                state.mNodeHandle->advertise<vision_msgs::Detection2DArray>(topicName, db.inputs.queueSize()));

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox2DData);
        const Bbox2DData* bboxData = reinterpret_cast<const Bbox2DData*>(db.inputs.data().data());

        vision_msgs::Detection2DArray msg;
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

        msg.detections.resize(numBbox);
        for (size_t i = 0; i < numBbox; i++)
        {
            const Bbox2DData& box = bboxData[i];

            msg.detections[i].bbox.center.theta = 0;
            msg.detections[i].bbox.center.x = (box.x_max + box.x_min) / 2.0;
            msg.detections[i].bbox.center.y = (box.y_max + box.y_min) / 2.0;
            msg.detections[i].bbox.size_x = box.x_max - box.x_min;
            msg.detections[i].bbox.size_y = box.y_max - box.y_min;
            msg.detections[i].results.resize(1);
            msg.detections[i].results[0].id = box.semanticId;
            msg.detections[i].results[0].score = 1.0;
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishBbox2DDatabase::sPerInstanceState<OgnROS1PublishBbox2D>(nodeObj, instanceId);
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
