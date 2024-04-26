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


#include <include/Ros2Node.h>

#include <OgnROS2PublishImuDatabase.h>


class OgnROS2PublishImu : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2PublishImuDatabase::sPerInstanceState<OgnROS2PublishImu>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2PublishImuDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS2PublishImu>();

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

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            // Setup ROS IMU publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateImuMessage();

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
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);
            state.mFrameId = db.inputs.frameId();

            return true;
        }

        state.publishImu(db);

        return true;
    }


    void publishImu(OgnROS2PublishImuDatabase& db)
    {

        auto& state = db.perInstanceState<OgnROS2PublishImu>();
        // Check if subscription count is 0
        if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
        {
            return;
        }
        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);

        if (!db.inputs.publishLinearAcceleration())
        {
            state.mMessage->fillAccel(true);
        }
        else
        {
            auto& linAccel = db.inputs.linearAcceleration();
            std::vector<double> accel{ linAccel[0], linAccel[1], linAccel[2] };
            state.mMessage->fillAccel(false, accel);
        }

        if (!db.inputs.publishAngularVelocity())
        {
            state.mMessage->fillVelo(true);
        }
        else
        {
            auto& angVel = db.inputs.angularVelocity();
            std::vector<double> velo{ angVel[0], angVel[1], angVel[2] };
            state.mMessage->fillVelo(false, velo);
        }

        if (!db.inputs.publishOrientation())
        {
            state.mMessage->fillOrient(true);
        }
        else
        {
            auto& orientation = db.inputs.orientation();
            std::vector<double> orient{ orientation.GetImaginary()[0], orientation.GetImaginary()[1],
                                        orientation.GetImaginary()[2], orientation.GetReal() };
            state.mMessage->fillOrient(false, orient);
        }

        state.mPublisher.get()->publish(state.mMessage->ptr());
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishImuDatabase::sPerInstanceState<OgnROS2PublishImu>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2ImuMessage> mMessage = nullptr;
    std::string mFrameId = "sim_imu";
};

REGISTER_OGN_NODE()
