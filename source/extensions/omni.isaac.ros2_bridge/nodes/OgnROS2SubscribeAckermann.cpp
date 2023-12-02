// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <include/Ros2Node.h>

#include <OgnROS2SubscribeAckermannDatabase.h>

class OgnROS2SubscribeAckermann : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2SubscribeAckermannDatabase::sInternalState<OgnROS2SubscribeAckermann>(nodeObj);
    // }

    static bool compute(OgnROS2SubscribeAckermannDatabase& db)
    {
        auto& state = db.internalState<OgnROS2SubscribeAckermann>();
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

            state.mMessage = state.mFactory->CreateAckermannDriveStampedMessage();

            if (!state.mMessage->ptr())
            {
                CARB_LOG_ERROR("Unable to find AckermannDriveStamped message type");
                return false;
            }

            state.mSubscriber =
                state.mFactory->CreateSubscriber(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                 state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.subscriberCallback(db);
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeAckermannDatabase::sInternalState<OgnROS2SubscribeAckermann>(nodeObj);
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
        Ros2Node::reset();
    }


    bool subscriberCallback(OgnROS2SubscribeAckermannDatabase& db)
    {
        auto& state = db.internalState<OgnROS2SubscribeAckermann>();


        if (state.mSubscriber->spin(state.mMessage->ptr()))
        {

            std::string frameId;

            auto& timeStamp = db.outputs.timeStamp();
            auto& steeringAngle = db.outputs.steeringAngle();
            auto& steeringAngleVelocity = db.outputs.steeringAngleVelocity();
            auto& speed = db.outputs.speed();
            auto& acceleration = db.outputs.acceleration();
            auto& jerk = db.outputs.jerk();

            state.mMessage->getData(frameId, timeStamp, steeringAngle, steeringAngleVelocity, speed, acceleration, jerk);

            db.outputs.frameId() = frameId;

            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }

        return false;
    }

private:
    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2AckermannDriveStampedMessage> mMessage = nullptr;
};

REGISTER_OGN_NODE()
