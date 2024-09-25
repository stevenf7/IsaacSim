// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>

#include <OgnROS2SubscribeJointStateDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2SubscribeJointState : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeJointStateDatabase::sPerInstanceState<OgnROS2SubscribeJointState>(nodeObj, instanceId);
        state.m_nodeObj = nodeObj;
    }

    static bool compute(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeJointState>();

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
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createJointStateMessage();

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

    bool subscriberCallback(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeJointState>();

        if (state.m_subscriber->spin(state.m_message->getPtr()))
        {
            size_t num_actuators = state.m_message->getNumJoints();
            if (num_actuators == 0)
            {
                db.logWarning("No joints found");
                return false;
            }

            // Check if all sub-message size match size of actuators before setting data
            if (state.m_message->checkValid())
            {
                db.outputs.positionCommand().resize(num_actuators);
                db.outputs.velocityCommand().resize(num_actuators);
                db.outputs.effortCommand().resize(num_actuators);
                db.outputs.jointNames().resize(num_actuators);

                state.m_message->readData(m_jointNames, db.outputs.positionCommand().data(),
                                          db.outputs.velocityCommand().data(), db.outputs.effortCommand().data(),
                                          db.outputs.timeStamp());

                for (size_t i = 0; i < num_actuators; i++)
                {
                    db.outputs.jointNames().at(i) = db.stringToToken(m_jointNames[i]);
                }

                db.outputs.execOut() = kExecutionAttributeStateEnabled;
            }
            else
            {
                db.logWarning("Please ensure size of position, velocity and effort arrays match the number of actuators");
                return false;
            }
        }
        return true;
    }

    static bool updateNodeVersion(const GraphContextObj& context, const NodeObj& nodeObj, int oldVersion, int newVersion)
    {
        if (oldVersion < newVersion)
        {
            const INode* const iNode = nodeObj.iNode;
            if (oldVersion < 2)
            {
                iNode->removeAttribute(nodeObj, "inputs:targetPrim");
            }
            return true;
        }
        return false;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeJointStateDatabase::sPerInstanceState<OgnROS2SubscribeJointState>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        auto db = OgnROS2SubscribeJointStateDatabase(m_nodeObj);

        db.outputs.jointNames.resize(0);
        db.outputs.positionCommand.resize(0);
        db.outputs.velocityCommand.resize(0);
        db.outputs.effortCommand.resize(0);

        m_subscriber.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Subscriber> m_subscriber = nullptr;
    std::shared_ptr<Ros2JointStateMessage> m_message = nullptr;

    // Names will be extracted as strings and later converted to tokens
    std::vector<char*> m_jointNames;

    NodeObj m_nodeObj;
};

REGISTER_OGN_NODE()
