// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <include/Ros2Node.h>

#include <OgnROS2SubscribeTwistDatabase.h>

class OgnROS2SubscribeTwist : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2SubscribeTwistDatabase::sPerInstanceState<OgnROS2SubscribeTwist>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2SubscribeTwistDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeTwist>();
        state.nodeObj = db.abi_node();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateTwistMessage();

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
            state.mSubscriber = state.mFactory->CreateSubscriber(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);


            return true;
        }

        return state.subscriberCallback(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2SubscribeTwistDatabase::sPerInstanceState<OgnROS2SubscribeTwist>(nodeObj, instanceId);
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
        GraphObj graphObj{ nodeObj.iNode->getGraph(nodeObj) };
        GraphContextObj context{ graphObj.iGraph->getDefaultGraphContext(graphObj) };

        AttributeObj linearAttr = nodeObj.iNode->getAttribute(nodeObj, "outputs:linearVelocity");
        auto linearHandle = linearAttr.iAttribute->getAttributeDataHandle(linearAttr, kAccordingToContextIndex);
        double* linearCommand = getDataW<double>(context, linearHandle);
        linearCommand[0] = 0.0;
        linearCommand[1] = 0.0;
        linearCommand[2] = 0.0;

        AttributeObj angularAttr = nodeObj.iNode->getAttribute(nodeObj, "outputs:angularVelocity");
        auto angularHandle = angularAttr.iAttribute->getAttributeDataHandle(angularAttr, kAccordingToContextIndex);
        double* angularCommand = getDataW<double>(context, angularHandle);
        angularCommand[0] = 0.0;
        angularCommand[1] = 0.0;
        angularCommand[2] = 0.0;


        mSubscriber.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


    bool subscriberCallback(OgnROS2SubscribeTwistDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeTwist>();


        if (state.mSubscriber->spin(state.mMessage->ptr()))
        {
            auto& linVel = db.outputs.linearVelocity();
            auto& angVel = db.outputs.angularVelocity();

            state.mMessage->getData(linVel, angVel);
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }

        return false;
    }

private:
    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2TwistMessage> mMessage = nullptr;
    NodeObj nodeObj;
};

REGISTER_OGN_NODE()
