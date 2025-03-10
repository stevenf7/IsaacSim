// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
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

#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

#include <OgnIsaacReadSimulationTimeDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacReadSimulationTime
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacReadSimulationTimeDatabase::sPerInstanceState<OgnIsaacReadSimulationTime>(nodeObj, instanceId);
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacReadSimulationTimeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadSimulationTime>();

        state.m_resetOnStop = db.inputs.resetOnStop();
        if (db.inputs.swhFrameNumber() > 0)
        {
            if (state.m_resetOnStop)
            {
                db.outputs.simulationTime() = state.m_coreNodeFramework->getSimTimeAtSwhFrame(db.inputs.swhFrameNumber());
            }
            else
            {
                db.outputs.simulationTime() =
                    state.m_coreNodeFramework->getSimTimeMonotonicAtSwhFrame(db.inputs.swhFrameNumber());
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
