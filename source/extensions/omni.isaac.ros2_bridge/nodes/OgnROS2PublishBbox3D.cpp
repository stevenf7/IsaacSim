// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sInternalState<ROS2PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS2PublishBbox3DDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishBbox3D>();
        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }
        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }
            state.mMessage = state.mFactory->CreateBoundingBox3DMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());
            state.mFrameId = db.inputs.frameId();

            return true;
        }

        return state.publishDetectionArray(db);
    }

    bool publishDetectionArray(OgnROS2PublishBbox3DDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishBbox3D>();
        if (state.mPublisher.get()->get_subscription_count() != 0){
        size_t bytes = db.inputs.data().size();
        size_t numBbox = bytes / sizeof(Bbox3DData);
        const Bbox3DData* bboxData = reinterpret_cast<const Bbox3DData*>(db.inputs.data().data());


        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);
        state.mMessage->fillBboxData(bboxData, numBbox);
        state.mPublisher.get()->publish(state.mMessage->ptr());
        }
        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishBbox3DDatabase::sInternalState<OgnROS2PublishBbox3D>(nodeObj);
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
