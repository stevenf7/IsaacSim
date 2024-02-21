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
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
#include <OgnIsaacRealTimeFactorDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacRealTimeFactor : public BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacRealTimeFactorDatabase::sPerInstanceState<OgnIsaacRealTimeFactor>(nodeObj, instanceId);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacRealTimeFactorDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacRealTimeFactor>();

        // Return immediately after first frame to get accurate measurement next frame
        if (state.mResetTimes)
        {
            state.mRealStartTime = std::chrono::steady_clock::now();
            state.mSimStartTime = state.mCoreNodeFramework->getSimTimeMonotonic();
            state.mResetTimes = false;
            return false;
        }

        double real_time_elapsed = std::chrono::duration_cast<std::chrono::duration<double>>(
                                       std::chrono::steady_clock::now() - state.mRealStartTime)
                                       .count();

        double sim_time_elapsed = state.mCoreNodeFramework->getSimTimeMonotonic() - state.mSimStartTime;

        if (sim_time_elapsed == 0.0)
        {
            return false;
        }

        float rtf = static_cast<float>(sim_time_elapsed / real_time_elapsed);

        db.outputs.rtf() = rtf;
        state.mRealStartTime = std::chrono::steady_clock::now();
        state.mSimStartTime = state.mCoreNodeFramework->getSimTimeMonotonic();

        return true;
    }

    virtual void reset()
    {
        mResetTimes = true;
    }

private:
    std::chrono::steady_clock::time_point mRealStartTime;
    double mSimStartTime;
    bool mResetTimes = true;
    uint64_t mFrames = 0;
    uint64_t mStep = 1;

    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
