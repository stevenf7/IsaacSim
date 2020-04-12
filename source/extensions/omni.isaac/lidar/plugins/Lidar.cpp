// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "Lidar.h"

#include <carb/physx/physx.h>
#include <carb/InterfaceUtils.h>

#include <omni/usd/UsdUtils.h>
#include <omni/isaac/utils/Conversions.h>

using namespace physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace lidar
{


Lidar::~Lidar()
{
    mDebugLines.clear();
}

Lidar::Lidar(carb::physics::PhysX* physx_ptr,
             omni::isaac::dynamic_control::DynamicControl* dc_ptr,
             const pxr::LidarSchemaLidar& prim,
             float metersPerUnit)
{

    mPhysx = physx_ptr;
    mMetersPerUnit = metersPerUnit;

    mDynamicControlPtr = dc_ptr;

    init(prim);
}


void Lidar::init(const pxr::LidarSchemaLidar& prim)
{
    this->mPrim = prim;

    // NOTE : Gross
    // TODO : Not this
    mValid = mPrim.GetHorizontalFovAttr().HasValue() && mPrim.GetVerticalFovAttr().HasValue() &&
             mPrim.GetRotationRateAttr().HasValue() && mPrim.GetHorizontalResolutionAttr().HasValue() &&
             mPrim.GetVerticalResolutionAttr().HasValue() && mPrim.GetMinRangeAttr().HasValue() &&
             mPrim.GetMaxRangeAttr().HasValue() && mPrim.GetHighLodAttr().HasValue() &&
             mPrim.GetDrawLidarPointsAttr().HasValue();

    if (!mValid)
        return;


    // Copy over the stuff from the mPrim
    mPrim.GetHorizontalFovAttr().Get(&mHorizontalFov);
    mPrim.GetVerticalFovAttr().Get(&mVerticalFov);
    mPrim.GetRotationRateAttr().Get(&mRotationRate);
    mPrim.GetHorizontalResolutionAttr().Get(&mHorizontalResolution);
    mPrim.GetVerticalResolutionAttr().Get(&mVerticalResolution);
    mPrim.GetMinRangeAttr().Get(&mMinRange);
    mPrim.GetMaxRangeAttr().Get(&mMaxRange);
    mPrim.GetHighLodAttr().Get(&mHighLod);
    mPrim.GetDrawLidarPointsAttr().Get(&mDrawLidarPoints);

    // printf("%f %f %f %f %f %f %f %d %d\n",
    //        mHorizontalFov,
    //        mVerticalFov,
    //        mRotationRate,
    //        mHorizontalResolution,
    //        mVerticalResolution,
    //        mMinRange,
    //        mMaxRange,
    //        mHighLod,
    //        mDrawLidarPoints);


    mMinDepth = mMinRange / mMetersPerUnit;
    mMaxDepth = mMaxRange / mMetersPerUnit;

    mMaxStepSize = float(1.0 / 30.0);

    mCols = int(mHorizontalFov / mHorizontalResolution);

    // Add one so that we have symmetry
    // Otherwise we are missing one angle for the Velodyne 16 case as 30/2 = 15
    mRows = mHighLod ? int(mVerticalFov / mVerticalResolution) + 1 : 1;

    if (mRotationRate != 0.0f && mRotationRate > 1.0 / mMaxStepSize)
        mRotationRate = float(1.0 / mMaxStepSize);


    mColScanSpeed = mCols * mRotationRate;
    mMaxColsPerTick = int(mColScanSpeed * mMaxStepSize);

    mDepth.assign(mRows * mCols, 0);
    mIntensity.assign(mRows * mCols, 0);
    mZenith.assign(mRows, 0.0f);
    mAzimuth.assign(mCols, 0.0f);

    float startAzimuth = -0.5f * mHorizontalFov;
    float startZenith = -0.5f * mVerticalFov;

    for (int col = 0; col < mCols; col++)
        mAzimuth[col] = float((startAzimuth + col * mHorizontalResolution) * M_PI / 180.0f);

    for (int row = 0; row < mRows; row++)
        mZenith[row] = float((startZenith + row * mVerticalResolution) * M_PI / 180.0f);

    if (!mHighLod)
        mZenith[0] = 0.0f;

    mLastAzimuth.assign(mMaxColsPerTick, 0.0f);
    mLastDepth.assign(mRows * mMaxColsPerTick, 0);

    mLastCol = 0;
    mLastNumColsTicked = 0;
    mRemainingTime = 0.0f;

    mDebugLines.clear();

    omni::isaac::dynamic_control::DcObjectType primType =
        mDynamicControlPtr->peekObjectType(mPrim.GetPath().GetString().c_str());
    if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        omni::isaac::dynamic_control::DcHandle artculationHandle =
            mDynamicControlPtr->getArticulation(mPrim.GetPath().GetString().c_str());
        mRigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
    }
    else if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
    {
        mRigidBodyHandle = mDynamicControlPtr->getRigidBody(mPrim.GetPath().GetString().c_str());
    }
    else
    {
        mRigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    }
}

