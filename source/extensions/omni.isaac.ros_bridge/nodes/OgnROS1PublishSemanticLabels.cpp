// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "std_msgs/String.h"

#include <carb/graphics/GraphicsTypes.h>

#include <nlohmann/json.hpp>

#include <OgnROS1PublishSemanticLabelsDatabase.h>
#include <RosNode.h>
#include <string>

class OgnROS1PublishSemanticLabels : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = ROS1PublishBbox2DDatabase::sPerInstanceState<ROS1PublishBbox2D>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS1PublishSemanticLabelsDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS1PublishSemanticLabels>();
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
                state.mNodeHandle->advertise<std_msgs::String>(topicName, db.inputs.queueSize()));


            return true;
        }
        std_msgs::String msg;

        nlohmann::json json;
        ros::Time timeObj;
        timeObj.fromSec(db.inputs.timeStamp());

        std::stringstream ss;


        // idToLabels is used by semantics node
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
        json["time_stamp"]["secs"] = timeObj.sec;
        json["time_stamp"]["nsecs"] = timeObj.nsec;

        msg.data = json.dump();
        state.mPublisher->publish(msg);

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS1PublishSemanticLabelsDatabase::sPerInstanceState<OgnROS1PublishSemanticLabels>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::Publisher> mPublisher;
};

REGISTER_OGN_NODE()
