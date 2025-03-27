// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/timeline/ITimeline.h>

#include <OgnIsaacSimulationGateDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{


class OgnIsaacSimulationGate
{

public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacSimulationGateDatabase::sPerInstanceState<OgnIsaacSimulationGate>(nodeObj, instanceId);

        state.m_timeline = carb::getCachedInterface<omni::timeline::ITimeline>();
        if (!state.m_timeline)
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
        if (state.m_timeline == nullptr)
        {
            return false;
        }
        else if (state.m_timeline->isPlaying() && inputStep > 0)
        {
            state.m_frame++;
            if (state.m_frame >= inputStep)
            {
                state.m_frame = 0;
                db.outputs.execOut() = kExecutionAttributeStateEnabled;
            }
        }
        return true;
    }

private:
    u_int m_frame = 0;
    omni::timeline::ITimeline* m_timeline = nullptr;
};
REGISTER_OGN_NODE()
}
}
}
