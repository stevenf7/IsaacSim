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
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnIsaacReadFabricXformDatabase::sPerInstanceState<OgnIsaacReadFabricXform>(nodeObj,
    //     instanceId);
    // }

    static bool compute(OgnIsaacReadWorldPoseDatabase& db)
    {
        // auto& nodeObj = db.abi_node();
        auto& context = db.abi_context();

        // const auto* const iContext = context.iContext;
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
        auto transform = usdrt::GfTransform(usdTransform);


        const double* sourceOrientation = transform.GetRotation().GetQuat().data();
        const double* sourceTranslation = transform.GetTranslation().data();
        if (includeScale)
        {
            AttributeDataHandle scaleAttr =
                iBundle->addAttribute(context, bundleHandle, iToken->getHandle("xformOp:scale"),
                                      Type(BaseDataType::eDouble, 3, 0, AttributeRole::eNone));
            double* scaleData = getDataW<double>(context, scaleAttr);
            const double* sourceScale = transform.GetScale().data();
            scaleData[0] = sourceScale[0];
            scaleData[1] = sourceScale[1];
            scaleData[2] = sourceScale[2];
        }

        orientationData[0] = sourceOrientation[0];
        orientationData[1] = sourceOrientation[1];
        orientationData[2] = sourceOrientation[2];
        orientationData[3] = sourceOrientation[3];

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

// Bundle 'read_prims_outputs_primsBundle' from /World/ActionGraph/bundle_inspector (attributes = 0 children = 1)
//     Has Child Bundle 'prim0' from /World/ActionGraph/bundle_inspector (attributes = 6 children = 0)
//         [0] sourcePrimPath(token) = "/World/Cube"
//         [1] sourcePrimType(token) = "Mesh"
//         [2] xformOp:scale(double3) = (1.000000, 1.000000, 1.000000)
//         [3] xformOp:translate(double3) = (0.000000, 0.000000, -2.974375)
//         [4] xformOp:orient(double4 (quaternion)) = (0.000000, 0.000000, 0.000000, 1.000000)
//         [5] worldMatrix(double16 (matrix)) = ((1.000000, 0.000000, 0.000000, 0.000000), (0.000000, 1.000000,
//         0.000000, 0.000000), (0.000000, 0.000000, 1.000000, 0.000000), (0.000000, 0.000000, -2.974375, 1.000000))
