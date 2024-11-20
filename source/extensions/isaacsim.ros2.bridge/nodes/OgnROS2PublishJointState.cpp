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

#include "isaacsim/core/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <isaacsim/core/utils/Math.h>
#include <omni/fabric/FabricUSD.h>

#include <DynamicControl.h>
#include <OgnROS2PublishJointStateDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2PublishJointState : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishJointStateDatabase::sPerInstanceState<OgnROS2PublishJointState>(nodeObj, instanceId);

        state.m_dynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        if (!state.m_dynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS2PublishJointStateDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnROS2PublishJointState>();

        const auto& prim = db.inputs.targetPrim();
        const char* primPath;
        if (prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            db.logError("Could not find target prim");
            return false;
        }

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.isInitialized())
        {
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!state.initializeNodeHandle(
                    std::string(nodeObj.iNode->getPrimPath(nodeObj)),
                    collectNamespace(db.inputs.nodeNamespace(),
                                     stage->GetPrimAtPath(pxr::SdfPath(nodeObj.iNode->getPrimPath(nodeObj)))),
                    db.inputs.context()))
            {
                db.logError("Unable to create ROS2 node, please check that namespace is valid");
                return false;
            }
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }
            state.m_unitScale = UsdGeomGetStageMetersPerUnit(stage);

            // Verify we have a valid articulation prim
            if (state.m_dynamicControlPtr->peekObjectType(primPath) == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.m_articulationHandle = state.m_dynamicControlPtr->getArticulation(primPath);
            }
            else
            {
                db.logError("Prim is not an articulation");
                return false;
            }

            if (!state.m_articulationHandle)
            {
                db.logError("Articulation %s not found", primPath);
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createJointStateMessage();

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

        return state.publishJointStates(db, context);
    }

    bool publishJointStates(OgnROS2PublishJointStateDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.perInstanceState<OgnROS2PublishJointState>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return false;
        }

        double stageUnits = 1.0 / m_unitScale;
        double dt = db.inputs.timeStamp() - m_previousTimeStamp;
        m_previousTimeStamp = db.inputs.timeStamp();

        long stageId = context.iContext->getStageId(context);
        m_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        state.m_message->writeData(db.inputs.timeStamp(), m_dynamicControlPtr, m_articulationHandle, m_stage,
                                   m_dofProperties, m_previousJointPosition, m_calculatedJointVelocity, dt, stageUnits);
        state.m_publisher.get()->publish(state.m_message->getPtr());
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishJointStateDatabase::sPerInstanceState<OgnROS2PublishJointState>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_stage = nullptr;
        m_dofProperties.clear();
        m_previousJointPosition.clear();
        m_calculatedJointVelocity.clear();
        m_previousTimeStamp = 0;
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2JointStateMessage> m_message = nullptr;

    pxr::UsdStageWeakPtr m_stage = nullptr;
    omni::isaac::dynamic_control::DynamicControl* m_dynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle m_articulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    std::vector<float> m_previousJointPosition;
    std::vector<float> m_calculatedJointVelocity;
    std::vector<omni::isaac::dynamic_control::DcDofProperties> m_dofProperties;

    double m_unitScale = 1;
    double m_previousTimeStamp = 0;
};

REGISTER_OGN_NODE()
