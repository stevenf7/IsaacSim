// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "std_msgs/msg/string.hpp"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2PublishSemanticLabelsDatabase.h>


class OgnROS2PublishSemanticLabels : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sInternalState<ROS2PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS2PublishSemanticLabelsDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishSemanticLabels>();
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
                state.mNodeHandle->create_publisher<std_msgs::msg::String>(topicName, db.inputs.queueSize());


            return true;
        }

        // size_t bytes = db.inputs.data().size();
        // size_t numBbox = bytes / sizeof(Bbox3DData);
        // const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());

        std_msgs::msg::String msg;

        msg.data = db.inputs.idToLabels();

        builtin_interfaces::msg::Time timeObj = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));

        std::stringstream ss;
        ss << ", \"time_stamp\": {\"sec\": \"" << timeObj.sec << "\", \"nanosec\": \"" << timeObj.nanosec << "\"}";

        if (msg.data[msg.data.size() - 1] == '}')
        {
            msg.data.insert(msg.data.size() - 1, ss.str());
        }
        else
        {
            db.logWarning("Invalid JSON format found. Omitting timestamp data.");
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishSemanticLabelsDatabase::sInternalState<OgnROS2PublishSemanticLabels>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<std_msgs::msg::String>> mPublisher;
};

REGISTER_OGN_NODE()
