// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <include/Ros2Node.h>

#include <OgnROS2SubscribeClockDatabase.h>

class OgnROS2SubscribeClock : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2SubscribeClockDatabase::sPerInstanceState<OgnROS2SubscribeClock>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2SubscribeClockDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeClock>();
        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }
        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }

            state.mMessage = state.mFactory->CreateClockMessage();


            state.mSubscriber =
                state.mFactory->CreateSubscriber(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                 state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.subscriberCallback(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2SubscribeClockDatabase::sPerInstanceState<OgnROS2SubscribeClock>(nodeObj, instanceId);
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
        // mCallback = nullptr;
        Ros2Node::reset();
    }

    bool subscriberCallback(OgnROS2SubscribeClockDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeClock>();


        // std::cout << "Subscriber callback..";

        if (state.mSubscriber->spin(state.mMessage->ptr()))
        {
            state.mMessage->setData(db.outputs.timeStamp());
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }

        return false;
    }

private:
    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2ClockMessage> mMessage = nullptr;
};

REGISTER_OGN_NODE()
