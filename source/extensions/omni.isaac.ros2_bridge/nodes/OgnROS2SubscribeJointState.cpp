// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>

#include <OgnROS2SubscribeJointStateDatabase.h>


class OgnROS2SubscribeJointState : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeJointStateDatabase::sPerInstanceState<OgnROS2SubscribeJointState>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;
    }

    static bool compute(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeJointState>();

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
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateJointStateMessage();

            state.mSubscriber =
                state.mFactory->CreateSubscriber(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                 state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.subscriberCallback(db);

        // return true;
    }


    bool subscriberCallback(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeJointState>();


        if (state.mSubscriber->spin(state.mMessage->ptr()))
        {
            size_t num_actuators = 0;
            state.mMessage->getActuators(num_actuators);

            if (num_actuators == 0)
            {
                db.logWarning("No joints found");
                return false;
            }

            // Check if all sub-message size match size of actuators before setting data
            if (state.mMessage->checkValid())
            {
                db.outputs.positionCommand().resize(num_actuators);
                db.outputs.velocityCommand().resize(num_actuators);
                db.outputs.effortCommand().resize(num_actuators);
                db.outputs.jointNames().resize(num_actuators);

                state.mMessage->getData(mJointNames, db.outputs.positionCommand().data(),
                                        db.outputs.velocityCommand().data(), db.outputs.effortCommand().data(),
                                        db.outputs.timeStamp());

                for (size_t i = 0; i < num_actuators; i++)
                {
                    db.outputs.jointNames().at(i) = db.stringToToken(mJointNames[i]);
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


    // void subCallback(const sensor_msgs::msg::JointState::SharedPtr& msg, OgnROS2SubscribeJointStateDatabase& db)
    // {
    //     const size_t num_actuators = msg->name.size();

    //     if (num_actuators == 0)
    //     {
    //         db.logWarning("No joints found");
    //         return;
    //     }

    //     db.outputs.jointNames().resize(num_actuators);

    //     // Copy joint names and convert to token array
    //     std::transform(msg->name.begin(), msg->name.end(), db.outputs.jointNames().begin(),
    //                    [db](std::string name) { return db.stringToToken(name.c_str()); });

    //     if (msg->position.size() > 0)
    //     {
    //         if (msg->position.size() != num_actuators)
    //         {
    //             db.logError("size of joint position array does not match number of joints");
    //             return;
    //         }
    //         db.outputs.positionCommand().resize(num_actuators);
    //         std::memcpy(db.outputs.positionCommand().data(), msg->position.data(), num_actuators * sizeof(double));
    //     }
    //     else
    //     {
    //         db.outputs.positionCommand().resize(0);
    //     }

    //     if (msg->velocity.size() != 0)
    //     {
    //         if (msg->velocity.size() != num_actuators)
    //         {
    //             db.logError("size of joint velocity array does not match number of joints");
    //             return;
    //         }
    //         db.outputs.velocityCommand().resize(num_actuators);
    //         std::memcpy(db.outputs.velocityCommand().data(), msg->velocity.data(), num_actuators * sizeof(double));
    //     }
    //     else
    //     {
    //         db.outputs.velocityCommand().resize(0);
    //     }

    //     if (msg->effort.size() != 0)
    //     {
    //         if (msg->effort.size() != num_actuators)
    //         {
    //             db.logError("size of effort array does not match number of joints");
    //             return;
    //         }

    //         db.outputs.effortCommand().resize(num_actuators);
    //         std::memcpy(db.outputs.effortCommand().data(), msg->effort.data(), num_actuators * sizeof(double));
    //     }
    //     else
    //     {
    //         db.outputs.effortCommand().resize(0);
    //     }


    //     db.outputs.execOut() = kExecutionAttributeStateEnabled;
    // }

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
        auto db = OgnROS2SubscribeJointStateDatabase(mNodeObj);

        db.outputs.jointNames.resize(0);
        db.outputs.positionCommand.resize(0);
        db.outputs.velocityCommand.resize(0);
        db.outputs.effortCommand.resize(0);

        mSubscriber.reset(); // This should be reset before we reset the handle.
        // mCallback = nullptr;
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2JointStateMessage> mMessage = nullptr;

    // Names will be extracted as strings and later converted to tokens
    std::vector<char*> mJointNames;

    NodeObj mNodeObj;
};

REGISTER_OGN_NODE()
