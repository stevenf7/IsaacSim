// Copyright (c) 2019-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <OgnIsaacConveyorDatabase.h>

///
#include <omni/usd/UsdContext.h>
///

#include <omni/fabric/FabricUSD.h>
#include <omni/usd/UsdUtils.h>
#include <physxSchema/physxSurfaceVelocityAPI.h>
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
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& _state = OgnIsaacConveyorDatabase::sPerInstanceState<OgnIsaacConveyor>(nodeObj, instanceId);
        _state.m_EventSubscription = carb::events::createSubscriptionToPop(
            omni::usd::UsdContext::getContext()->getStageEventStream().get(),
            [nodeObj, instanceId](carb::events::IEvent* e)
            {
                auto& state = OgnIsaacConveyorDatabase::sPerInstanceState<OgnIsaacConveyor>(nodeObj, instanceId);
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
            pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
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
            // const GraphContextObj& context = db.abi_context();
            // pxr::SdfChangeBlock changeBlock(true);
            auto& state = db.perInstanceState<OgnIsaacConveyor>();
            pxr::UsdPhysicsRigidBodyAPI physics_conveyor(conveyor);
            pxr::GfVec3f velocity;
            auto new_velocity = db.inputs.direction() * db.inputs.velocity();
            if (physics_conveyor)
            {
                auto surfaceVelocity = pxr::PhysxSchemaPhysxSurfaceVelocityAPI::Apply(conveyor);

                if (db.inputs.curved())
                {
                    surfaceVelocity.GetSurfaceAngularVelocityAttr().Get(&velocity);
                }
                else
                {
                    surfaceVelocity.GetSurfaceVelocityAttr().Get(&velocity);
                }
            }
            else
            {
                db.logError("Selected Prim is not a Rigid Body");
                return false;
            }
            bool velocity_changed = (velocity - new_velocity).GetLengthSq() > 1e-6f;
            if (state.mOnStart || velocity_changed)
            {
                state.mVelocity = db.inputs.velocity();

                auto surfaceVelocity = pxr::PhysxSchemaPhysxSurfaceVelocityAPI::Apply(conveyor);
                // Cycle the enabled attr to hardwire it to work on first sim
                surfaceVelocity.GetSurfaceVelocityEnabledAttr().Set(false);
                surfaceVelocity.GetSurfaceVelocityEnabledAttr().Set(true);
                if (db.inputs.curved())
                {
                    surfaceVelocity.GetSurfaceAngularVelocityAttr().Set(new_velocity);
                }
                else
                {
                    surfaceVelocity.GetSurfaceVelocityAttr().Set(new_velocity);
                }


                if (state.mOnStart)
                {
                    state.mOnStart = false;
                    state.mShaders.clear();
                    state.mShadersStart.clear();
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
                                    attr = prim.CreateAttribute(pxr::TfToken("inputs:texture_translate"),
                                                                pxr::SdfValueTypeNames->Float2, false);
                                    attr.Set(pxr::GfVec2f(0.00000f, 0.0f));
                                }
                                // attr = prim.GetAttribute(pxr::TfToken("inputs:texture_translate"));
                                if (attr)
                                {
                                    pxr::UsdEditContext context(stage, stage->GetRootLayer());
                                    state.mShaders.push_back(attr);
                                    pxr::GfVec2f tx;
                                    attr.Get(&tx);
                                    state.mShadersStart.push_back(tx);
                                    tx[0] += 0.0000f;
                                    attr.Set(tx);
                                }
                            }
                        }
                    }
                }

                if (state.mOnEnd)
                {
                    pxr::SdfChangeBlock changeBlock;
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
