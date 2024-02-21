// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <omni/isaac/utils/BaseResetNode.h>

#include <CoreNodes.h>
#include <OgnIsaacRunOneSimulationFrameDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacRunOneSimulationFrame : public BaseResetNode
{
public:
    static bool compute(OgnIsaacRunOneSimulationFrameDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnIsaacRunOneSimulationFrame>();

        if (state.mFirstFrame)
        {
            state.mFirstFrame = false;
            db.outputs.step() = kExecutionAttributeStateEnabled;
        }
        return true;
    }

    virtual void reset()
    {
        mFirstFrame = true;
    }


private:
    bool mFirstFrame = true;
};

REGISTER_OGN_NODE()
}
}
}
