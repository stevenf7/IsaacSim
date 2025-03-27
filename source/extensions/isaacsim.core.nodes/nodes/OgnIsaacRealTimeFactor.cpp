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
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

#include <OgnIsaacRealTimeFactorDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacRealTimeFactor : public isaacsim::core::includes::BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacRealTimeFactorDatabase::sPerInstanceState<OgnIsaacRealTimeFactor>(nodeObj, instanceId);
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacRealTimeFactorDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacRealTimeFactor>();

        // Return immediately after first frame to get accurate measurement next frame
        if (state.m_resetTimes)
        {
            state.m_realStartTime = std::chrono::steady_clock::now();
            state.m_simStartTime = state.m_coreNodeFramework->getSimTimeMonotonic();
            state.m_resetTimes = false;
            return false;
        }

        double realTimeElapsed = std::chrono::duration_cast<std::chrono::duration<double>>(
                                     std::chrono::steady_clock::now() - state.m_realStartTime)
                                     .count();

        double simTimeElapsed = state.m_coreNodeFramework->getSimTimeMonotonic() - state.m_simStartTime;

        if (simTimeElapsed == 0.0)
        {
            return false;
        }

        float rtf = static_cast<float>(simTimeElapsed / realTimeElapsed);

        db.outputs.rtf() = rtf;
        state.m_realStartTime = std::chrono::steady_clock::now();
        state.m_simStartTime = state.m_coreNodeFramework->getSimTimeMonotonic();

        return true;
    }

    virtual void reset()
    {
        m_resetTimes = true;
    }

private:
    std::chrono::steady_clock::time_point m_realStartTime;
    double m_simStartTime;
    bool m_resetTimes = true;
    uint64_t m_frames = 0;
    uint64_t m_step = 1;

    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
