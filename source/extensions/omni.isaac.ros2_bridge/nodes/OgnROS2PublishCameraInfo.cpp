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

#include "sensor_msgs/msg/camera_info.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishCameraInfoDatabase.h>


class OgnROS2PublishCameraInfo : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishCameraInfoDatabase::sInternalState<OgnROS2PublishCameraInfo>(nodeObj);
    // }

    static bool compute(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishCameraInfo>();

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
                state.mNodeHandle->create_publisher<sensor_msgs::msg::CameraInfo>(fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }


        sensor_msgs::msg::CameraInfo cam_info_msg;
        cam_info_msg.header.frame_id = state.mFrameId;

        if (db.inputs.timeStamp() >= 0.0)
        {
            cam_info_msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
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

        cam_info_msg.k = { fx, 0, cx, 0, fy, cy, 0, 0, 1 };

        cam_info_msg.p = { fx, 0, cx, db.inputs.stereoOffset()[0], 0, fy, cy, db.inputs.stereoOffset()[1], 0, 0, 1, 0 };

        cam_info_msg.distortion_model = db.tokenToString(db.inputs.projectionType());

        state.mPublisher->publish(cam_info_msg);

        return true;
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishCameraInfoDatabase::sInternalState<OgnROS2PublishCameraInfo>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::CameraInfo>> mPublisher = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
