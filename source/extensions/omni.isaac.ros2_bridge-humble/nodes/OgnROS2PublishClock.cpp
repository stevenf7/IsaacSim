// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "rosgraph_msgs/msg/clock.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishClockDatabase.h>

class OgnROS2PublishClock : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishClockDatabase::sInternalState<OgnROS2PublishClock>(nodeObj);
    // }

    static bool compute(OgnROS2PublishClockDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishClock>();
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

            state.mPublisher =
                state.mNodeHandle->create_publisher<rosgraph_msgs::msg::Clock>(fullTopicName, db.inputs.queueSize());
            return true;
        }

        // publish the input string to topic
        rosgraph_msgs::msg::Clock time_msg;
        time_msg.clock = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));

        state.mPublisher.get()->publish(time_msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishClockDatabase::sInternalState<OgnROS2PublishClock>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<rosgraph_msgs::msg::Clock>> mPublisher = nullptr;
};

REGISTER_OGN_NODE()
