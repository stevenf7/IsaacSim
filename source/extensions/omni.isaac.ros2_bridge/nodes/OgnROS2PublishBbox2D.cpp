// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>

#include <include/Ros2Factory.h>
#include <include/Ros2Node.h>

#include <OgnROS2PublishBbox2DDatabase.h>

struct Bbox2DData
{
    uint32_t semanticId;
    int32_t x_min;
    int32_t y_min;
    int32_t x_max;
    int32_t y_max;
    float occlusionRatio;
};

class OgnROS2PublishBbox2D : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = ROS2PublishBbox2DDatabase::sInternalState<ROS2PublishBbox2D>(nodeObj);
    // }

    static bool compute(OgnROS2PublishBbox2DDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishBbox2D>();
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

            state.mMessage = state.mFactory->CreateBoundingBox2DMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        return state.publishDetectionArray(db);
    }

    bool publishDetectionArray(OgnROS2PublishBbox2DDatabase& db)
    {

        auto& state = db.internalState<OgnROS2PublishBbox2D>();
        if (state.mPublisher.get()->get_subscription_count() != 0)
        {
            size_t bytes = db.inputs.data().size();
            size_t numBbox = bytes / sizeof(Bbox2DData);

            const Bbox2DData* bboxData = reinterpret_cast<const Bbox2DData*>(db.inputs.data().data());

            state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);
            state.mMessage->fillBboxData(bboxData, numBbox);
            state.mPublisher.get()->publish(state.mMessage->ptr());
        }
        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishBbox2DDatabase::sInternalState<OgnROS2PublishBbox2D>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2BoundingBox2DMessage> mMessage = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
