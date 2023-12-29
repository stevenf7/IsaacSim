// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }

            state.mMessage = state.mFactory->CreateSemanticLabelMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.publishSemanticLabels(db);
    }

    bool publishSemanticLabels(OgnROS2PublishSemanticLabelsDatabase& db)
    {

        auto& state = db.internalState<OgnROS2PublishSemanticLabels>();
        if (state.mPublisher.get()->get_subscription_count() != 0)
        {
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

            state.mMessage->fillData(json.dump());
            state.mPublisher.get()->publish(state.mMessage->ptr());
        }
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
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2SemanticLabelMessage> mMessage = nullptr;
};

REGISTER_OGN_NODE()
