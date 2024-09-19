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

using namespace omni::isaac::ros2_bridge;

class OgnROS2PublishCameraInfo : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
    }

    static bool compute(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishCameraInfo>();

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createCameraInfoMessage();

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

            state.m_publisher = state.m_factory->createPublisher(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);
            return true;
        }

        state.m_frameId = db.inputs.frameId();
        state.publishCameraInfo(db);
        return true;
    }

    void publishCameraInfo(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishCameraInfo>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return;
        }

        state.m_message->writeHeader(db.inputs.timeStamp(), state.m_frameId);
        state.m_message->writeResolution(db.inputs.height(), db.inputs.width());
        state.m_message->writeIntrinsicMatrix(db.inputs.k().data(), 9);
        state.m_message->writeRectificationMatrix(db.inputs.r().data(), 9);
        state.m_message->writeProjectionMatrix(db.inputs.p().data(), 12);

        std::string physicalDistortion = db.tokenToString(db.inputs.physicalDistortionModel());
        if (physicalDistortion.length() > 0)
        {
            std::vector<double> coeff;
            for (size_t i = 0; i < db.inputs.physicalDistortionCoefficients().size(); i++)
            {
                coeff.push_back(db.inputs.physicalDistortionCoefficients()[i]);
            }
            state.m_message->writeDistortionParameters(coeff, physicalDistortion);
        }
        else
        {
            // TODO: Handle fisheye coefficients?
            std::vector<double> empty;
            state.m_message->writeDistortionParameters(empty, db.tokenToString(db.inputs.projectionType()));
        }

        state.m_publisher.get()->publish(state.m_message->getPtr());
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishCameraInfoDatabase::sPerInstanceState<OgnROS2PublishCameraInfo>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2CameraInfoMessage> m_message = nullptr;

    std::string m_frameId = "sim_camera";
};

REGISTER_OGN_NODE()
