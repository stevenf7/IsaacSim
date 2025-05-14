// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

#include <OgnIsaacReadSimulationTimeAnnotatorDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacReadSimulationTimeAnnotator
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacReadSimulationTimeAnnotatorDatabase::sPerInstanceState<OgnIsaacReadSimulationTimeAnnotator>(
            nodeObj, instanceId);
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacReadSimulationTimeAnnotatorDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadSimulationTimeAnnotator>();

        state.m_resetOnStop = db.inputs.resetOnStop();
        if (db.inputs.referenceTimeNumerator() > 0 || db.inputs.referenceTimeDenominator() > 0)
        {
            if (state.m_resetOnStop)
            {
                db.outputs.simulationTime() = state.m_coreNodeFramework->getSimTimeAtTime(omni::fabric::RationalTime(
                    db.inputs.referenceTimeNumerator(), db.inputs.referenceTimeDenominator()));
            }
            else
            {
                db.outputs.simulationTime() = state.m_coreNodeFramework->getSimTimeMonotonicAtTime(
                    omni::fabric::RationalTime(db.inputs.referenceTimeNumerator(), db.inputs.referenceTimeDenominator()));
            }
        }
        else
        {
            if (state.m_resetOnStop)
            {
                db.outputs.simulationTime() = state.m_coreNodeFramework->getSimTime();
            }
            else
            {
                db.outputs.simulationTime() = state.m_coreNodeFramework->getSimTimeMonotonic();
            }
        }
        db.outputs.execOut() = ExecutionAttributeState::kExecutionAttributeStateEnabled;

        return true;
    }


private:
    bool m_resetOnStop = true;
    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
