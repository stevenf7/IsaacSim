// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "Eigen/Eigen"
#include "vision_msgs/Detection3DArray.h"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1PublishBbox3DDatabase.h>

struct Bbox3DData
{
    uint32_t semanticId;
    float x_min;
    float y_min;
    float z_min;
    float x_max;
    float y_max;
    float z_max;
    pxr::GfMatrix4f transform;
    float occlusionRatio;
};

class OgnROS1PublishBbox3D : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS1PublishBbox2DDatabase::sInternalState<ROS1PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS1PublishBbox3DDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishBbox3D>();
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
                state.mNodeHandle->advertise<vision_msgs::Detection3DArray>(topicName, db.inputs.queueSize()));

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox3DData);
        const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());

        vision_msgs::Detection3DArray msg;
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
            const Bbox3DData& box = bboxData[i];
            auto mat = pxr::GfMatrix4d(box.transform);
            auto transform = pxr::GfTransform(mat);

            auto trans = transform.GetTranslation();
            auto rot = transform.GetRotation().GetQuaternion();
            auto scale = transform.GetScale();

            msg.detections[i].bbox.center.position.x = trans[0];
            msg.detections[i].bbox.center.position.y = trans[1];
            msg.detections[i].bbox.center.position.z = trans[2];
            auto imag = rot.GetImaginary();

            msg.detections[i].bbox.center.orientation.x = imag[0];
            msg.detections[i].bbox.center.orientation.y = imag[1];
            msg.detections[i].bbox.center.orientation.z = imag[2];
            msg.detections[i].bbox.center.orientation.w = rot.GetReal();

            msg.detections[i].bbox.size.x = (box.x_max - box.x_min) * scale[0];
            msg.detections[i].bbox.size.y = (box.y_max - box.y_min) * scale[1];
            msg.detections[i].bbox.size.z = (box.z_max - box.z_min) * scale[2];
            msg.detections[i].results.resize(1);
            msg.detections[i].results[0].id = box.semanticId;
            msg.detections[i].results[0].score = 1.0;
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishBbox3DDatabase::sInternalState<OgnROS1PublishBbox3D>(nodeObj);
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
