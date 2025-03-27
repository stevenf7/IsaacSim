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

#include <OgnIsaacReadSystemTimeDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacReadSystemTime
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacReadSystemTimeDatabase::sPerInstanceState<OgnIsaacReadSystemTime>(nodeObj, instanceId);
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
    }

    static bool compute(OgnIsaacReadSystemTimeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadSystemTime>();

        if (db.inputs.swhFrameNumber() > 0)
        {
            db.outputs.systemTime() = state.m_coreNodeFramework->getSystemTimeAtSwhFrame(db.inputs.swhFrameNumber());
        }
        else
        {
            db.outputs.systemTime() = state.m_coreNodeFramework->getSystemTime();
        }
        return true;
    }


private:
    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework;
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
