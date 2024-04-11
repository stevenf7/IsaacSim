// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>

#include <include/Ros2Node.h>

#include <OgnROS2PublishBbox3DDatabase.h>

struct Bbox3DData
{
    uint32_t semanticId;
    float x_min;
    float y_min;
    float z_min;
    float x_max;
    float y_max;
    float z_max;
    pxr::GfMatrix4f transform;
    float occlusionRatio;
};

class OgnROS2PublishBbox3D : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sPerInstanceState<ROS2PublishBbox2D>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2PublishBbox3DDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishBbox3D>();
        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }
        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }
            state.mMessage = state.mFactory->CreateBoundingBox3DMessage();

            if (!state.mMessage->ptr())
            {
                CARB_LOG_ERROR("Unable to find Detection3DArray message type");

                return false;
            }

            Ros2QoSProfile qos;
            qos.depth = db.inputs.queueSize();
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);
            state.mFrameId = db.inputs.frameId();

            return true;
        }

        return state.publishDetectionArray(db);
    }

    bool publishDetectionArray(OgnROS2PublishBbox3DDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishBbox3D>();
        // Check if subscription count is 0
        if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
        {
            return false;
        }
        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox3DData);
        const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());


        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);
        state.mMessage->fillBboxData(bboxData, numBbox);
        state.mPublisher.get()->publish(state.mMessage->ptr());

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishBbox3DDatabase::sPerInstanceState<OgnROS2PublishBbox3D>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2BoundingBox3DMessage> mMessage = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