void Lidar::scan(int start, int stop)
{
    // printf("%f %f %f %f %f %f %f %d %d\n",
    //        mHorizontalFov,
    //        mVerticalFov,
    //        mRotationRate,
    //        mHorizontalResolution,
    //        mVerticalResolution,
    //        mMinRange,
    //        mMaxRange,
    //        mHighLod,
    //        mDrawLidarPoints);

    GfMatrix4d worldTransform;
    if (mRigidBodyHandle)
    {
        worldTransform = utils::conversions::asGfMatrix4d(mDynamicControlPtr->getRigidBodyPose(mRigidBodyHandle));
    }
    else
    {
        worldTransform = omni::usd::UsdUtils::getWorldTransformMatrix(mPrim.GetPrim());
    }

    // GfRotation startingRotation(GfVec3f(1.0f, 0.0f, 0.0f), 180.0f);
    // startingRotation *= worldTransform.ExtractRotation();
    GfRotation worldRotation = worldTransform.RemoveScaleShear().ExtractRotation();

    GfVec3f origin = worldTransform.Transform(GfVec3f(0.0f, 0.0f, 0.0f));


    int i = start * mRows;
    int j = start;

    for (int colPreMod = start; colPreMod < stop; colPreMod++)
    {
        for (int row = 0; row < mRows; row++)
        {
            int col = colPreMod % mCols;

            // Pitch then yaw
            GfRotation pitchYaw(GfVec3f(0.0f, 0.0f, 1.0f), mZenith[row] * 180.0f / M_PI);
            pitchYaw *= GfRotation(GfVec3f(0.0f, 1.0f, 0.0f), mAzimuth[col] * 180.0f / M_PI);


            GfRotation rot = pitchYaw;
            // rot *= startingRotation;
            rot *= worldRotation;

            GfVec3f unitDir = rot.TransformDir(GfVec3f(1.0f, 0.0f, 0.0f));

            carb::Float3 carbOrigin = { origin[0], origin[1], origin[2] };
            carb::Float3 carbUnitDir = { unitDir[0], unitDir[1], unitDir[2] };
            carb::physics::RaycastHit raycastHit;

            bool hit = mPhysx->raycastClosest(carbOrigin, carbUnitDir, mMaxDepth, raycastHit, true);

            if (hit)
            {
                mDepth[i] = uint16_t(raycastHit.distance / mMaxDepth * 65535.0f);
                mIntensity[i] = 255;

                if (mDrawLidarPoints)
                {
                    GfVec3f hitPos(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z);
                    carb::renderer::Line line;

                    line.startPosition = { origin[0], origin[1], origin[2] };
                    line.endPosition = { hitPos[0], hitPos[1], hitPos[2] };
                    line.startColor = { 0.4f, 1.0f, 1.0f, 0.5f };
                    line.endColor = { 0.4f, 1.0f, 1.0f, 0.2f };

                    mDebugLines.push_back(line);
                }
            }
            else
            {
                mDepth[i] = 65535;
                mIntensity[i] = 0;
                if (mDrawLidarPoints)
                {
                    GfVec3f hitPos = origin + unitDir * mMaxDepth;
                    carb::renderer::Line line;

                    line.startPosition = { origin[0], origin[1], origin[2] };
                    line.endPosition = { hitPos[0], hitPos[1], hitPos[2] };
                    line.startColor = { 0.0f, 0.4f, 0.4f, 1.0f };
                    line.endColor = { 0.0f, 0.4f, 0.4f, 1.0f };

                    mDebugLines.push_back(line);
                }
            }

            if (mZenith[row] == 0.0f)
                ++j %= mCols;
            ++i %= (mCols * mRows);
        }
    }
}

