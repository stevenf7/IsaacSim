// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/RangeSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/Color.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/lidar.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class LidarSensor : public RangeSensorComponent
{

public:
    LidarSensor(omni::renderer::IDebugDraw* debugDrawPtr,
                omni::physx::IPhysx* physxPtr,
                omni::syntheticdata::SyntheticData* syntheticDataPtr);
    ~LidarSensor();

    virtual void onStart();
    virtual void preTick();
    virtual void tick();
    virtual void onComponentChange();

    int getNumCols() const
    {
        return mCols;
    }

    int getNumRows() const
    {
        return mRows;
    }

    int getNumColsTicked() const
    {
        return mLastNumColsTicked;
    }

    std::vector<uint16_t>& getDepthData()
    {
        return mLastDepth;
    }

    std::vector<float>& getBeamTimeData()
    {
        return mLastBeamTime;
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

    std::vector<std::string>& getPrimData()
    {
        return mLastPrimData;
    }

    carb::Float2 getAzimuthRange()
    {
        return mAzimuthRange;
    }

    carb::Float2 getZenithRange()
    {
        return mZenithRange;
    }

private:
    void dumpData(int start, int stop, double elapsedTime);

    template <bool drawPoints, bool drawLines, bool enableSemantics>
    void scan(int start,
              int stop,
              int rows,
              int cols,
              const ::physx::PxVec3& origin,
              const ::physx::PxQuat& worldRotation,
              bool zUp)
    {
        if (!mPxScene)
        {
            return;
        }
        float invMaxDepth = 1.0f / mMaxDepth;
        // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up
        // vs Z up stage. So commented this out and using the pure Z up rotation version
        // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
        // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

        ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
        ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

        auto lidarLambda = [&](int colPreMod)
        {
            int col = colPreMod % cols;
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(mAzimuth[col], azimuthDir);

            for (int row = 0; row < rows; row++)
            {
                int i = row + colPreMod * rows % (rows * cols);

                // Time will be the same for all beams in this bucket - note beams are not interpolated over frame.
                mBeamTime[i] = static_cast<float>(mTimeSeconds);
                // Pitch then yaw
                ::physx::PxQuat rot = mainrot * ::physx::PxQuat(mZenith[row], zenithDir);
                ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
                ::physx::PxRaycastHit raycastHit;
                // Project the start point out to prevent collisions from origin

                const bool hit = ::physx::PxSceneQueryExt::raycastSingle(
                    *mPxScene, origin + unitDir * mMinDepth, unitDir, mMaxDepth, mHitFlags, raycastHit);

                if (hit)
                {
                    // the distance of the ray should be from center of lidar
                    mDepth[i] = static_cast<uint16_t>((raycastHit.distance + mMinDepth) * invMaxDepth * 65535.0f);
                    mLinearDepth[i] = (raycastHit.distance + mMinDepth) * mMetersPerUnit; // in meters
                    mIntensity[i] = 255;

                    carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                    if (enableSemantics)
                    {
                        const char* hitActorName = raycastHit.actor->getName();
                        mPrimData[i] = hitActorName;
                    }
                    if (drawPoints)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        // ::physx::PxVec3 diff = raycastHit.position - origin;

                        // auto temp = raycastHit.position - diff.getNormalized();
                        // set ratio for color.  should be zero at mMinDepth and unity at mMaxDepth
                        auto ratio =
                            (mLinearDepth[i] - mMinDepth * mMetersPerUnit) / ((mMaxDepth - mMinDepth) * mMetersPerUnit);

                        data.position = hitPos;
                        data.color = omni::isaac::utils::color::distToRgba(ratio);
                        data.width = 5.0;

                        mPointDrawing->addVertex(data);
                        // data.position = { temp.x, temp.y, temp.z };
                        // mPointDrawing->addVertex(data);
                    }

                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        ::physx::PxVec3 diff = raycastHit.position - origin;
                        auto temp = origin + diff.getNormalized() * mMinDepth;
                        // set ratio for color.  should be zero at mMinDepth and unity at mMaxDepth
                        auto ratio =
                            (mLinearDepth[i] - mMinDepth * mMetersPerUnit) / ((mMaxDepth - mMinDepth) * mMetersPerUnit);

                        data.position = { temp.x, temp.y, temp.z };
                        data.color = omni::isaac::utils::color::distToRgba(ratio);
                        data.width = 1.0;

                        mLineDrawing->addVertex(data);
                        data.position = hitPos;
                        mLineDrawing->addVertex(data);
                    }
                }
                else
                {
                    mDepth[i] = 65535;
                    mLinearDepth[i] = mMaxDepth * mMetersPerUnit; // in meters
                    mIntensity[i] = 0;
                    ::physx::PxVec3 hitPos = origin + unitDir * (mMaxDepth + mMinDepth);
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        auto temp = origin + unitDir * mMinDepth;

                        data.position = { temp.x, temp.y, temp.z };
                        data.color = { 1, 1, 1, 50.0f / 255.0f };
                        data.width = 1.0;

                        mLineDrawing->addVertex(data);
                        data.position = { hitPos.x, hitPos.y, hitPos.z };
                        mLineDrawing->addVertex(data);
                    }
                }
            }
        };
        if (drawLines || drawPoints || enableSemantics)
        {
            for (int colPreMod = start; colPreMod < stop; colPreMod++)
            {
                lidarLambda(colPreMod);
            }
        }
        else
        {
            mTasking->parallelFor(start, stop, lidarLambda);
        }
    }

    // From the prim
    float mRotationRate = 20.0f;
    bool mHighLod = true;
    float mHorizontalFov = 360.0f;
    float mVerticalFov = 30.0f;
    float mHorizontalResolution = 0.4f;
    float mVerticalResolution = 4.0f;
    float mYawOffset = 0.0f;

    // Ranges converted to proper units
    float mMinDepth = 0;
    float mMaxDepth = 1e8;
    float mMaxStepSize = 0;
    int mMaxColsPerTick = 0;
    int mLastCol = 0;
    float mColScanSpeed = 0;
    double mRemainingTime = 0;


    int mRows = 0, mCols = 0;
    int mLastNumColsTicked = 0;

    std::vector<float> mZenith;
    std::vector<float> mAzimuth, mLastAzimuth;

    carb::Float2 mAzimuthRange;
    carb::Float2 mZenithRange;

    std::vector<float> mBeamTime, mLastBeamTime;
    std::vector<float> mLinearDepth, mLastLinearDepth;
    std::vector<uint8_t> mIntensity, mLastIntensity;

    std::vector<uint16_t> mDepth, mLastDepth;
    std::vector<carb::Float3> mHitPos;

    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
    ::physx::PxVec3 mFinalTranslation;
    ::physx::PxQuat mFinalRotation;

    omni::syntheticdata::SyntheticData* mSyntheticDataPtr = nullptr;
    bool mEnableSemantics;
    std::vector<std::string> mPrimData, mLastPrimData;
};


}
}
}
