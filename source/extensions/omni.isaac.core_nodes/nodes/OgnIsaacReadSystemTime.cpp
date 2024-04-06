// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <CoreNodes.h>
//
#include <omni/usd/UsdContext.h>

#include <OgnIsaacReadSystemTimeDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadSystemTime
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacReadSystemTimeDatabase::sPerInstanceState<OgnIsaacReadSystemTime>(nodeObj, instanceId);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacReadSystemTimeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadSystemTime>();

        if (db.inputs.swhFrameNumber() > 0)
        {
            db.outputs.systemTime() = state.mCoreNodeFramework->getSystemTimeAtSwhFrame(db.inputs.swhFrameNumber());
        }
        else
        {
            db.outputs.systemTime() = state.mCoreNodeFramework->getSystemTime();
        }
        return true;
    }


private:
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
