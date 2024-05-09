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

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
//
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdContext.h>

#include <OgnOnPhysicsStepDatabase.h>
#include <algorithm>
#include <chrono>

namespace omni
{
namespace isaac
{
namespace core_nodes
{


omni::graph::core::INode* gINode;
omni::physx::IPhysx* gPhysXInterface;
struct PhysicsStepData
{
    std::vector<NodeHandle> nodes;
    omni::physx::SubscriptionId stepSubscription;
};
struct handleIDPair
{
    GraphHandle graphHandle;
    GraphInstanceID instanceId;
};
namespace
{
std::map<GraphHandle, PhysicsStepData> gGraphsWithPhysxStepNode;
}
class OgnOnPhysicsStep
{
public:
    OgnOnPhysicsStep()
    {
    }

    static void start(const NodeObj& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnOnPhysicsStepDatabase::sPerInstanceState<OgnOnPhysicsStep>(nodeObj, instanceId);
        auto graphObj = gINode->getGraph(nodeObj);
        auto pipelineStage = graphObj.iGraph->getPipelineStage(graphObj);
        if (pipelineStage != kGraphPipelineStage_OnDemand && state.mInitialized)
        {
            // NodeGraph changed from on-demand since last execution - unsubscribe node from step events
            unsubscribe(nodeObj);
        }
        else if (!state.mInitialized)
        {
            initialize(nodeObj, instanceId);
        }

        state.mStartTime = std::chrono::high_resolution_clock::now();
    }
    static void initialize(const NodeObj& nodeObj, GraphInstanceID instanceId)
    {
        // Acquire All interfaces
        if (!gPhysXInterface)
        {
            gPhysXInterface = carb::getCachedInterface<omni::physx::IPhysx>();
        }
        if (!gINode)
        {
            gINode = carb::getCachedInterface<omni::graph::core::INode>();
        }
        // Get information on the graph the node was inserted
        auto graphObj = gINode->getGraph(nodeObj);
        auto pipelineStage = graphObj.iGraph->getPipelineStage(graphObj);
        auto& state = OgnOnPhysicsStepDatabase::sPerInstanceState<OgnOnPhysicsStep>(nodeObj, instanceId);
        if (!state.mTimelineEventSub)
        {
            state.mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
            state.mTimelineEventSub = carb::events::createSubscriptionToPopByType(
                state.mTimeline->getTimeline()->getTimelineEventStream(),
                static_cast<carb::events::EventType>(omni::timeline::TimelineEventType::ePlay),
                [nodeObj, instanceId](carb::events::IEvent* e) { start(nodeObj, instanceId); }, 0,
                "IsaacSimOGNPhysicStepsTimelineEventHandler");
        }
        if (pipelineStage != kGraphPipelineStage_OnDemand)
        {
            CARB_LOG_ERROR(
                "Physics OnSimulationStep node detected in a non on-demand Graph. Node will only trigger events if the parent Graph is set to compute on-demand. (%s))",
                gINode->getPrimPath(nodeObj));
            // graphObj.iGraph->changePipelineStage(graphObj, kGraphPipelineStage_OnDemand);
        }
        else
        {
            // Check if another Step node was already inserted before subscribing

            if (gGraphsWithPhysxStepNode.find(graphObj.graphHandle) == gGraphsWithPhysxStepNode.end())
            {
                gGraphsWithPhysxStepNode[graphObj.graphHandle] = PhysicsStepData();
                state.mGraphHandlePair = handleIDPair{ graphObj.graphHandle, instanceId };
                gGraphsWithPhysxStepNode[graphObj.graphHandle].stepSubscription =
                    gPhysXInterface->subscribePhysicsStepEvents(
                        onPhysicsStep, reinterpret_cast<void*>(&state.mGraphHandlePair));
            }
            gGraphsWithPhysxStepNode[graphObj.graphHandle].nodes.push_back(nodeObj.nodeHandle);
            state.mInitialized = true;
        }
    }
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        initialize(nodeObj, instanceId);
    }


    static void unsubscribe(const NodeObj& nodeObj)
    {
        const INode* const iNode = nodeObj.iNode;
        if (!iNode)
            return;
        auto graphObj = gINode->getGraph(nodeObj);
        auto graphData = gGraphsWithPhysxStepNode.find(graphObj.graphHandle);

        // Sanity check if graph still exists
        if (graphData != gGraphsWithPhysxStepNode.end())
        {
            // Remove node from list of nodes on this graph
            graphData->second.nodes.erase(
                std::remove(graphData->second.nodes.begin(), graphData->second.nodes.end(), nodeObj.nodeHandle),
                graphData->second.nodes.end());
            // If No more step nodes are present, remove graph from map
            if (graphData->second.nodes.size() == 0)
            {
                gPhysXInterface->unsubscribePhysicsStepEvents(graphData->second.stepSubscription);
                gGraphsWithPhysxStepNode.erase(graphData);
            }
        }
        auto& state = OgnOnPhysicsStepDatabase::sSharedState<OgnOnPhysicsStep>(nodeObj);
        state.mInitialized = false;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        unsubscribe(nodeObj);
        auto& state = OgnOnPhysicsStepDatabase::sPerInstanceState<OgnOnPhysicsStep>(nodeObj, instanceId);
        state.mTimelineEventSub->unsubscribe();
    }


    static void onPhysicsStep(float timeElapsed, void* userData)
    {
        handleIDPair* idpair = reinterpret_cast<handleIDPair*>(userData);
        auto graphHandle = idpair->graphHandle;
        auto instanceId = idpair->instanceId;
        auto graphData = gGraphsWithPhysxStepNode.find(graphHandle);
        // Sanity check if graph exists
        if (graphData != gGraphsWithPhysxStepNode.end())
        {
            // Double sanity check if there are step nodes in this graph
            if (graphData->second.nodes.size() > 0)
            {
                NodeObj node = gINode->getNodeFromHandle(graphData->second.nodes[0]);
                auto graphObj = gINode->getGraph(node);
                // Iterate over all step nodes enabling them to receive the evaluate input
                for (auto handle : graphData->second.nodes)
                {
                    NodeObj node = gINode->getNodeFromHandle(handle);
                    auto& state = OgnOnPhysicsStepDatabase::sPerInstanceState<OgnOnPhysicsStep>(node, instanceId);
                    state.mDt = timeElapsed;
                    state.mIsSet = true;
                }

                graphObj.iGraph->evaluate(graphObj);
            }
        }
    }

    static bool compute(OgnOnPhysicsStepDatabase& db)
    {
        auto& state = db.perInstanceState<OgnOnPhysicsStep>();
        // Update node with trigger event
        if (state.mIsSet)
        {
            state.mIsSet = false;
            db.outputs.deltaSimulationTime() = state.mDt;
            db.outputs.step() = kExecutionAttributeStateEnabled;
            auto end = std::chrono::high_resolution_clock::now();
            db.outputs.deltaSystemTime() =
                std::chrono::duration_cast<std::chrono::microseconds>(end - state.mStartTime).count() * 1.0e-6f;
            state.mStartTime = end;
        }
        else
        {
            CARB_LOG_INFO("Graph evaluated outside physics step. A step will not be triggered this time.(%s))",
                          gINode->getPrimPath(db.abi_node()));
        }
        return true;
    }


private:
    float mDt = 0.0f;
    bool mInitialized = false;
    bool mIsSet = false;
    std::chrono::time_point<std::chrono::high_resolution_clock> mStartTime;
    handleIDPair mGraphHandlePair;
    carb::events::ISubscriptionPtr mTimelineEventSub = nullptr;
    omni::timeline::ITimeline* mTimeline = nullptr;
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
