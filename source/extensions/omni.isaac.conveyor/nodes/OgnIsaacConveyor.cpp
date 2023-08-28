// Copyright (c) 2019-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <OgnIsaacConveyorDatabase.h>

///
#include <omni/usd/UsdContext.h>
///

#include <omni/fabric/FabricUSD.h>
#include <omni/usd/UsdUtils.h>
#include <pxr/pxr.h>
#include <pxr/usd/usdPhysics/rigidBodyAPI.h>

namespace omni
{
namespace isaac
{
namespace conveyor
{

// minimal compute node example that reads one float and writes one float
// e.g. out value = 3.0f * in value
class OgnIsaacConveyor
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& _state = OgnIsaacConveyorDatabase::sInternalState<OgnIsaacConveyor>(nodeObj);
        _state.m_EventSubscription = carb::events::createSubscriptionToPop(
            omni::usd::UsdContext::getContext()->getStageEventStream().get(),
            [nodeObj](carb::events::IEvent* e)
            {
                auto& state = OgnIsaacConveyorDatabase::sInternalState<OgnIsaacConveyor>(nodeObj);
                state.mOnEnd =
                    static_cast<omni::usd::StageEventType>(e->type) == omni::usd::StageEventType::eAnimationStopPlay;
                state.mOnStart =
                    static_cast<omni::usd::StageEventType>(e->type) == omni::usd::StageEventType::eAnimationStartPlay;
                if (nodeObj.iNode->isValid(nodeObj) && (state.mOnEnd || state.mOnStart))
                {
                    nodeObj.iNode->requestCompute(nodeObj);
                }
            });
    }

    static bool compute(OgnIsaacConveyorDatabase& db)
    {
        if (db.inputs.enabled())
        {
            // const GraphContextObj& context = db.abi_context();
            // pxr::SdfChangeBlock changeBlock(true);
            auto& state = db.internalState<OgnIsaacConveyor>();
            bool velocity_changed = state.mVelocity != db.inputs.velocity() ||
                                    (state.mDirection - pxr::GfVec3f(db.inputs.direction())).GetLength() > 1.0e-6f;
            if (state.mOnStart || velocity_changed)
            {
                pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
                state.mVelocity = db.inputs.velocity();
                const auto& prim = db.inputs.conveyorPrim();
                UsdPrim conveyor;
                if (prim.size() > 0)
                {
                    conveyor = stage->GetPrimAtPath(omni::fabric::toSdfPath(prim[0]));
                }
                else
                {
                    db.logError("no prim path found for the conveyor");
                    return false;
                }

                pxr::UsdPhysicsRigidBodyAPI physics_conveyor(conveyor);
                if (physics_conveyor)
                {
                    bool isKinematic;
                    physics_conveyor.GetKinematicEnabledAttr().Get(&isKinematic);
                    if (!isKinematic)
                    {
                        physics_conveyor.GetKinematicEnabledAttr().Set(true);
                    }
                    auto m = omni::usd::UsdUtils::getWorldTransformMatrix(conveyor);
                    m.Orthonormalize();
                    pxr::GfRotation r = m.ExtractRotation();
                    pxr::GfVec3f direction = r.TransformDir(pxr::GfVec3f(db.inputs.direction()));
                    if (db.inputs.curved())
                    {
                        physics_conveyor.GetAngularVelocityAttr().Set(direction * state.mVelocity);
                    }
                    else
                    {
                        physics_conveyor.GetVelocityAttr().Set(direction * state.mVelocity);
                    }
                }

                if (state.mOnStart)
                {
                    state.mShaders.clear();
                    state.mShadersStart.clear();
                    pxr::SdfChangeBlock changeBlock;
                    for (auto m : pxr::UsdPrimRange(conveyor))
                    {
                        if (pxr::UsdGeomImageable(m))
                        {
                            auto mat = pxr::UsdShadeMaterialBindingAPI(m).ComputeBoundMaterial();
                            for (auto shader : pxr::UsdPrimRange(mat.GetPrim()))
                            {
                                auto prim = stage->OverridePrim(shader.GetPrim().GetPath());
                                auto attr = prim.GetAttribute(pxr::TfToken("inputs:texture_translate"));
                                if (!attr)
                                {
                                    pxr::UsdEditContext context(stage, stage->GetRootLayer());
                                    attr = prim.CreateAttribute(
                                        pxr::TfToken("inputs:texture_translate"), pxr::SdfValueTypeNames->Float2, true);
                                    attr.Set(pxr::GfVec2f(0.00001f, 0.0f));
                                }
                                // attr = prim.GetAttribute(pxr::TfToken("inputs:texture_translate"));
                                if (attr)
                                {
                                    pxr::UsdEditContext context(stage, stage->GetRootLayer());
                                    state.mShaders.push_back(attr);
                                    pxr::GfVec2f tx;
                                    attr.Get(&tx);
                                    state.mShadersStart.push_back(tx);
                                    tx[0] += 0.0001f;
                                    attr.Set(tx);
                                }
                            }
                        }
                    }
                }

                if (state.mOnEnd)
                {
                    for (size_t i = 0; i < state.mShaders.size(); i++)
                    {
                        state.mShaders[i].Set(state.mShadersStart[i]);
                    }
                }
            }
            if (db.inputs.animateTexture())
            {
                if (state.mVelocity != 0 && db.inputs.onStep())
                {
                    pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
                    pxr::UsdEditContext context(stage, stage->GetRootLayer());
                    pxr::SdfChangeBlock changeBlock;
                    for (auto& attr : state.mShaders)
                    {
                        pxr::GfVec2f tx;
                        attr.Get(&tx);
                        tx += pxr::GfVec2f(db.inputs.delta() * db.inputs.animateDirection() * state.mVelocity *
                                           db.inputs.animateScale());
                        attr.Set(tx);
                    }
                }
            }
        }
        return true;
    }

private:
    std::vector<pxr::UsdAttribute> mShaders;
    std::vector<pxr::GfVec2f> mShadersStart;
    float mVelocity;
    pxr::GfVec3f mDirection;
    bool mOnStart;
    bool mOnEnd;
    bool mOnsStep;
    bool mDt;
    carb::events::ISubscriptionPtr m_EventSubscription;
};

REGISTER_OGN_NODE()

}
}
}
