// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

#include <OgnIsaacReadSimulationTimeDatabase.h>

namespace omni
{
namespace graph
{
namespace nodes
{

class OgnIsaacReadSimulationTime : public BaseResetNode
{
public:
    static bool compute(OgnIsaacReadSimulationTimeDatabase& db)
    {
        const auto& contextObj = db.abi_context();
        const IGraphContext* const iContext = contextObj.iContext;
        auto& state = db.internalState<OgnIsaacReadSimulationTime>();

        state.mResetOnStop = db.inputs.resetOnStop();
        db.outputs.simulationTime() = state.mSimulationTime;
        state.mSimulationTime += iContext->getElapsedTime(contextObj);
        return true;
    }

    virtual void reset()
    {
        if (mResetOnStop)
        {
            mSimulationTime = 0.0;
        }
    }

private:
    double mSimulationTime = 0.0;
    bool mResetOnStop = true;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
