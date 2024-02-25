// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <include/Ros2Node.h>

#include <OgnROS2PublishAckermannDatabase.h>

class OgnROS2PublishAckermann : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2PublishAckermannDatabase::sPerInstanceState<OgnROS2PublishAckermann>(nodeObj,
    //     instanceId);
    // }

    static bool compute(OgnROS2PublishAckermannDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishAckermann>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {

            // Setup ROS AckermannDriveStamped publisher
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

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        state.publishAckermmanDrive(db);

        return true;
    }


    void publishAckermmanDrive(OgnROS2PublishAckermannDatabase& db)
    {

        auto& state = db.perInstanceState<OgnROS2PublishAckermann>();

        // Check if subscription count is 0
        if (!state.mPublisher.get()->get_subscription_count())
        {
            return;
        }

        state.mMessage->fillHeader(db.inputs.timeStamp(), db.inputs.frameId());
        state.mMessage->fillData(db.inputs.steeringAngle(), db.inputs.steeringAngleVelocity(), db.inputs.speed(),
                                 db.inputs.acceleration(), db.inputs.jerk());

        state.mPublisher.get()->publish(state.mMessage->ptr());
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishAckermannDatabase::sPerInstanceState<OgnROS2PublishAckermann>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2AckermannDriveStampedMessage> mMessage = nullptr;
};

REGISTER_OGN_NODE()
