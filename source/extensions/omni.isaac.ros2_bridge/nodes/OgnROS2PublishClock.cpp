// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/extras/Library.h>

#include <include/Ros2Factory.h>
#include <include/Ros2Node.h>

#include <OgnROS2PublishClockDatabase.h>

class OgnROS2PublishClock : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        // auto& state = OgnROS2PublishClockDatabase::sInternalState<OgnROS2PublishClock>(nodeObj);
    }

    static bool compute(OgnROS2PublishClockDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishClock>();
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
            state.mMessage = state.mFactory->CreateClockMessage();
            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.publishClock(db);
        // return true;
    }

    bool publishClock(OgnROS2PublishClockDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishClock>();

        // std::cout << "Creating message next...." << std::endl;

        
        if (state.mPublisher.get()->get_subscription_count() != 0){
        // if (1 != 0){

        // std::cout << "Filling Message... " << std::endl;
            state.mMessage->fill(db.inputs.timeStamp());

        // std::cout << "Publishing message" << std::endl;
        
            state.mPublisher.get()->publish(state.mMessage->ptr());
        }


        // std::cout << "Message published..." << std::endl;

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishClockDatabase::sInternalState<OgnROS2PublishClock>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2ClockMessage> mMessage = nullptr;
};

REGISTER_OGN_NODE()
