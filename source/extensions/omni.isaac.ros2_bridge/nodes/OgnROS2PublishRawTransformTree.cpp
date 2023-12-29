// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state =
    //     OgnROS2PublishRawTransformTreeDatabase::sInternalState<OgnROS2PublishRawTransformTree>(nodeObj);

    // }

    static bool compute(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishRawTransformTree>();

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
            // Setup ROS TF publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }

            state.mMessage = state.mFactory->CreateRawTfTreeMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            state.mParentFrameId = db.inputs.parentFrameId();
            state.mChildFrameId = db.inputs.childFrameId();

            return true;
        }

        return state.publishTF(db);
    }

    bool publishTF(OgnROS2PublishRawTransformTreeDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishRawTransformTree>();
        if (state.mPublisher.get()->get_subscription_count() != 0)
        {
            auto& translation = db.inputs.translation();
            auto& rotation = db.inputs.rotation();


            state.mMessage->fillData(
                db.inputs.timeStamp(), state.mParentFrameId, state.mChildFrameId, translation, rotation);
            state.mPublisher.get()->publish(state.mMessage->ptr());
        }
        return true;
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishRawTransformTreeDatabase::sInternalState<OgnROS2PublishRawTransformTree>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2RawTfTreeMessage> mMessage = nullptr;

    std::string mParentFrameId = "odom";
    std::string mChildFrameId = "base_link";
};

REGISTER_OGN_NODE()
