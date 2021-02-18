#include "../RangeSensorUtils.h"
#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "plugins/core/UsdUtilities.h"

#include <omni/usd/UtilsIncludes.h>
//
#include <omni/usd/UsdUtils.h>
//
#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/ultrasonicEmitter.h>

#include <vector>

using namespace ::physx;

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class UltrasonicEmitter : public utils::ComponentBase<pxr::RangeSensorSchemaUltrasonicEmitter>
{
public:
    UltrasonicEmitter()
    {
    }

    ::physx::PxVec3 getOrigin(carb::fastcache::FastCache* fastCachePtr)
    {
        carb::fastcache::Transform parentTrans;
        parentTrans.orientation = { 0, 0, 0, 1 };
        auto lidarLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));
        ::physx::PxVec3 origin = utils::conversions::asPxVec3(lidarLocalTrans.ExtractTranslation());
        ::physx::PxQuat theta0 = utils::conversions::asPxQuat(lidarLocalTrans.ExtractRotation().GetQuat());
        // Make sure the parent prim has a transform, otherwise use local transform from the lidar prim itself
        if (mParentPrim.IsA<pxr::UsdGeomXformable>())
        {
            fastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);
            ::physx::PxQuat parentRot = utils::conversions::asPxQuat(parentTrans.orientation);
            origin = utils::conversions::asPxVec3(parentTrans.position) + parentRot.rotate(origin);
            theta0 = parentRot * theta0;
        }
        return origin;
    }

    void doScan(carb::fastcache::FastCache* fastCachePtr,
                omni::physx::IPhysx* physxPtr,
                ::physx::PxScene* physxScenePtr,
                std::vector<float>& zenith,
                std::vector<float>& azimuth,
                float maxDepth,
                float minDepth)
    {

        carb::fastcache::Transform parentTrans;
        parentTrans.orientation = { 0, 0, 0, 1 };
        auto lidarLocalTrans = omni::usd::UsdUtils::getLocalTransformMatrix(mStage->GetPrimAtPath(mPrim.GetPath()));
        ::physx::PxVec3 origin = utils::conversions::asPxVec3(lidarLocalTrans.ExtractTranslation());
        ::physx::PxQuat theta0 = utils::conversions::asPxQuat(lidarLocalTrans.ExtractRotation().GetQuat());
        // Make sure the parent prim has a transform, otherwise use local transform from the lidar prim itself
        if (mParentPrim.IsA<pxr::UsdGeomXformable>())
        {
            fastCachePtr->getTransform(mParentPrim.GetPath(), parentTrans);
            ::physx::PxQuat parentRot = utils::conversions::asPxQuat(parentTrans.orientation);
            origin = utils::conversions::asPxVec3(parentTrans.position) + parentRot.rotate(origin);
            theta0 = parentRot * theta0;
        }

        bool zUp = pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z;

        scan_<true, true>(0, mCols, mRows, mCols, origin, theta0, physxPtr, physxScenePtr, zenith, azimuth, mYawOffset,
                          maxDepth, minDepth, mMetersPerUnit, zUp);
    }

    template <bool drawPoints, bool drawLines>
    void scan_(int start,
               int stop,
               int rows,
               int cols,
               const ::physx::PxVec3& origin,
               const ::physx::PxQuat& worldRotation,
               omni::physx::IPhysx* physxPtr,
               ::physx::PxScene* physxScenePtr,
               std::vector<float>& zenith,
               std::vector<float>& azimuth,
               float yawOffset,
               float maxDepth,
               float minDepth,
               float metersPerUnit,
               bool zUp)
    {

        int i = start * rows;
        int j = start;
        float invMaxDepth = 1.0f / maxDepth;
        // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up
        // vs Z up stage. So commented this out and using the pure Z up rotation version
        // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
        // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

        ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
        ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

        for (int colPreMod = start; colPreMod < stop; colPreMod++)
        {
            int col = colPreMod % cols;
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[col] + yawOffset, azimuthDir);

            for (int row = 0; row < rows; row++)
            {
                // Pitch then yaw
                ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[row], zenithDir);
                ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
                ::physx::PxRaycastHit raycastHit;
                // Project the start point out to prevent collisions from origin
                bool hit = raycast(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);
                mHitPosWorld[i] = raycastHit.position;

                if (hit)
                {
                    // the distance of the ray should be from center of lidar
                    mDepth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                    mLinearDepth[i] = (raycastHit.distance + minDepth) * metersPerUnit; // in meters
                    mIntensity[i] = 255;
                    carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location

                    if (drawPoints)
                    {
                        omni::isaac::range_sensor::DebugData data;

                        ::physx::PxVec3 diff = raycastHit.position - origin;

                        data.startPos = hitPos;
                        auto temp = raycastHit.position - diff.getNormalized();
                        data.endPos = { temp.x, temp.y, temp.z };
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (mLinearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                        data.color = dist_to_color(ratio, true);
                        mEmitterDebugLines.push_back(data);
                    }

                    if (drawLines)
                    {
                        omni::isaac::range_sensor::DebugData data;
                        ::physx::PxVec3 diff = raycastHit.position - origin;
                        auto temp = origin + diff.getNormalized() * minDepth;
                        data.startPos = { temp.x, temp.y, temp.z };
                        data.endPos = hitPos;
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (mLinearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                        data.color = dist_to_color(ratio, true);
                        mEmitterDebugLines.push_back(data);
                    }
                }
                else
                {
                    mDepth[i] = 65535;
                    mLinearDepth[i] = maxDepth * metersPerUnit; // in meters
                    mIntensity[i] = 0;
                    ::physx::PxVec3 hitPos = origin + unitDir * (maxDepth + minDepth);
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
                    if (drawPoints)
                    {

                        omni::isaac::range_sensor::DebugData data;

                        ::physx::PxVec3 diff = hitPos - origin;
                        // TODO: replace lines with dots.

                        data.startPos = { hitPos.x, hitPos.y, hitPos.z };
                        auto temp = hitPos - diff.getNormalized();
                        data.endPos = { temp.x, temp.y, temp.z };
                        data.color = 255 + (255 << 8) + (255 << 16) + (255 << 24);
                        mEmitterDebugLines.push_back(data);
                    }

                    if (drawLines)
                    {
                        omni::isaac::range_sensor::DebugData data;

                        auto temp = origin + unitDir * minDepth;
                        data.startPos = { temp.x, temp.y, temp.z };
                        data.endPos = { hitPos.x, hitPos.y, hitPos.z };
                        data.color = 255 + (255 << 8) + (255 << 16) + (50 << 24);
                        mEmitterDebugLines.push_back(data);
                    }
                }

                if (zenith[row] == 0.0f)
                    ++j %= cols;
                ++i %= (cols * rows);
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

    void initialize(const pxr::RangeSensorSchemaUltrasonicEmitter& prim,
                    pxr::UsdStageWeakPtr stage,
                    const size_t numBins,
                    const float maxDepth,
                    const int rows,
                    const int cols)
    {
        utils::ComponentBase<pxr::RangeSensorSchemaUltrasonicEmitter>::initialize(prim, stage);

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

        mLinearDepth.assign(mRows * mCols, 0);
        mIntensity.assign(mRows * mCols, 0);
        mDepth.assign(mRows * mCols, 0);
        mHitPos.assign(mRows * mCols, { 0, 0, 0 });
        mHitPosWorld.assign(mRows * mCols, { 0, 0, 0 });
        onComponentChange();
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


    std::vector<omni::isaac::range_sensor::DebugData> mEmitterDebugLines;
    std::vector<float> mLinearDepth;
    std::vector<uint8_t> mIntensity;
    std::vector<uint16_t> mDepth;
    std::vector<carb::Float3> mHitPos;
    std::vector<::physx::PxVec3> mHitPosWorld;
    pxr::VtArray<int> mAdjacencyList;
    int mRows = 0;
    int mCols = 0;
    size_t mNumBins = 0;

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

        if (!physxScene)
        {
            return false;
        }

        ::physx::PxHitFlags hitFlags = PxHitFlag::eDEFAULT | PxHitFlag::eMESH_BOTH_SIDES;
        const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
        return ret;
    }
    float mYawOffset = 0.0f;

    float mPerRayIntensity = 1.0f;
    float mMetersPerUnit = 1.0f;

    pxr::UsdPrim mParentPrim;
};
}
}
}
