// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../RangeSensorUtils.h"
#include "../core/RangeSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/Conversions.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/generic.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class GenericSensor : public RangeSensorComponent
{

public:
    GenericSensor(omni::renderer::IDebugDraw* debugDrawPtr,
                  omni::physx::IPhysx* physxPtr,
                  carb::fastcache::FastCache* fastCachePtr);
    ~GenericSensor();

    virtual void onStart();
    virtual void preTick();
    virtual void tick();
    virtual void onComponentChange();


    int getNumSamplesTicked() const
    {
        return mSamplesPerTick;
    }
    std::vector<uint16_t>& getDepthData()
    {
        return mLastDepth;
    }

    std::vector<float>& getLinearDepthData()
    {
        return mLastLinearDepth;
    }

    std::vector<uint8_t>& getIntensityData()
    {
        return mLastIntensity;
    }

    std::vector<float>& getZenithData()
    {
        return mZenith;
    }

    std::vector<float>& getAzimuthData()
    {
        return mLastAzimuth;
    }

    std::vector<carb::Float3>& getOffsetData()
    {
        return mLastOffset;
    }

    bool sendNextBatch();
    /**
     * @brief indicate whether the next batch of sensor pattern vectors should be sent
     *
     */


    void setNextBatchRays(const float* azimuth_angles, const float* zenith_angles, const int sample_length);
    /**
     *  @brief passing in the next batch of sensor pattern
     */

    void setNextBatchOffsets(const float* origin_offsets, const int sample_length);
    /**
     *  @brief if each ray has its own offset
     */

private:
    void wrapData(int start);
    void dumpData();


    bool raycastClose(const ::physx::PxVec3& pos,
                      const ::physx::PxVec3& dir,
                      float distance,
                      ::physx::PxRaycastHit& hit,
                      ::physx::PxScene* physxScene)
    {


        const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, mHitFlags, hit);
        return ret;
    }

    template <bool drawPoints, bool drawLines>
    void scan(const ::physx::PxVec3& sensor_origin,
              const ::physx::PxQuat& worldRotation,
              omni::physx::IPhysx* physxPtr,
              ::physx::PxScene* physxScenePtr,
              std::vector<uint16_t>& depth,
              std::vector<carb::Float3>& hitPosition,
              std::vector<float>& linearDepth,
              std::vector<uint8_t>& intensity,
              std::vector<float>& zenith,
              std::vector<float>& azimuth,
              std::vector<carb::Float3>& origin_offset,
              float maxDepth,
              float minDepth,
              float metersPerUnit,
              bool zUp)
    {
        if (!physxScenePtr)
        {
            return;
        }
        float invMaxDepth = 1.0f / maxDepth;
        // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up
        // vs Z up stage. So commented this out and using the pure Z up rotation version
        // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
        // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

        ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
        ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

        size_t n_scan = azimuth.size();
        for (size_t i = 0; i < n_scan; i++)
        {
            // Pitch then yaw
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(azimuth[i], azimuthDir);
            ::physx::PxQuat rot = mainrot * ::physx::PxQuat(zenith[i], zenithDir);
            ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
            ::physx::PxRaycastHit raycastHit;
            // Project the start point out to prevent collisions from origin
            ::physx::PxVec3 origin = sensor_origin + utils::conversions::asPxVec3(origin_offset[i]);
            bool hit = raycastClose(origin + unitDir * minDepth, unitDir, maxDepth, raycastHit, physxScenePtr);

            if (hit)
            {
                // the distance of the ray should be from center of lidar
                depth[i] = static_cast<uint16_t>((raycastHit.distance + minDepth) * invMaxDepth * 65535.0f);
                linearDepth[i] = (raycastHit.distance + minDepth) * metersPerUnit; // in meters
                intensity[i] = 255;

                // if (linearDepth[i] < minDepth * metersPerUnit)
                // {
                //     depth[i] = 0;
                //     linearDepth[i] = minDepth * metersPerUnit; // in meters
                //     intensity[i] = 0;
                //     continue;
                // }
                carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                // ::physx::PxVec3 hitPosRelRay = worldRotation.rotateInv(raycastHit.position - origin);
                // hitPosRay[i] = { hitPosRelRay.x, hitPosRelRay.y, hitPosRelRay.z }; // relative to the ray's origin
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - sensor_origin);
                hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor's origin, not
                                                                            // accounting for individual ray origin
                                                                            // offset
                if (drawPoints)
                {
                    carb::scenerenderer::PrimitiveVertex data;

                    // ::physx::PxVec3 diff = raycastHit.position - origin;

                    data.position = hitPos;
                    // auto temp = raycastHit.position - diff.getNormalized();
                    // set ratio for color.  should be zero at minDepth and unity at maxDepth
                    auto ratio = (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);
                    data.color = distToRgba(ratio);
                    data.width = 5.0f;
                    mPointDrawing->addVertex(data);
                }

                // else
                if (drawLines)
                {
                    carb::scenerenderer::PrimitiveVertex data;

                    ::physx::PxVec3 diff = raycastHit.position - origin;
                    auto temp = origin + diff.getNormalized() * minDepth;
                    // set ratio for color.  should be zero at minDepth and unity at maxDepth
                    auto ratio = (linearDepth[i] - minDepth * metersPerUnit) / ((maxDepth - minDepth) * metersPerUnit);

                    data.position = { temp.x, temp.y, temp.z };
                    data.color = distToRgba(ratio);
                    data.width = 1.0;

                    mLineDrawing->addVertex(data);
                    data.position = hitPos;
                    mLineDrawing->addVertex(data);
                }
            }
            else
            {
                depth[i] = 65535;
                linearDepth[i] = maxDepth * metersPerUnit; // in meters
                intensity[i] = 0;
                ::physx::PxVec3 hitPos = origin + unitDir * (maxDepth + minDepth);
                // ::physx::PxVec3 hitPosRelRay = worldRotation.rotateInv(hitPos - origin);
                // hitPosRay[i] = { hitPosRelRay.x, hitPosRelRay.y, hitPosRelRay.z }; // relative to the ray's origin
                ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - sensor_origin);
                hitPosition[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor's origin, not
                                                                            // accounting for individual ray origin
                                                                            // offset
                if (drawLines)
                {
                    carb::scenerenderer::PrimitiveVertex data;

                    auto temp = origin + unitDir * minDepth;

                    data.position = { temp.x, temp.y, temp.z };
                    data.color = { 1, 1, 1, 50.0f / 255.0f };
                    data.width = 1.0;

                    mLineDrawing->addVertex(data);
                    data.position = { hitPos.x, hitPos.y, hitPos.z };
                    mLineDrawing->addVertex(data);
                }
            }
        }
    }

    int mSamplingRate; // number of samples per second
    bool mStreaming;
    int mBatchSize = 0; // the total number of samples for each batch of data
    int minBatchSize = 0;
    int A_length = 0;
    int B_length = 0;

    int mLastSample = 0;
    int mSamplesPerTick = 60; // number of samples per tick
    int maxSamplesPerTick = 1000000;

    float mMinDepth = 0;
    float mMaxDepth = 1e8;

    std::vector<float> mAzimuth_A{}, mAzimuth_B{};
    std::vector<float> mZenith_A{}, mZenith_B{};
    std::vector<carb::Float3> mOffset_A{}, mOffset_B{};
    // bool mCustomOffset = false;


    float *pActiveAzimuth, *pActiveZenith;
    carb::Float3* pActiveOffset;

    std::vector<float> mZenith, mLastZenith;
    std::vector<float> mAzimuth, mLastAzimuth;
    std::vector<carb::Float3> mOffset, mLastOffset;

    std::vector<float> mLinearDepth, mLastLinearDepth;
    std::vector<uint8_t> mIntensity, mLastIntensity;
    std::vector<uint16_t> mDepth, mLastDepth;
    std::vector<carb::Float3> mHitPos;

    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
    ::physx::PxVec3 mFinalTranslation;
    ::physx::PxQuat mFinalRotation;
};


}
}
}
