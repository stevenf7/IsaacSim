// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "std_msgs/String.h"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1PublishSemanticLabelsDatabase.h>


class OgnROS1PublishSemanticLabels : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS1PublishBbox2DDatabase::sInternalState<ROS1PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS1PublishSemanticLabelsDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishSemanticLabels>();
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

        // size_t bytes = db.inputs.data().size();
        // size_t numBbox = bytes / sizeof(Bbox3DData);
        // const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());
        std_msgs::String msg;

        msg.data = db.inputs.idToLabels();
        ros::Time timeObj;
        timeObj.fromSec(db.inputs.timeStamp());

        std::stringstream ss;
        ss << ", \"time_stamp\": {\"secs\": \"" << timeObj.sec << "\", \"nsecs\": \"" << timeObj.nsec << "\"}";

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
        auto& state = OgnROS1PublishSemanticLabelsDatabase::sInternalState<OgnROS1PublishSemanticLabels>(nodeObj);
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
