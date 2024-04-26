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
#include <omni/usd/UsdContext.h>

#include <OgnIsaacReadSimulationTimeDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadSimulationTime
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacReadSimulationTimeDatabase::sPerInstanceState<OgnIsaacReadSimulationTime>(nodeObj, instanceId);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacReadSimulationTimeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadSimulationTime>();

        state.mResetOnStop = db.inputs.resetOnStop();
        if (db.inputs.swhFrameNumber() > 0)
        {
            if (state.mResetOnStop)
            {
                db.outputs.simulationTime() = state.mCoreNodeFramework->getSimTimeAtSwhFrame(db.inputs.swhFrameNumber());
            }
            else
            {
                db.outputs.simulationTime() =
                    state.mCoreNodeFramework->getSimTimeMonotonicAtSwhFrame(db.inputs.swhFrameNumber());
            }
        }
        else
        {
            if (state.mResetOnStop)
            {
                db.outputs.simulationTime() = state.mCoreNodeFramework->getSimTime();
            }
            else
            {
                db.outputs.simulationTime() = state.mCoreNodeFramework->getSimTimeMonotonic();
            }
        }
        return true;
    }


private:
    bool mResetOnStop = true;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