void Lidar::dumpData(int start, int stop, float dt)
{

    // Size of mLastDepth and mLastIntensity == mRows * mLastNumColsTicked
    // Size of mDepth, and mIntensity == mRows * mCols
    // Size of mAzimuth == mCols
    // Size of mLastAzimuth == mLastNumColsTicked

    int colsToTick = stop - start;

    int unwrappedSize = std::min(stop, mCols) - start;
    int wrappedSize = std::max(0, stop - mCols);

    mLastDepth.resize(mRows * colsToTick);
    mLastIntensity.resize(mRows * colsToTick);
    mLastAzimuth.resize(colsToTick);

    std::copy(mAzimuth.begin() + start, mAzimuth.begin() + (start + unwrappedSize), mLastAzimuth.begin());
    std::copy(mDepth.begin() + start * mRows, mDepth.begin() + (start + unwrappedSize) * mRows, mLastDepth.begin());
    std::copy(mIntensity.begin() + start * mRows, mIntensity.begin() + (start + unwrappedSize) * mRows,
              mLastIntensity.begin());

    // We wrapped around
    if (wrappedSize > 0)
    {
        std::copy(mAzimuth.begin(), mAzimuth.begin() + wrappedSize, mLastAzimuth.begin() + unwrappedSize);
        std::copy(mDepth.begin(), mDepth.begin() + wrappedSize * mRows, mLastDepth.begin() + unwrappedSize * mRows);
        std::copy(mIntensity.begin(), mIntensity.begin() + wrappedSize * mRows,
                  mLastIntensity.begin() + unwrappedSize * mRows);
    }
}


void Lidar::update(float elapsedTime)
{

    if (!mValid)
    {
        CARB_LOG_ERROR("Attempted to use an invalid Lidar, please specify all attributes on prim");
        return;
    }

    mDebugLines.clear();


    // Every tick does a full scan
    if (mRotationRate == 0.0f)
    {
        mLastNumColsTicked = mCols;

        scan(0, mCols);
        dumpData(0, mCols, elapsedTime);

        mLastCol = 0;
    }
    else
    {
        mRemainingTime += elapsedTime;


        mLastNumColsTicked = int(mColScanSpeed * mRemainingTime);

        // If too much time is remaining, cap the number of columns
        if (mLastNumColsTicked > mMaxColsPerTick)
        {
            mLastNumColsTicked = mMaxColsPerTick;
        }

        float simulateTime = mLastNumColsTicked / mColScanSpeed;
        mRemainingTime -= simulateTime;


        // In the case where we capped the number of columns, we drop from mRemainingTime
        // a multiple of mMaxStepSize
        mRemainingTime = std::fmod(mRemainingTime, mMaxStepSize);

        // Now scan the columns and dump the data
        scan(mLastCol, mLastCol + mLastNumColsTicked);
        dumpData(mLastCol, mLastCol + mLastNumColsTicked, simulateTime);

        mLastCol = (mLastCol + mLastNumColsTicked) % mCols;
    }
}


}
}
}
