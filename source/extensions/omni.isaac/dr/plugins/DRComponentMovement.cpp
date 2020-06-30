// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentMovement.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/movementComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentMovement::DRComponentMovement() : DRComponentBase()
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

    update();
    CARB_LOG_INFO("Movement Update: %s", mCompName.c_str());
}
void DRComponentMovement::stop()
{
    CARB_LOG_INFO("DR Movement Component Stopped");
}
void DRComponentMovement::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Set random translation
            float x = randomRange(mXRange[0], mXRange[1]);
            float y = randomRange(mYRange[0], mYRange[1]);
            float z = randomRange(mZRange[0], mZRange[1]);
            pxr::GfVec3d eyeUsd(x, y, z);
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
                    averagelookAtTarget /= mLookAtTargetPaths.size();
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
            omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
        }
    }
}

}
}
}
