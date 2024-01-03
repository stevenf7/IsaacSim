// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "rosgraph_msgs/Clock.h"

#include <OgnROS1PublishClockDatabase.h>
#include <RosNode.h>

class OgnROS1PublishClock : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1PublishClockDatabase::sInternalState<OgnROS1PublishClock>(nodeObj);
    // }

    static bool compute(OgnROS1PublishClockDatabase& db)
    {
        auto& state = db.internalState<OgnROS1PublishClock>();
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
                state.mNodeHandle->advertise<rosgraph_msgs::Clock>(topicName, db.inputs.queueSize()));
            return true;
        }

        // publish the input string to topic
        rosgraph_msgs::Clock time_msg;
        ros::Time t;
        t.fromSec(db.inputs.timeStamp());
        time_msg.clock = t;
        state.mPublisher.get()->publish(time_msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishClockDatabase::sInternalState<OgnROS1PublishClock>(nodeObj);
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
