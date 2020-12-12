// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentMovement.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <drSchema/movementComponent.h>

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

DRComponentMovement::DRComponentMovement(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                                         omni::renderer::IDebugDraw* debugDrawPtr)
    : DRComponentBase(), mDynamicControlPtr(dynamicControlPtr), mDebugDrawPtr(debugDrawPtr)
{
}
DRComponentMovement::~DRComponentMovement()
{
    stop();
}
void DRComponentMovement::initialize(const pxr::DrSchemaMovementComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentMovement::onStart()
{
    CARB_LOG_INFO("DR Movement Component Started");
    mEnableLookAtTarget = false;
    if (pxr::UsdGeomGetStageUpAxis(mStage) == pxr::UsdGeomTokens->z)
        mUpUsd = { 0.0, 0.0, 1.0 };
    else
        mUpUsd = { 0.0, 1.0, 0.0 };
    onComponentChange();
}
void DRComponentMovement::update()
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
void DRComponentMovement::onComponentChange()
{
    const pxr::DrSchemaMovementComponent& movPrim = (pxr::DrSchemaMovementComponent)mPrim;
    movPrim.GetCompNameAttr().Get(&mCompName);
    movPrim.GetXRangeAttr().Get(&mXRange);
    movPrim.GetYRangeAttr().Get(&mYRange);
    movPrim.GetZRangeAttr().Get(&mZRange);
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

    update();
    CARB_LOG_INFO("Movement Update: %s", mCompName.c_str());
}
void DRComponentMovement::stop()
{
    CARB_LOG_INFO("DR Movement Component Stopped");
    releaseDebugLineList(mDebugDrawPtr);
}
pxr::GfVec3f DRComponentMovement::randomPointTriangle(std::vector<pxr::GfVec3f>& samplePoints)
{
    double r1 = randomRangeFloat(0, 1);
    double r2 = randomRangeFloat(0, 1);
    pxr::GfVec3f randomPoint =
        (1 - sqrt(r1)) * samplePoints[0] + (sqrt(r1) * (1 - r2)) * samplePoints[1] + (r2 * sqrt(r1)) * samplePoints[2];
    // CARB_LOG_WARN("New point: (%lf, %lf, %lf)", randomPoint[0], randomPoint[1], randomPoint[2]);
    return randomPoint;
}
std::vector<std::vector<pxr::GfVec3f>> triangulatePolygon(std::vector<pxr::GfVec3f>& samplePoints)
{
    std::vector<std::vector<pxr::GfVec3f>> triangulatedPolygon;
    for (unsigned int i = 0; i < samplePoints.size() - 2; i++)
    {
        std::vector<pxr::GfVec3f> triplets;
        triplets.push_back(samplePoints[i]);
        triplets.push_back(samplePoints[i + 1]);
        triplets.push_back(samplePoints[i + 2]);
        triangulatedPolygon.push_back(triplets);
    }
    return triangulatedPolygon;
}
// A utility function to find distance between two points in a plane
double dist(pxr::GfVec3f p1, pxr::GfVec3f p2)
{
    return sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]));
}
double areaTriangle(std::vector<pxr::GfVec3f> trianglePts)
{
    double a = dist(trianglePts[0], trianglePts[1]);
    double b = dist(trianglePts[1], trianglePts[2]);
    double c = dist(trianglePts[0], trianglePts[2]);
    double s = (a + b + c) / 2.0;
    return sqrt(s * (s - a) * (s - b) * (s - c));
}
std::vector<double> generateDistribution(std::vector<std::vector<pxr::GfVec3f>> allTriangles)
{
    double totalArea = 0.0;
    std::vector<double> cumulativeAreaDistribution;
    cumulativeAreaDistribution.push_back(totalArea);
    for (std::vector<pxr::GfVec3f> triangle : allTriangles)
    {
        double newArea = areaTriangle(triangle);
        totalArea += newArea;
        cumulativeAreaDistribution.push_back(totalArea);
    }
    for (unsigned int i = 0; i < cumulativeAreaDistribution.size(); i++)
        cumulativeAreaDistribution[i] /= totalArea;
    return cumulativeAreaDistribution;
}
pxr::GfVec3f DRComponentMovement::randomPointPolygon(std::vector<pxr::GfVec3f>& samplePoints)
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
void DRComponentMovement::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Set random translation
            float x = randomRangeFloat(mXRange[0], mXRange[1]);
            float y = randomRangeFloat(mYRange[0], mYRange[1]);
            float z = randomRangeFloat(mZRange[0], mZRange[1]);
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
                if (mLookAtTargetPaths.size() > 0)
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
                bodyPose.SetRotation(currentTr.GetRotation());
                finalTransformMat = bodyPose.GetMatrix();
            }
            // Get current scale
            scaleMat.SetScale(currentTr.GetScale());
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
}

}
}
}
