// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacRenderVarToCpuPointerDatabase.h"

#include <carb/graphics/GraphicsTypes.h>
#include <carb/logging/Log.h>

#include <rtx/hydra/HydraRenderResults.h>

namespace omni::isaac::sensor
{

/**
 * @brief a node to pass the pointer to a cpu renderVar
 *
 */
class OgnIsaacRenderVarToCpuPointer
{

public:
    // If the node fails we want to cleanup the output
    static bool returnCleanly(OgnIsaacRenderVarToCpuPointerDatabase& db, bool passThroughValue)
    {
        db.outputs.cpuPointer() = 0;
        db.outputs.bufferSize() = 0;
        db.outputs.exec() = passThroughValue ? kExecutionAttributeStateEnabled : kExecutionAttributeStateDisabled;
        return passThroughValue;
    }

    static bool compute(OgnIsaacRenderVarToCpuPointerDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Isaac RenderVar To CPU Pointer");
        // parse input render result
        auto rp = reinterpret_cast<omni::usd::hydra::HydraRenderProduct*>(db.inputs.renderResults());
        if (!rp)
        {
            return returnCleanly(db, true);
        }
        if (rp->status == omni::usd::hydra::RenderStatus::eFailed)
        {
            return returnCleanly(db, false);
        }

        const auto renderVarToken = db.inputs.renderVar();
        auto renderVar = omni::usd::hydra::getRenderVarFromProduct(rp, renderVarToken.token);
        if (!renderVar)
        {
            CARB_LOG_WARN_ONCE(
                "IsaacRenderVarToCpuPointer missing valid input renderVar %s", db.tokenToString(db.inputs.renderVar()));
            return returnCleanly(db, false);
        }

        if (!renderVar->isRpResource)
        {
            if (!renderVar->rawResource)
            {
                if (renderVar->rawResourceBufferSize != 0)
                {
                    CARB_LOG_WARN_ONCE("IsaacRenderVarToCpuPointer has a bad rawResource");
                }
                return returnCleanly(db, false);
            }
            db.outputs.cpuPointer() = reinterpret_cast<uint64_t>(renderVar->rawResource);
            db.outputs.bufferSize() = static_cast<uint64_t>(renderVar->rawResourceBufferSize);
        }
        else
        {
            db.outputs.cpuPointer() = 0;
            db.outputs.bufferSize() = 0;
        }
        db.outputs.exec() = kExecutionAttributeStateEnabled;

        return true;
    }
};

REGISTER_OGN_NODE()
} // omni::isaac::sensor
