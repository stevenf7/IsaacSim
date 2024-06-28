// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include "LightBeamSensor.h"

#include "IsaacSensor.h"
#include "omni/isaac/utils/Pose.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <physicsSchemaTools/UsdTools.h>
#include <pxr/usd/usdPhysics/scene.h>

#include <PxActor.h>

#if defined(_WIN32)
#    include <PxArticulationLink.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <PxArticulationLink.h>
#    pragma GCC diagnostic pop
#endif

#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <map>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace sensor
{

void LightBeamSensor::onComponentChange()
{
    IsaacSensorComponentBase::onComponentChange();

    const pxr::IsaacSensorIsaacLightBeamSensor& typedPrim = (pxr::IsaacSensorIsaacLightBeamSensor)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetCurtainLengthAttr(), mCurtainLength);
    isaac::utils::safeGetAttribute(typedPrim.GetNumRaysAttr(), mNumRays);
    isaac::utils::safeGetAttribute(typedPrim.GetCurtainAxisAttr(), mCurtainAxis);
    isaac::utils::safeGetAttribute(typedPrim.GetForwardAxisAttr(), mForwardAxis);
    isaac::utils::safeGetAttribute(typedPrim.GetMinRangeAttr(), mMinRange);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxRangeAttr(), mMaxRange);

    mMetersPerUnit = static_cast<float>(UsdGeomGetStageMetersPerUnit(this->mStage));
    mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);
    mMaxDepth = mMaxRange / mMetersPerUnit;
    mMinDepth = mMinRange / mMetersPerUnit;
    mLinearDepth.assign(mNumRays, 0);
    mHitPos.assign(mNumRays, { 0, 0, 0 });
    mBeamHit.assign(mNumRays, 0);
    mBeamOrigins.assign(mNumRays, { 0, 0, 0 });
    mBeamEndPoints.assign(mNumRays, { 0, 0, 0 });

    pxr::UsdPrimRange range = this->mStage->Traverse();

    mPxScene = nullptr;
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::UsdPhysicsScene>())
        {
            mPxScene =
                static_cast<::physx::PxScene*>(mPhysx->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

            if (mPxScene)
            {
                break;
            }
        }
    }
}

void LightBeamSensor::scan(const ::physx::PxVec3& origin, const ::physx::PxQuat& worldRotation)
{
    if (!mPxScene)
    {
        return;
    }

    ::physx::PxVec3 unitDir = worldRotation.rotate(utils::conversions::asPxVec3(mForwardAxis)).getNormalized();
    ::physx::PxVec3 unitCurtain = worldRotation.rotate(utils::conversions::asPxVec3(mCurtainAxis)).getNormalized();

    auto lightbeamLambda = [&]()
    {
        // for each ray in the light curtain
        for (int ray = 0; ray < mNumRays; ray++)
        {
            // increase casting origin by unit offset
            ::physx::PxVec3 rayOffset = ray * mCurtainLength / mNumRays * unitCurtain;
            ::physx::PxRaycastHit raycastHit;

            // Calculate the start point of the ray
            ::physx::PxVec3 startPoint = origin + unitDir * mMinDepth + rayOffset;

            // Project the start point out to prevent collisions from origin
            const bool hit = ::physx::PxSceneQueryExt::raycastSingle(
                *mPxScene, startPoint, unitDir, mMaxDepth, mHitFlags, raycastHit);

            // Store the start point (in world coordinates)
            mBeamOrigins[ray] = { startPoint.x, startPoint.y, startPoint.z };

            if (hit)
            {
                mBeamHit[ray] = 1;
                // calculate the distance and position of the ray hit
                mLinearDepth[ray] = (raycastHit.distance + mMinDepth) * mMetersPerUnit; // in meters
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                mHitPos[ray] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                // Calculate and store the end point (in world coordinates)
                ::physx::PxVec3 endPoint = raycastHit.position;
                mBeamEndPoints[ray] = { endPoint.x, endPoint.y, endPoint.z };
            }
            else
            {
                mBeamHit[ray] = 0;
                mLinearDepth[ray] = mMaxDepth * mMetersPerUnit; // in meters
                ::physx::PxVec3 hitPos = origin + unitDir * (mMaxDepth + mMinDepth) + rayOffset;
                // store the end point (in world coordinates)
                mBeamEndPoints[ray] = { hitPos.x, hitPos.y, hitPos.z };
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                mHitPos[ray] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
            }
        }
    };

    // call lambda
    lightbeamLambda();
}

void LightBeamSensor::onPhysicsStep()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }

    auto worldMat = omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath());

    mWorldTranslation = utils::conversions::asPxVec3(worldMat.ExtractTranslation());
    mWorldRotation = utils::conversions::asPxQuat(worldMat.ExtractRotation());

    // run full scan
    scan(mWorldTranslation, mWorldRotation);

    if (mPreviousEnabled != this->mEnabled)
    {
        if (mEnabled)
        {
            this->onPhysicsStep(); // force on physics step to run to get up to date value
        }
        else
        {
            this->onStop();
        }
        mPreviousEnabled = this->mEnabled;
    }
}

} // sensor
} // isaac
} // omni
