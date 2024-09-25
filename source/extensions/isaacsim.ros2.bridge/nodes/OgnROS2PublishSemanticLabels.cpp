// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>

#include <include/Ros2Node.h>
#include <nlohmann/json.hpp>

#include <OgnROS2PublishSemanticLabelsDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2PublishSemanticLabels : public Ros2Node
{
public:
    static bool compute(OgnROS2PublishSemanticLabelsDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishSemanticLabels>();

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createSemanticLabelMessage();

            Ros2QoSProfile qos;
            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile == "")
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }

            state.m_publisher = state.m_factory->createPublisher(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);
            return true;
        }

        return state.publishSemanticLabels(db);
    }

    bool publishSemanticLabels(OgnROS2PublishSemanticLabelsDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishSemanticLabels>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return false;
        }

        nlohmann::json json;
        if (db.inputs.idToLabels().length() > 0)
        {
            json = nlohmann::json::parse(db.inputs.idToLabels());
        }
        else
        {
            for (size_t i = 0; i < db.inputs.ids().size(); i++)
            {
                std::string label = db.tokenToString(db.inputs.labels()[i]);
                if (label.rfind("class:", 0) == 0)
                {
                    label = label.erase(0, 6);
                    json[std::to_string(db.inputs.ids()[i])]["class"] = label;
                }
                else
                {
                    json[std::to_string(db.inputs.ids()[i])] = label;
                }
            }
        }
        json["time_stamp"] = {};
        const auto result =
            std::div(static_cast<int64_t>(db.inputs.timeStamp() * 1e9), static_cast<int64_t>(1000000000L));
        if (result.rem >= 0)
        {
            json["time_stamp"]["sec"] = static_cast<std::int32_t>(result.quot);
            json["time_stamp"]["nanosec"] = static_cast<std::uint32_t>(result.rem);
        }
        else
        {
            json["time_stamp"]["sec"] = static_cast<std::int32_t>(result.quot - 1);
            json["time_stamp"]["nanosec"] = static_cast<std::uint32_t>(1000000000L + result.rem);
        }

        state.m_message->writeData(json.dump());
        state.m_publisher.get()->publish(state.m_message->getPtr());

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2PublishSemanticLabelsDatabase::sPerInstanceState<OgnROS2PublishSemanticLabels>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2SemanticLabelMessage> m_message = nullptr;
};

REGISTER_OGN_NODE()
