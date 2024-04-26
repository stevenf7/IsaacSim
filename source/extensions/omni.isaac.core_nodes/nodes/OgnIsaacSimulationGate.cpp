// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/fabric/FabricUSD.h>
#include <omni/timeline/ITimeline.h>

#include <CoreNodes.h>
#include <OgnIsaacSimulationGateDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{


class OgnIsaacSimulationGate
{

public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacSimulationGateDatabase::sPerInstanceState<OgnIsaacSimulationGate>(nodeObj, instanceId);

        state.mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
        if (!state.mTimeline)
        {
            CARB_LOG_ERROR("Failed to acquire timeline interface");
            return;
        }
    }

    static bool compute(OgnIsaacSimulationGateDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacSimulationGate>();
        const auto& inputStep = db.inputs.step();
        // If the timeline is stopped or step is set to zero, skip execution
        if (state.mTimeline == nullptr)
        {
            return false;
        }
        else if (state.mTimeline->isPlaying() && inputStep > 0)
        {
            state.mFrame++;
            if (state.mFrame >= inputStep)
            {
                state.mFrame = 0;
                db.outputs.execOut() = kExecutionAttributeStateEnabled;
            }
        }
        else
        {
            state.mFrame = 0;
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
        }
        return true;
    }

private:
    u_int mFrame = 0;
    omni::timeline::ITimeline* mTimeline = nullptr;
};
REGISTER_OGN_NODE()
}
}
}
