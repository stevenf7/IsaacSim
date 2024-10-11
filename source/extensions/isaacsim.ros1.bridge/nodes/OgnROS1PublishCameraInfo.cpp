// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "sensor_msgs/CameraInfo.h"

#include <OgnROS1PublishCameraInfoDatabase.h>
#include <RosNode.h>


class OgnROS1PublishCameraInfo : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS1PublishCameraInfoDatabase::sPerInstanceState<OgnROS1PublishCameraInfo>(nodeObj,
    //     instanceId);
    // }

    static bool compute(OgnROS1PublishCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS1PublishCameraInfo>();

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
                state.mNodeHandle->advertise<sensor_msgs::CameraInfo>(topicName, db.inputs.queueSize()));

            state.mFrameId = db.inputs.frameId();
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }


        sensor_msgs::CameraInfo cam_info_msg;
        cam_info_msg.header.seq = 0;
        cam_info_msg.header.frame_id = state.mFrameId;

        if (db.inputs.timeStamp() >= 0.0)
        {
            cam_info_msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS CameraInfo messages");
        }

        auto& height = db.inputs.height();
        auto& width = db.inputs.width();

        cam_info_msg.height = height;
        cam_info_msg.width = width;


        // ROS image: conventions
        // origin of frame should be optical center of camera
        // +x should point to the right in the image
        // +y should point down in the image
        // +z should point into the plane of the image

        float fx, fy, cy, cx;

        fx = width * db.inputs.focalLength() / db.inputs.horizontalAperture();
        fy = height * db.inputs.focalLength() / db.inputs.verticalAperture();
        cx = width * 0.5f;
        cy = height * 0.5f;

        cam_info_msg.K = { fx, 0, cx, 0, fy, cy, 0, 0, 1 };

        cam_info_msg.P = { fx, 0, cx, db.inputs.stereoOffset()[0] * fx, 0, fy, cy, db.inputs.stereoOffset()[1] * fy, 0,
                           0,  1, 0 };

        cam_info_msg.R = { 1, 0, 0, 0, 1, 0, 0, 0, 1 };


        std::string physicalDistortion = db.tokenToString(db.inputs.physicalDistortionModel());

        if (physicalDistortion.length() > 0)
        {
            for (size_t i = 0; i < db.inputs.physicalDistortionCoefficients().size(); i++)
            {
                cam_info_msg.D.push_back(db.inputs.physicalDistortionCoefficients()[i]);
            }

            cam_info_msg.distortion_model = physicalDistortion;
        }
        else
        {
            // TODO: Handle fisheye coeffieicents?
            cam_info_msg.distortion_model = db.tokenToString(db.inputs.projectionType());
        }

        state.mPublisher->publish(cam_info_msg);

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishCameraInfoDatabase::sPerInstanceState<OgnROS1PublishCameraInfo>(nodeObj, instanceId);
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
