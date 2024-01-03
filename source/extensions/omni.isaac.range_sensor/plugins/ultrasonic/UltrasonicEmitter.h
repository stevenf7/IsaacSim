// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/usd/UtilsIncludes.h>

#include <Color.h>
//
#include <omni/usd/UsdUtils.h>
//
#include "omni/isaac/utils/ScopedTimer.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/isaac/utils/Pose.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/timeline/ITimeline.h>
#include <pxr/usd/usd/inherits.h>
#include <pxr/usd/usdPhysics/materialAPI.h>
#include <rangeSensorSchema/ultrasonicEmitter.h>
#include <rangeSensorSchema/ultrasonicMaterialAPI.h>

#include <RangeSensorInterface.h>
#include <vector>

using namespace ::physx;
using namespace pxr;
using namespace carb;

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class UltrasonicEmitter : public utils::ComponentBase<pxr::RangeSensorUltrasonicEmitter>
{
public:
    UltrasonicEmitter()
    {
        mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
    }

    ::physx::PxVec3 getOrigin()
    {
        return mOrigin;
    }
    ::physx::PxTransform getPose()
    {
        return ::physx::PxTransform(mOrigin, mTheta0);
    }

    inline const pxr::SdfPath& intToPath(const uint64_t& path)
    {
        static_assert(sizeof(pxr::SdfPath) == sizeof(uint64_t), "Change to make the same size as pxr::SdfPath");

        return reinterpret_cast<const pxr::SdfPath&>(path);
    }


    pxr::SdfPath getMaterialBinding(const pxr::UsdStageWeakPtr stage, const pxr::UsdPrim& usdPrim)
    {
        SdfPath materialPath;

        UsdShadeMaterialBindingAPI materialBindingAPI = UsdShadeMaterialBindingAPI(usdPrim);
        if (materialBindingAPI)
        {
            const static TfToken physicsPurpose("physics");
            UsdShadeMaterialBindingAPI::DirectBinding binding = materialBindingAPI.GetDirectBinding(physicsPurpose);
            return binding.GetMaterialPath();
        }
        else
        {
            // handle material through a direct binding rel search
            UsdRelationship materialRel;
            SdfPathVector materials;
            static TfToken materialPhysicsBinding("material:binding:physics");
            materialRel = usdPrim.GetRelationship(materialPhysicsBinding);
            if (materialRel)
                materialRel.GetTargets(&materials);

            if (materials.size() != 0)
            {
                return materials[0].GetPrimPath();
            }
        }

        return SdfPath();
    }

    void updatePose()
    {

        mParentPrimTimeCode = pxr::UsdTimeCode::Default();
        if (mIsParentPrimTimeSampled)
        {
            mParentPrimTimeCode = round(mTimeline->getCurrentTime() * mStage->GetTimeCodesPerSecond());
        }


        auto worldMat = omni::isaac::utils::pose::computeWorldXformNoCache(
            mStage, mUsdrtStage, mPrim.GetPath(), mParentPrimTimeCode);

        mOrigin = utils::conversions::asPxVec3(worldMat.ExtractTranslation());
        mTheta0 = utils::conversions::asPxQuat(worldMat.ExtractRotation());
    }
    void doScan(float maxDepth, float minDepth, ::physx::PxScene* pxScenePtr)
    {
        mPxScene = pxScenePtr;

        if (!mPxScene)
        {
            return;
        }

        // mHitPosWorld.clear();
        // mNormals.clear();

        bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;
        if (mDrawLines && mDrawPoints)
        {
            scan_<true, true>(mRows, mCols, mOrigin, mTheta0, mZenith, mAzimuth, maxDepth, minDepth, zUp);
        }
        else if (mDrawLines)
        {
            scan_<false, true>(mRows, mCols, mOrigin, mTheta0, mZenith, mAzimuth, maxDepth, minDepth, zUp);
        }
        else if (mDrawPoints)
        {
            scan_<true, false>(mRows, mCols, mOrigin, mTheta0, mZenith, mAzimuth, maxDepth, minDepth, zUp);
        }
        else
        {
            scan_<false, false>(mRows, mCols, mOrigin, mTheta0, mZenith, mAzimuth, maxDepth, minDepth, zUp);
        }
    }

    template <bool drawPoints, bool drawLines>
    void scan_(int rows,
               int cols,
               const ::physx::PxVec3& origin,
               const ::physx::PxQuat& worldRotation,
               std::vector<float>& zenith,
               std::vector<float>& azimuth,
               float maxDepth,
               float minDepth,
               bool zUp)
    {

        int i = 0;
        float invMaxDepth = 1.0f / maxDepth;
        // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up
        // vs Z up stage. So commented this out and using the pure Z up rotation version
        // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
        // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

        ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
        ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);


        for (int col = 0; col < cols; col++)
        {
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[col] + mYawOffset, azimuthDir);

            for (int row = 0; row < rows; row++)
            {
                // Pitch then yaw
                ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[row], zenithDir);
                ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
                ::physx::PxRaycastHit raycastHit;
                // Project the start point out to prevent collisions from origin
                bool hit = raycast(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, mPxScene);

                if (hit)
                {
                    const omni::physx::usdparser::ObjectId bodyIndex =
                        (omni::physx::usdparser::ObjectId)raycastHit.actor->userData;
                    mHitPrims[i] = mPhysx->getPhysXObjectUsdPath(bodyIndex);

                    auto hitPrim = mStage->GetPrimAtPath(mHitPrims[i]);
                    auto physicsMaterialPath = getMaterialBinding(mStage, hitPrim);

                    if (!physicsMaterialPath.IsEmpty() &&
                        mStage->GetPrimAtPath(physicsMaterialPath).HasAPI<pxr::RangeSensorUltrasonicMaterialAPI>())
                    {
                        auto ussHitMaterial = pxr::RangeSensorUltrasonicMaterialAPI::Get(mStage, physicsMaterialPath);
                        ussHitMaterial.GetPerceptualRoughnessAttr().Get(&mHitMaterials[i].x);
                        ussHitMaterial.GetReflectanceAttr().Get(&mHitMaterials[i].y);
                        ussHitMaterial.GetMetallicAttr().Get(&mHitMaterials[i].z);
                        ussHitMaterial.GetBase_colorAttr().Get(&mHitMaterials[i].w);
                    }

                    mHitPosWorld[i] = raycastHit.position;
                    mNormals[i] = raycastHit.normal;

                    // the distance of the ray should be from center of lidar
                    mDepth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                    mLinearDepth[i] = (raycastHit.distance + minDepth) * mMetersPerUnit; // in meters
                    mIntensity[i] = 255;
                    carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location

                    if (drawPoints)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        // ::physx::PxVec3 diff = raycastHit.position - origin;

                        data.position = hitPos;
                        // auto temp = raycastHit.position - diff.getNormalized();
                        // data.endPos = { temp.x, temp.y, temp.z };
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (mLinearDepth[i] - minDepth * mMetersPerUnit) / ((maxDepth - minDepth) * mMetersPerUnit);
                        data.color = omni::isaac::utils::color::distToRgba(ratio);
                        data.width = 5.0;
                        mPoints[i] = data;
                    }

                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;
                        ::physx::PxVec3 diff = raycastHit.position - origin;
                        auto temp = origin + diff.getNormalized() * minDepth;
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (mLinearDepth[i] - minDepth * mMetersPerUnit) / ((maxDepth - minDepth) * mMetersPerUnit);

                        data.position = { temp.x, temp.y, temp.z };
                        data.color = omni::isaac::utils::color::distToRgba(ratio);
                        data.width = 1.0;

                        mLines[i * 2 + 0] = data;
                        data.position = hitPos;
                        mLines[i * 2 + 1] = data;
                    }
                }
                else
                {
                    mDepth[i] = 65535;
                    mLinearDepth[i] = maxDepth * mMetersPerUnit; // in meters
                    mIntensity[i] = 0;
                    ::physx::PxVec3 hitPos = origin + unitDir * (maxDepth + minDepth);
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };

                    mHitPosWorld[i] = ::physx::PxVec3(0, 0, 0);
                    mNormals[i] = ::physx::PxVec3(0, 0, 0);
                    mHitPrims[i] = pxr::SdfPath();
                    mHitMaterials[i] = PxVec4(0, 0, 0, 0);
                    if (drawPoints)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        // ::physx::PxVec3 diff = raycastHit.position - origin;
                        data.position = { origin.x, origin.y, origin.z };
                        // auto temp = raycastHit.position - diff.getNormalized();
                        // data.endPos = { temp.x, temp.y, temp.z };
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (mLinearDepth[i] - minDepth * mMetersPerUnit) / ((maxDepth - minDepth) * mMetersPerUnit);
                        data.color = omni::isaac::utils::color::distToRgba(ratio);
                        data.width = 5.0;
                        mPoints[i] = data;
                    }
                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        auto temp = origin + unitDir * minDepth;


                        data.position = { temp.x, temp.y, temp.z };
                        data.color = { 1, 1, 1, 50.0f / 255.0f };
                        data.width = 1.0;

                        mLines[i * 2 + 0] = data;
                        data.position = { hitPos.x, hitPos.y, hitPos.z };
                        mLines[i * 2 + 1] = data;
                    }
                }


                ++i;
            }
        }

        /*
        // direct so intensities are all 1.f
        std::vector<float> intensities(mLinearDepth.size(), 1.f);
        std::vector<float> totalDepth;
        // updateInterface takes _round trip_ depth, not one way
        // hence we pass double the linear depth of the direct ray
        // from sensor to ray's collision point
        for (size_t i = 0; i < mLinearDepth.size(); i++)
        {
            totalDepth.push_back(mLinearDepth[i] * 2.f);
        }
        mEnvelope->updateEnvelope(totalDepth, intensities);*/
    }

    void initialize(const pxr::RangeSensorUltrasonicEmitter& prim,
                    pxr::UsdStageWeakPtr stage,
                    omni::physx::IPhysx* physxPtr,
                    const size_t numBins,
                    const float maxDepth,
                    const int rows,
                    const int cols,
                    bool drawLines,
                    bool drawPoints,
                    const std::vector<float>& zenith,
                    const std::vector<float>& azimuth)
    {
        utils::ComponentBase<pxr::RangeSensorUltrasonicEmitter>::initialize(prim, stage);

        mPhysx = physxPtr;

        mRows = rows;
        mCols = cols;
        mNumBins = numBins;

        mEnvelopeLow = std::make_unique<USSEnvelope>(numBins, maxDepth);
        mEnvelopeHigh = std::make_unique<USSEnvelope>(numBins, maxDepth);
        mEnvelopeCombined = std::make_unique<USSEnvelope>(numBins, maxDepth);
        mLinearDepth.resize(mRows * mCols);
        mIntensity.resize(mRows * mCols);
        mDepth.resize(mRows * mCols);
        mHitPos.resize(mRows * mCols);
        mHitPosWorld.resize(mRows * mCols);
        mNormals.resize(mRows * mCols);
        mHitPrims.resize(mRows * mCols);
        mHitMaterials.resize(mRows * mCols);
        mLinearDepth.assign(mRows * mCols, 0);
        mIntensity.assign(mRows * mCols, 0);
        mDepth.assign(mRows * mCols, 0);
        mHitPos.assign(mRows * mCols, { 0, 0, 0 });
        mHitPosWorld.assign(mRows * mCols, ::physx::PxVec3(0, 0, 0));
        mNormals.assign(mRows * mCols, ::physx::PxVec3(0, 0, 0));
        onComponentChange();

        mLines.resize(mRows * mCols * 2); // 2 points per line
        mPoints.resize(mRows * mCols);


        mDrawLines = drawLines;
        mDrawPoints = drawPoints;
        mZenith = zenith;
        mAzimuth = azimuth;
    }


    void onStart()
    {
    }

    void tick()
    {
    }

    void onComponentChange()
    {
        mMetersPerUnit = static_cast<float>(UsdGeomGetStageMetersPerUnit(this->mStage));
        isaac::utils::safeGetAttribute(mPrim.GetYawOffsetAttr(), mYawOffset);
        isaac::utils::safeGetAttribute(mPrim.GetPerRayIntensityAttr(), mPerRayIntensity);
        isaac::utils::safeGetAttribute(mPrim.GetAdjacencyListAttr(), mAdjacencyList);

        mParentPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();

        if (mParentPrim.IsA<pxr::UsdGeomXformable>())
        {
            std::vector<double> times;
            pxr::UsdGeomXformable(mParentPrim).GetTimeSamples(&times);

            mIsParentPrimTimeSampled = times.size() > 1;
        }
    }

    std::vector<float>& getEnvelope()
    {
        // return mEnvelope->getEnvelope();
        return mEnvelopeCombined->getEnvelope();
    }

    std::vector<float>& getEnvelopeLow()
    {
        return mEnvelopeLow->getEnvelope();
    }

    std::vector<float>& getEnvelopeHigh()
    {
        return mEnvelopeHigh->getEnvelope();
    }

    void setEnvelopes(USSEnvelope& low, USSEnvelope& high, const bool isReceivingLow, const bool isReceivingHigh)
    {
        if (isReceivingLow)
        {
            mEnvelopeLow = std::make_unique<USSEnvelope>(low);
        }
        else
        {
            USSEnvelope dummy(mNumBins, -1.1f);
            dummy.isValid = false;
            mEnvelopeLow = std::make_unique<USSEnvelope>(dummy);
        }
        if (isReceivingHigh)
        {
            mEnvelopeHigh = std::make_unique<USSEnvelope>(high);
        }
        else
        {
            USSEnvelope dummy(mNumBins, -1.1f);
            dummy.isValid = false;
            mEnvelopeHigh = std::make_unique<USSEnvelope>(dummy);
        }

        if (isReceivingLow && isReceivingHigh)
        {
            mEnvelopeCombined = std::make_unique<USSEnvelope>(low + high);
        }
        else if (isReceivingLow)
        {
            mEnvelopeCombined = std::make_unique<USSEnvelope>(low);
        }
        else
        {
            mEnvelopeCombined = std::make_unique<USSEnvelope>(high);
        }
    }


    std::vector<float> mLinearDepth;
    std::vector<uint8_t> mIntensity;
    std::vector<uint16_t> mDepth;
    std::vector<carb::Float3> mHitPos;
    std::vector<::physx::PxVec3> mHitPosWorld;
    std::vector<::physx::PxVec3> mNormals;
    std::vector<::physx::PxVec4> mHitMaterials;
    std::vector<pxr::SdfPath> mHitPrims;
    pxr::VtArray<int> mAdjacencyList;
    int mRows = 0;
    int mCols = 0;
    size_t mNumBins = 0;
    std::vector<carb::scenerenderer::PrimitiveVertex> mLines;
    std::vector<carb::scenerenderer::PrimitiveVertex> mPoints;

private:
    std::unique_ptr<USSEnvelope> mEnvelopeCombined;
    std::unique_ptr<USSEnvelope> mEnvelopeLow;
    std::unique_ptr<USSEnvelope> mEnvelopeHigh;

    bool raycast(const ::physx::PxVec3& pos,
                 const ::physx::PxVec3& dir,
                 float distance,
                 ::physx::PxRaycastHit& hit,
                 ::physx::PxScene* physxScene)
    {


        const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, mHitFlags, hit);
        return ret;
    }
    float mYawOffset = 0.0f;

    float mPerRayIntensity = 1.0f;
    float mMetersPerUnit = 1.0f;

    pxr::UsdPrim mParentPrim;
    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
    omni::physx::IPhysx* mPhysx = nullptr;
    ::physx::PxScene* mPxScene = nullptr;
    omni::timeline::ITimeline* mTimeline = nullptr;
    bool mDrawLines = false;
    bool mDrawPoints = false;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth;
    ::physx::PxVec3 mOrigin;
    ::physx::PxQuat mTheta0;

    pxr::UsdTimeCode mParentPrimTimeCode;
    bool mIsParentPrimTimeSampled = false;
};
}
}
}
