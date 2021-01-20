#include "../RangeSensorUtils.h"
#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "plugins/core/UsdUtilities.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>

// #include <rangeSensorSchema/ultrasonicEmitter.h>

#include <vector>

using namespace ::physx;

namespace omni
{
namespace isaac
{
namespace range_sensor
{

// TODO: This class will eventually refer to a specific emitter prim
class UltrasonicEmitter //: public utils::ComponentBase<pxr::RangeSensorSchemaUltrasonicEmitter>
{
public:
    UltrasonicEmitter()
    {
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
               std::vector<omni::isaac::range_sensor::DebugData>& debugLines,
               std::vector<uint16_t>& depth,
               std::vector<carb::Float3>& hitPosition,
               std::vector<float>& linearDepth,
               std::vector<uint8_t>& intensity,
               USSEnvelope& envelope,
               std::vector<float>& zenith,
               std::vector<float>& azimuth,
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
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[col], azimuthDir);

            for (int row = 0; row < rows; row++)
            {
                // Pitch then yaw
                ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[row], zenithDir);
                ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
                ::physx::PxRaycastHit raycastHit;
                // Project the start point out to prevent collisions from origin
                bool hit = raycast(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);

                if (hit)
                {
                    // the distance of the ray should be from center of lidar
                    depth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                    linearDepth[i] = (raycastHit.distance + minDepth) * metersPerUnit; // in meters
                    intensity[i] = 255;
                    carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                    hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                    if (drawPoints)
                    {
                        omni::isaac::range_sensor::DebugData data;

                        ::physx::PxVec3 diff = raycastHit.position - origin;

                        data.startPos = hitPos;
                        auto temp = raycastHit.position - diff.getNormalized();
                        data.endPos = { temp.x, temp.y, temp.z };
                        // set ratio for color.  should be zero at minDepth and unity at maxDepth
                        auto ratio =
                            (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                        data.color = dist_to_color(ratio, true);
                        debugLines.push_back(data);
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
                            (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                        data.color = dist_to_color(ratio, true);
                        debugLines.push_back(data);
                    }
                }
                else
                {
                    depth[i] = 65535;
                    linearDepth[i] = maxDepth * metersPerUnit; // in meters
                    intensity[i] = 0;
                    ::physx::PxVec3 hitPos = origin + unitDir * (maxDepth + minDepth);
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                    hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
                    if (drawPoints)
                    {

                        omni::isaac::range_sensor::DebugData data;

                        ::physx::PxVec3 diff = hitPos - origin;
                        // TODO: replace lines with dots.

                        data.startPos = { hitPos.x, hitPos.y, hitPos.z };
                        auto temp = hitPos - diff.getNormalized();
                        data.endPos = { temp.x, temp.y, temp.z };
                        data.color = 255 + (255 << 8) + (255 << 16) + (255 << 24);
                        debugLines.push_back(data);
                    }

                    if (drawLines)
                    {
                        omni::isaac::range_sensor::DebugData data;

                        auto temp = origin + unitDir * minDepth;
                        data.startPos = { temp.x, temp.y, temp.z };
                        data.endPos = { hitPos.x, hitPos.y, hitPos.z };
                        data.color = 255 + (255 << 8) + (255 << 16) + (50 << 24);
                        debugLines.push_back(data);
                    }
                }

                if (zenith[row] == 0.0f)
                    ++j %= cols;
                ++i %= (cols * rows);
            }
        }
        envelope.updateEnvelope(linearDepth);
    }
    // void onComponentChange()
    // {
    //     mMetersPerUnit = static_cast<float>(UsdGeomGetStageMetersPerUnit(this->mStage));

    //     isaac::utils::safeGetAttribute(mPrim.GetHorizontalFovAttr(), mHorizontalFov);
    //     isaac::utils::safeGetAttribute(mPrim.GetVerticalFovAttr(), mVerticalFov);

    //     isaac::utils::safeGetAttribute(mPrim.GetHorizontalResolutionAttr(), mHorizontalResolution);
    //     isaac::utils::safeGetAttribute(mPrim.GetVerticalResolutionAttr(), mVerticalResolution);

    //     isaac::utils::safeGetAttribute(mPrim.GetMinRangeAttr(), mMinRange);
    //     isaac::utils::safeGetAttribute(mPrim.GetMaxRangeAttr(), mMaxRange);
    //     isaac::utils::safeGetAttribute(mPrim.GetYawOffsetAttr(), mYawOffset);

    //     isaac::utils::safeGetAttribute(mPrim.GetFiringGroupAttr(), mFiringGroup);
    //     isaac::utils::safeGetAttribute(mPrim.GetPerRayIntensityAttr(), mPerRayIntensity);

    //     // we have to have atleast one beam so the FOV can never be smaller than resolution
    //     mHorizontalResolution = pxr::GfClamp(mHorizontalResolution, 0.005f, 1024);
    //     mHorizontalFov = pxr::GfClamp(mHorizontalFov, mHorizontalResolution, 360);

    //     mVerticalResolution = pxr::GfClamp(mVerticalResolution, 0.005f, 1024);
    //     mVerticalFov = pxr::GfClamp(mVerticalFov, mVerticalResolution, 360);


    //     mMinRange = pxr::GfClamp(mMinRange, 0, 1e9f);
    //     mMaxRange = pxr::GfClamp(mMaxRange, mMinRange, 1e9f);

    //     mMinDepth = mMinRange / mMetersPerUnit;
    //     mMaxDepth = mMaxRange / mMetersPerUnit;
    // }

private:
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

    // int mFiringGroup = 0;
    // float mPerRayIntensity = 1.0;
    // float mMinRange = 0.4;
    // float mMaxRange = 100.0;
    // float mYawOffset = 0.0;
    // float mHorizontalFov = 60.0;
    // float mVerticalFov = 30.0;
    // float mHorizontalResolution = 0.4;
    // float mVerticalResolution = 4.0;

    // float mMetersPerUnit = 1.0;

    // float mMinDepth = 0.0;
    // float mMaxDepth = 1.0;


    // int mRows; // = 0,
    // int mCols; // = 0;

    // float mNumBins = 224;
};
}
}
}
