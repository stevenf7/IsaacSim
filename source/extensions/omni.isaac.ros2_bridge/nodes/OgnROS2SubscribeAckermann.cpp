// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <include/Ros2Node.h>

#include <OgnROS2SubscribeAckermannDatabase.h>

using namespace omni::isaac::ros2_bridge;

class OgnROS2SubscribeAckermann : public Ros2Node
{
public:
    static bool compute(OgnROS2SubscribeAckermannDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeAckermann>();

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.m_subscriber)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createAckermannDriveStampedMessage();
            if (!state.m_message->getPtr())
            {
                CARB_LOG_ERROR("Unable to find AckermannDriveStamped message type");
                return false;
            }

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

            state.m_subscriber = state.m_factory->createSubscriber(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);
            return true;
        }

        return state.subscriberCallback(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeAckermannDatabase::sPerInstanceState<OgnROS2SubscribeAckermann>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_subscriber.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

    bool subscriberCallback(OgnROS2SubscribeAckermannDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeAckermann>();

        if (state.m_subscriber->spin(state.m_message->getPtr()))
        {
            std::string frameId;

            auto& timeStamp = db.outputs.timeStamp();
            auto& steeringAngle = db.outputs.steeringAngle();
            auto& steeringAngleVelocity = db.outputs.steeringAngleVelocity();
            auto& speed = db.outputs.speed();
            auto& acceleration = db.outputs.acceleration();
            auto& jerk = db.outputs.jerk();

            state.m_message->readData(
                timeStamp, frameId, steeringAngle, steeringAngleVelocity, speed, acceleration, jerk);

            db.outputs.frameId() = frameId;

            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }
        return false;
    }

private:
    std::shared_ptr<Ros2Subscriber> m_subscriber = nullptr;
    std::shared_ptr<Ros2AckermannDriveStampedMessage> m_message = nullptr;
};

REGISTER_OGN_NODE()
