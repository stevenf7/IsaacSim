// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "rosgraph_msgs/Clock.h"

#include <OgnROS1SubscribeClockDatabase.h>
#include <RosNode.h>

class OgnROS1SubscribeClock : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS1SubscribeClockDatabase::sPerInstanceState<OgnROS1SubscribeClock>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS1SubscribeClockDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS1SubscribeClock>();
        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }
        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            const std::string& topicName = db.inputs.topicName();
            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mCallback = [&state, &db](const rosgraph_msgs::Clock::ConstPtr& msg) { state.subCallback(msg, db); };

            state.mSubscriber = std::make_unique<ros::Subscriber>(
                state.mNodeHandle->subscribe<rosgraph_msgs::Clock>(topicName, db.inputs.queueSize(), state.mCallback));
            return true;
        }

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1SubscribeClockDatabase::sPerInstanceState<OgnROS1SubscribeClock>(nodeObj, instanceId);
        state.reset();
    }

    /**
     * @brief Reset the node
     * Note that we need to reset the subscriber first so it doesn't get called again, then the callback, and then call
     * the base class reset
     *
     */
    virtual void reset()
    {
        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        RosNode::reset();
    }

    void subCallback(const rosgraph_msgs::Clock::ConstPtr& msg, OgnROS1SubscribeClockDatabase& db)
    {
        db.outputs.timeStamp() = msg->clock.toSec();
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
    }


private:
    std::unique_ptr<ros::Subscriber> mSubscriber;
    std::function<void(const rosgraph_msgs::Clock::ConstPtr&)> mCallback;
};

REGISTER_OGN_NODE()
