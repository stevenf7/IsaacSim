// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on


#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Pose.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/transform.h>
#include <usdrt/gf/vec.h>

#include <OgnIsaacReadWorldPoseDatabase.h>


namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadWorldPose
{
public:
    static bool compute(OgnIsaacReadWorldPoseDatabase& db)
    {
        auto& context = db.abi_context();

        const auto* const iToken = context.iToken;
        const auto* const iBundle = context.iBundle;

        auto& state = db.perInstanceState<OgnIsaacReadWorldPose>();
        const auto& input_prim = db.inputs.prim();
        const auto& includeScale = db.inputs.includeScale();
        pxr::SdfPath primPath;
        if (input_prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(input_prim[0]);
        }
        else
        {
            db.logError("Omnigraph Error: no input prim");
            return false;
        }
        if (state.mStage == nullptr)
        {
            //  Find our stage
            const GraphContextObj& context = db.abi_context();
            state.mStageId = context.iContext->getStageId(context);
            state.mStage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(state.mStageId));
            state.mUsdrtStage = usdrt::UsdStage::Attach({ (state.mStageId) });
            if (!state.mStage)
            {
                db.logError("Could not find USD stage %ld", state.mStageId);
                return false;
            }
        }
        usdrt::GfMatrix4d usdTransform =
            omni::isaac::utils::pose::computeWorldXformNoCache(state.mStage, state.mUsdrtStage, primPath);
        const double* sourceOrientation_i =
            usdTransform.ExtractRotationMatrix().ExtractRotation().GetImaginary().GetArray();
        const double sourceOrientation_r = usdTransform.ExtractRotationMatrix().ExtractRotation().GetReal();
        const double* sourceTranslation = usdTransform.ExtractTranslation().GetArray();
        auto& bundleContents = db.outputs.primsBundle();
        auto bundleHandle = bundleContents.abi_bundleHandle();

        AttributeDataHandle orientationAttr =
            iBundle->addAttribute(context, bundleHandle, iToken->getHandle("xformOp:orient"),
                                  Type(BaseDataType::eDouble, 4, 0, AttributeRole::eQuaternion));
        AttributeDataHandle positionAttr =
            iBundle->addAttribute(context, bundleHandle, iToken->getHandle("xformOp:translate"),
                                  Type(BaseDataType::eDouble, 3, 0, AttributeRole::eNone));

        double* orientationData = getDataW<double>(context, orientationAttr);
        double* positionData = getDataW<double>(context, positionAttr);

        if (includeScale)
        {
            auto transform = usdrt::GfTransform(usdTransform);
            AttributeDataHandle scaleAttr =
                iBundle->addAttribute(context, bundleHandle, iToken->getHandle("xformOp:scale"),
                                      Type(BaseDataType::eDouble, 3, 0, AttributeRole::eNone));
            double* scaleData = getDataW<double>(context, scaleAttr);
            const double* sourceScale = transform.GetScale().data();
            scaleData[0] = sourceScale[0];
            scaleData[1] = sourceScale[1];
            scaleData[2] = sourceScale[2];
        }

        orientationData[0] = sourceOrientation_r;
        orientationData[1] = sourceOrientation_i[0];
        orientationData[2] = sourceOrientation_i[1];
        orientationData[3] = sourceOrientation_i[2];

        positionData[0] = sourceTranslation[0];
        positionData[1] = sourceTranslation[1];
        positionData[2] = sourceTranslation[2];

        return true;
    }

private:
    pxr::UsdStageRefPtr mStage = nullptr;
    long mStageId;
    usdrt::UsdStageRefPtr mUsdrtStage{ nullptr };
};
REGISTER_OGN_NODE()
}
}
}
