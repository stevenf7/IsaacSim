// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ackermann_msgs/AckermannDriveStamped.h"

#include <OgnROS1SubscribeAckermannDatabase.h>
#include <RosNode.h>

class OgnROS1SubscribeAckermann : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS1SubscribeAckermannDatabase::sPerInstanceState<OgnROS1SubscribeAckermann>(nodeObj,
    //     instanceId);
    // }

    static bool compute(OgnROS1SubscribeAckermannDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS1SubscribeAckermann>();
        state.m_nodeObj = db.abi_node();
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
            state.mCallback = [&state, &db](const ackermann_msgs::AckermannDriveStamped::ConstPtr& msg)
            { state.subCallback(msg, db); };

            state.mSubscriber =
                std::make_unique<ros::Subscriber>(state.mNodeHandle->subscribe<ackermann_msgs::AckermannDriveStamped>(
                    topicName, db.inputs.queueSize(), state.mCallback));
            return true;
        }

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS1SubscribeAckermannDatabase::sPerInstanceState<OgnROS1SubscribeAckermann>(nodeObj, instanceId);
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
        if (!m_nodeObj.iNode)
        {
            return;
        }
        GraphObj graphObj{ m_nodeObj.iNode->getGraph(m_nodeObj) };
        GraphContextObj context{ graphObj.iGraph->getDefaultGraphContext(graphObj) };

        // For acceleration
        AttributeObj accelerationAttr = m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:acceleration");
        auto accelerationHandle =
            accelerationAttr.iAttribute->getAttributeDataHandle(accelerationAttr, kAccordingToContextIndex);
        double* accelerationCommand = getDataW<double>(context, accelerationHandle);
        *accelerationCommand = 0.0;

        // For jerk
        AttributeObj jerkAttr = m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:jerk");
        auto jerkHandle = jerkAttr.iAttribute->getAttributeDataHandle(jerkAttr, kAccordingToContextIndex);
        double* jerkCommand = getDataW<double>(context, jerkHandle);
        *jerkCommand = 0.0;

        // For speed
        AttributeObj speedAttr = m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:speed");
        auto speedHandle = speedAttr.iAttribute->getAttributeDataHandle(speedAttr, kAccordingToContextIndex);
        double* speedCommand = getDataW<double>(context, speedHandle);
        *speedCommand = 0.0;

        // For steeringAngle
        AttributeObj steeringAngleAttr = m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:steeringAngle");
        auto steeringAngleHandle =
            steeringAngleAttr.iAttribute->getAttributeDataHandle(steeringAngleAttr, kAccordingToContextIndex);
        double* steeringAngleCommand = getDataW<double>(context, steeringAngleHandle);
        *steeringAngleCommand = 0.0;

        // For steeringAngleVelocity
        AttributeObj steeringAngleVelocityAttr =
            m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:steeringAngleVelocity");
        auto steeringAngleVelocityHandle = steeringAngleVelocityAttr.iAttribute->getAttributeDataHandle(
            steeringAngleVelocityAttr, kAccordingToContextIndex);
        double* steeringAngleVelocityCommand = getDataW<double>(context, steeringAngleVelocityHandle);
        *steeringAngleVelocityCommand = 0.0;

        // For timeStamp
        AttributeObj timeStampAttr = m_nodeObj.iNode->getAttribute(m_nodeObj, "outputs:timeStamp");
        auto timeStampHandle = timeStampAttr.iAttribute->getAttributeDataHandle(timeStampAttr, kAccordingToContextIndex);
        double* timeStampCommand = getDataW<double>(context, timeStampHandle);
        *timeStampCommand = 0.0;

        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        RosNode::reset();
    }

    void subCallback(const ackermann_msgs::AckermannDriveStamped::ConstPtr& msg, OgnROS1SubscribeAckermannDatabase& db)
    {
        auto& frameId = db.outputs.frameId();
        auto& timeStamp = db.outputs.timeStamp();
        auto& steeringAngle = db.outputs.steeringAngle();
        auto& steeringAngleVelocity = db.outputs.steeringAngleVelocity();
        auto& speed = db.outputs.speed();
        auto& acceleration = db.outputs.acceleration();
        auto& jerk = db.outputs.jerk();

        frameId = msg->header.frame_id;
        timeStamp = msg->header.stamp.toSec();
        steeringAngle = msg->drive.steering_angle;
        steeringAngleVelocity = msg->drive.steering_angle_velocity;
        speed = msg->drive.speed;
        acceleration = msg->drive.acceleration;
        jerk = msg->drive.jerk;


        db.outputs.execOut() = kExecutionAttributeStateEnabled;
    }


private:
    std::unique_ptr<ros::Subscriber> mSubscriber;
    std::function<void(const ackermann_msgs::AckermannDriveStamped::ConstPtr&)> mCallback;
    NodeObj m_nodeObj;
};

REGISTER_OGN_NODE()
