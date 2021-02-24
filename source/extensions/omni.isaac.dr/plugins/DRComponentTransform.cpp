// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "DRComponentTransform.h"
#include "DRUtils.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <drSchema/transformComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;

DRComponentTransform::DRComponentTransform(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                                           omni::renderer::IDebugDraw* debugDrawPtr)
    : DRComponentBase(), mDynamicControlPtr(dynamicControlPtr), mDebugDrawPtr(debugDrawPtr)
{
}
DRComponentTransform::~DRComponentTransform()
{
    stop();
}
void DRComponentTransform::initialize(const pxr::DrSchemaTransformComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentTransform::onStart()
{
    CARB_LOG_INFO("DR Transform Component Started");
    mEnableLookAtTarget = false;
    if (pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z)
        mUpUsd = { 0.0, 0.0, 1.0 };
    else
        mUpUsd = { 0.0, 1.0, 0.0 };
    onComponentChange();
}
void DRComponentTransform::update()
{
    mAllPrims.clear();
    for (auto& path : mPaths)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(pxr::SdfPath(path.c_str()));
        if (prim)
            mAllPrims.push_back(prim);

        if (mIncludeChild && prim)
        {
            pxr::UsdPrimSubtreeRange range = prim.GetDescendants();
            for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
            {
                pxr::UsdPrim prim = *iter;
                mAllPrims.push_back(prim);
            }
        }
    }
}
void DRComponentTransform::onComponentChange()
{
    const pxr::DrSchemaTransformComponent& movPrim = (pxr::DrSchemaTransformComponent)mPrim;
    movPrim.GetCompNameAttr().Get(&mCompName);
    movPrim.GetTranslateMinAttr().Get(&mTranslateMin);
    movPrim.GetTranslateMaxAttr().Get(&mTranslateMax);
    movPrim.GetRotateMinAttr().Get(&mRotateMin);
    movPrim.GetRotateMaxAttr().Get(&mRotateMax);
    movPrim.GetScaleMinAttr().Get(&mScaleMin);
    movPrim.GetScaleMaxAttr().Get(&mScaleMax);
    movPrim.GetEnableLookAtTargetAttr().Get(&mEnableLookAtTarget);
    movPrim.GetLookAtTargetOffsetAttr().Get(&mLookAtTargetOffset);
    movPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    movPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    movPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    mLookAtTargetPaths.clear();
    pxr::UsdRelationship primPaths = movPrim.GetPrimPathsRel();
    pxr::UsdRelationship lookAtTargetPrimPaths = movPrim.GetLookAtTargetPathsRel();
    pxr::SdfPathVector targets, lookAtTargets;
    primPaths.GetTargets(&targets);
    lookAtTargetPrimPaths.GetTargets(&lookAtTargets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());
    for (auto target : lookAtTargets)
        mLookAtTargetPaths.push_back(target.GetString());

    mPolygonPoints.clear();
    pxr::VtArray<pxr::GfVec3f> polygonPoints;
    movPrim.GetPolygonPointsAttr().Get<pxr::VtArray<pxr::GfVec3f>>(&polygonPoints);
    for (unsigned int ind = 0; ind < polygonPoints.size(); ind++)
        mPolygonPoints.push_back(polygonPoints[ind]);

    movPrim.GetDrawPolygonAttr().Get(&mDrawPolygon);
    releaseDebugLineList(mDebugDrawPtr);
    if (mDrawPolygon && mPolygonPoints.size() > 2)
    {
        createDebugLineList(mPolygonPoints.size(), mDebugDrawPtr);
        uint32_t color = 255 + (255 << 8) + (255 << 16) + (255 << 24);
        for (unsigned int ind = 0; ind < mPolygonPoints.size() - 1; ind++)
        {
            mDebugDrawPtr->setLine(
                mShapeDebugLineBuffer, ind, { mPolygonPoints[ind][0], mPolygonPoints[ind][1], mPolygonPoints[ind][2] },
                color, { mPolygonPoints[ind + 1][0], mPolygonPoints[ind + 1][1], mPolygonPoints[ind + 1][2] }, color);
            if (ind == mPolygonPoints.size() - 2)
                mDebugDrawPtr->setLine(
                    mShapeDebugLineBuffer, ind + 1,
                    { mPolygonPoints[ind + 1][0], mPolygonPoints[ind + 1][1], mPolygonPoints[ind + 1][2] }, color,
                    { mPolygonPoints[0][0], mPolygonPoints[0][1], mPolygonPoints[0][2] }, color);
        }
    }

    mTargetPoints.clear();
    pxr::VtArray<pxr::GfVec3f> targetPoints;
    movPrim.GetTargetPointsAttr().Get<pxr::VtArray<pxr::GfVec3f>>(&targetPoints);
    for (unsigned int ind = 0; ind < targetPoints.size(); ind++)
        mTargetPoints.push_back(targetPoints[ind]);
    mLookAtTargetPoints.clear();
    pxr::VtArray<pxr::GfVec3f> lookAtTargetPoints;
    movPrim.GetLookAtTargetPointsAttr().Get<pxr::VtArray<pxr::GfVec3f>>(&lookAtTargetPoints);
    for (unsigned int ind = 0; ind < lookAtTargetPoints.size(); ind++)
        mLookAtTargetPoints.push_back(lookAtTargetPoints[ind]);
    movPrim.GetEnableSequentialBehaviorAttr().Get(&mEnableSequentialBehavior);

    update();
    CARB_LOG_INFO("Transform Update: %s", mCompName.c_str());
}
void DRComponentTransform::stop()
{
    CARB_LOG_INFO("DR Transform Component Stopped");
    releaseDebugLineList(mDebugDrawPtr);
}
pxr::GfVec3f DRComponentTransform::randomPointTriangle(std::vector<pxr::GfVec3f>& samplePoints)
{
    double r1 = randomRangeFloat(0, 1);
    double r2 = randomRangeFloat(0, 1);
    pxr::GfVec3f randomPoint =
        (1 - sqrt(r1)) * samplePoints[0] + (sqrt(r1) * (1 - r2)) * samplePoints[1] + (r2 * sqrt(r1)) * samplePoints[2];
    // CARB_LOG_WARN("New point: (%lf, %lf, %lf)", randomPoint[0], randomPoint[1], randomPoint[2]);
    return randomPoint;
}
pxr::GfVec3f DRComponentTransform::randomPointPolygon(std::vector<pxr::GfVec3f>& samplePoints)
{
    pxr::GfVec3f randomPoint(0, 0, 0);
    std::vector<std::vector<pxr::GfVec3f>> allTriangles = triangulatePolygon(samplePoints);
    std::vector<double> cumulativeAreaDistribution = generateDistribution(allTriangles);
    double randomArea = randomRangeFloat(0, 1);
    int randomIndex = 0;
    for (unsigned int i = 0; i < cumulativeAreaDistribution.size() - 1; i++)
    {
        // CARB_LOG_WARN("%lf", cumulativeAreaDistribution[i]);
        if (randomArea > cumulativeAreaDistribution[i] && randomArea <= cumulativeAreaDistribution[i + 1])
        {
            randomIndex = i;
            break;
        }
    }
    // CARB_LOG_WARN("Area: %lf, Index: %d", randomArea, randomIndex);
    return randomPointTriangle(allTriangles[randomIndex]);
}
void DRComponentTransform::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            int randIndex = -1;
            // Set random translation
            float x = randomRangeFloat(mTranslateMin[0], mTranslateMax[0]);
            float y = randomRangeFloat(mTranslateMin[1], mTranslateMax[1]);
            float z = randomRangeFloat(mTranslateMin[2], mTranslateMax[2]);
            if (mTargetPoints.size() > 0)
            {
                randIndex = randomRangeInt(0, static_cast<int>(mTargetPoints.size()) - 1);
                if (mEnableSequentialBehavior)
                    randIndex = mSequentialIndex;
                x = mTargetPoints[randIndex][0];
                y = mTargetPoints[randIndex][1];
                z = mTargetPoints[randIndex][2];
            }
            pxr::GfVec3d eyeUsd(x, y, z);
            if (mPolygonPoints.size() > 2)
            {
                pxr::GfVec3f randPoint = randomPointPolygon(mPolygonPoints);
                if (pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z)
                    eyeUsd = pxr::GfVec3d(randPoint[0], randPoint[1], z);
                else
                    eyeUsd = pxr::GfVec3d(randPoint[0], y, randPoint[2]);
            }
            pxr::GfMatrix4d currentTransformMat, finalTransformMat, scaledTransformMat, scaleMat;
            currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
            pxr::GfTransform currentTr(currentTransformMat);
            if (mEnableLookAtTarget)
            {
                // Compute transformation if look at is enabled
                pxr::GfMatrix4d matrix;
                pxr::GfVec3d averagelookAtTarget(0.0, 0.0, 0.0);
                if (mLookAtTargetPoints.size() > 0)
                {
                    if (randIndex == -1)
                        randIndex = randomRangeInt(0, static_cast<int>(mLookAtTargetPoints.size()) - 1);
                    averagelookAtTarget = mLookAtTargetPoints[randIndex];
                }
                else if (mLookAtTargetPaths.size() > 0)
                {
                    for (std::string& targetPath : mLookAtTargetPaths)
                    {
                        auto targetPrim = mStage->GetPrimAtPath(pxr::SdfPath(targetPath.c_str()));
                        pxr::GfMatrix4d targetPrimTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(targetPrim);
                        averagelookAtTarget += targetPrimTransformMat.ExtractTranslation();
                    }
                    averagelookAtTarget /= static_cast<double>(mLookAtTargetPaths.size());
                }
                averagelookAtTarget += mLookAtTargetOffset;
                matrix.SetLookAt(eyeUsd, averagelookAtTarget, mUpUsd);
                finalTransformMat = matrix.GetInverse();
            }
            else
            {
                // Get current rotation
                pxr::GfTransform bodyPose;
                bodyPose.SetTranslation(eyeUsd);
                if (mRotateMin == pxr::GfVec3f(0.0, 0.0, 0.0) && mRotateMax == pxr::GfVec3f(0.0, 0.0, 0.0))
                {
                    bodyPose.SetRotation(currentTr.GetRotation());
                }
                else
                {
                    float rotX = randomRangeFloat(mRotateMin[0], mRotateMax[0]);
                    float rotY = randomRangeFloat(mRotateMin[1], mRotateMax[1]);
                    float rotZ = randomRangeFloat(mRotateMin[2], mRotateMax[2]);
                    pxr::GfRotation rowRot(pxr::GfVec3d(1, 0, 0), rotX), pitchRot(pxr::GfVec3d(0, 1, 0), rotY),
                        yawRot(pxr::GfVec3d(0, 0, 1), rotZ);
                    bodyPose.SetRotation(rowRot * pitchRot * yawRot);
                }
                finalTransformMat = bodyPose.GetMatrix();
            }
            if (mScaleMin == pxr::GfVec3f(0.0, 0.0, 0.0) && mScaleMax == pxr::GfVec3f(0.0, 0.0, 0.0))
            {
                // Get current scale
                scaleMat.SetScale(currentTr.GetScale());
            }
            else
            {
                float scaleX = randomRangeFloat(mScaleMin[0], mScaleMax[0]);
                float scaleY = randomRangeFloat(mScaleMin[1], mScaleMax[1]);
                float scaleZ = randomRangeFloat(mScaleMin[2], mScaleMax[2]);
                pxr::GfVec3d doubleScale(scaleX, scaleY, scaleZ);
                scaleMat.SetScale(doubleScale);
            }

            // Multiply current scale with random pose
            scaledTransformMat = scaleMat * finalTransformMat;

            DcObjectType primType = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
            if (primType == omni::isaac::dynamic_control::eDcObjectArticulation ||
                primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
            {
                DcHandle rigidBodyHandle;
                if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
                {
                    DcHandle artculationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
                    mDynamicControlPtr->wakeUpArticulation(artculationHandle);
                    rigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
                }
                else if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
                {
                    rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
                }
                auto newTranslation = pxr::GfVec3f(scaledTransformMat.ExtractTranslation());
                auto pxBodyRotation = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
                DcTransform t;
                t.p = { newTranslation[0], newTranslation[1], newTranslation[2] };
                t.r = pxBodyRotation.r;
                mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
                mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
            }
            else
            {
                omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
            }
        }
    }
    if (mEnableSequentialBehavior)
    {
        mSequentialIndex++;
        if (mSequentialIndex == mTargetPoints.size())
            mSequentialIndex = 0;
    }
}

}
}
}
