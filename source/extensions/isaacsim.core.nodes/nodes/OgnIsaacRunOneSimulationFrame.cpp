// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.


#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/nodes/ICoreNodes.h>

#include <OgnIsaacRunOneSimulationFrameDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacRunOneSimulationFrame : public isaacsim::core::includes::BaseResetNode
{
public:
    static bool compute(OgnIsaacRunOneSimulationFrameDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacRunOneSimulationFrame>();

        if (state.m_firstFrame)
        {
            state.m_firstFrame = false;
            db.outputs.step() = kExecutionAttributeStateEnabled;
        }
        return true;
    }

    virtual void reset()
    {
        m_firstFrame = true;
    }


private:
    bool m_firstFrame = true;
};

REGISTER_OGN_NODE()
}
}
}
