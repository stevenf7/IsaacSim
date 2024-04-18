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


#include <include/Ros2Node.h>

#include <OgnROS2PublishRawTransformTreeDatabase.h>

class OgnROS2PublishRawTransformTree : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishRawTransformTreeDatabase::sPerInstanceState<OgnROS2PublishRawTransformTree>(
            nodeObj, instanceId);

        state.mFirstIteration = true;
    }

    static bool compute(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishRawTransformTree>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS TF publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateRawTfTreeMessage();

            Ros2QoSProfile qos;

            const std::string& qosProfile = db.inputs.qosProfile();
            if (db.inputs.staticPublisher())
            {
                qos.depth = 1;
                qos.durability = Ros2QoSDurabilityPolicyType::eTransientLocal;
            }
            else if (qosProfile == "")
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
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);

            state.mParentFrameId = db.inputs.parentFrameId();
            state.mChildFrameId = db.inputs.childFrameId();

            return true;
        }

        return state.publishTF(db);
    }

    bool publishTF(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishRawTransformTree>();

        bool isStaticPublisher = db.inputs.staticPublisher();

        // If we're a static publisher we only publish once on the first iteration.
        // The message will persist as long as the simulation is playing.
        // If we're not a static publisher, we publish every tick only if
        // we have subscribers or mPublishWithoutVerification is true.
        if (isStaticPublisher)
        {
            if (!state.mFirstIteration)
            {
                return false;
            }
            state.mFirstIteration = false;
        }
        else
        {
            // Check if subscription count is 0
            if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
            {
                return false;
            }
        }

        auto& translation = db.inputs.translation();
        auto& rotation = db.inputs.rotation();


        state.mMessage->fillData(db.inputs.timeStamp(), state.mParentFrameId, state.mChildFrameId, translation, rotation);
        state.mPublisher.get()->publish(state.mMessage->ptr());

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishRawTransformTreeDatabase::sPerInstanceState<OgnROS2PublishRawTransformTree>(
            nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
        mFirstIteration = true;
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2RawTfTreeMessage> mMessage = nullptr;

    bool mFirstIteration = true;

    std::string mParentFrameId = "odom";
    std::string mChildFrameId = "base_link";
};

REGISTER_OGN_NODE()
