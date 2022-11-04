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

namespace omni
{
namespace isaac
{
namespace sensor
{

/**
 * @brief a node to pass the pointer to a cpu renderVar
 *
 */
class OgnIsaacRenderVarToCpuPointer
{

public:
    static bool compute(OgnIsaacRenderVarToCpuPointerDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Isaac RenderVar To CPU Pointer");
        // parse input render result
        auto rp = reinterpret_cast<omni::usd::hydra::HydraRenderProduct*>(db.inputs.renderResults());
        if (!rp || rp->status == omni::usd::hydra::RenderStatus::eFailed)
        {
            return false;
        }

        const auto renderVarToken = db.inputs.renderVar();
        auto renderVar = omni::usd::hydra::getRenderVarFromProduct(rp, renderVarToken.token);
        if (!renderVar)
        {
            CARB_LOG_WARN_ONCE(
                "IsaacRenderVarToCpuPointer missing valid input renderVar %s", db.tokenToString(db.inputs.renderVar()));
            return false;
        }

        if (!renderVar->isRpResource)
        {
            if (!renderVar->rawResource)
            {
                CARB_ASSERT(renderVar->rawResourceBufferSize == 0);
                return true;
            }
            db.outputs.cpuPointer() = reinterpret_cast<uint64_t>(renderVar->rawResource);
            db.outputs.bufferSize() = static_cast<uint64_t>(renderVar->rawResourceBufferSize);
        }
        db.outputs.exec() = kExecutionAttributeStateEnabled;

        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
