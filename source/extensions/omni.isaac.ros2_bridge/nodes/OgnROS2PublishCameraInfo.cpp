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

#include <OgnROS2PublishCameraInfoDatabase.h>


class OgnROS2PublishCameraInfo : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        // auto& state = OgnROS2PublishCameraInfoDatabase::sPerInstanceState<OgnROS2PublishCameraInfo>(nodeObj,
        // instanceId);
    }

    static bool compute(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishCameraInfo>();
        // std::cout << "Call publish method..." << std::endl;

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
            state.mMessage = state.mFactory->CreateCameraInfoMessage();
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

            return true;
        }

        state.mFrameId = db.inputs.frameId();

        state.publishCameraInfo(db);

        return true;
    }

    void publishCameraInfo(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishCameraInfo>();

        // Check if subscription count is 0
        if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
        {
            return;
        }
        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);
        state.mMessage->fillHeightWidth(db.inputs.height(), db.inputs.width());
        state.mMessage->fillIntrisicArray(db.inputs.k().data(), 9);
        state.mMessage->fillRectificationArray(db.inputs.r().data(), 9);
        state.mMessage->fillProjectionArray(db.inputs.p().data(), 12);

        std::string physicalDistortion = db.tokenToString(db.inputs.physicalDistortionModel());

        if (physicalDistortion.length() > 0)
        {
            std::vector<double> coeff;
            for (size_t i = 0; i < db.inputs.physicalDistortionCoefficients().size(); i++)
            {
                coeff.push_back(db.inputs.physicalDistortionCoefficients()[i]);
            }
            state.mMessage->fillDistortionModel(coeff, physicalDistortion);
        }
        else
        {
            // TODO: Handle fisheye coeffieicents?
            std::vector<double> empty;
            state.mMessage->fillDistortionModel(empty, db.tokenToString(db.inputs.projectionType()));
        }
        state.mPublisher.get()->publish(state.mMessage->ptr());
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishCameraInfoDatabase::sPerInstanceState<OgnROS2PublishCameraInfo>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2CameraInfoMessage> mMessage = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
