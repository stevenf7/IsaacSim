// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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


#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <OgnGXFPoseTreeFrameMapBuilderDatabase.h>

class OgnGXFPoseTreeFrameMapBuilder
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnGXFPoseTreeFrameMapBuilderDatabase::sInternalState<OgnGXFPoseTreeFrameMapBuilder>(nodeObj);
        state.mThisPrimPath = nodeObj.iNode->getPrimPath(nodeObj);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }

    static bool compute(OgnGXFPoseTreeFrameMapBuilderDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.internalState<OgnGXFPoseTreeFrameMapBuilder>();
        //  Find our stage
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return false;
        }
        const pxr::UsdPrim thisPrim = stage->GetPrimAtPath(pxr::SdfPath(state.mThisPrimPath));
        // Finding target prims
        pxr::TfToken targetPrimInputs =
            carb::flatcache::toTfToken(OgnGXFPoseTreeFrameMapBuilderAttributes::inputs::targetPrims.m_token);
        const pxr::UsdRelationship targetRel = thisPrim.GetRelationship(targetPrimInputs);
        targetRel.GetTargets(&state.mPrims);

        auto frameNames = db.inputs.frameNames();

        if (state.mPrims.size() != frameNames.size())
        {
            CARB_LOG_ERROR_ONCE(
                "Need to have the same number of target prims and frame names, "
                "but there are %i target prims and %i frame names",
                state.mPrims.size(), frameNames.size());
            return false;
        }

        db.outputs.frameNamesMap().resize(2 * frameNames.size());
        for (int i = 0; i < frameNames.size(); ++i)
        {
            db.outputs.frameNamesMap()[2 * i] = db.stringToToken(state.mPrims[i].GetString().c_str());
            db.outputs.frameNamesMap()[2 * i + 1] = frameNames[i];
        }


        return true;
    }

private:
    pxr::SdfPathVector mPrims;
    const char* mThisPrimPath = nullptr;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
