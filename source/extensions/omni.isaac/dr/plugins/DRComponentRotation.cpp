// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentRotation.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/rotationComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentRotation::DRComponentRotation() : DRComponentBase()
{
}
DRComponentRotation::~DRComponentRotation()
{
    stop();
}
void DRComponentRotation::initialize(const pxr::DrSchemaRotationComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentRotation::onStart()
{
    CARB_LOG_INFO("DR Rotation Component Started");
}
void DRComponentRotation::update()
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
void DRComponentRotation::onComponentChange()
{
    const pxr::DrSchemaRotationComponent& rotPrim = (pxr::DrSchemaRotationComponent)mPrim;
    rotPrim.GetCompNameAttr().Get(&mCompName);
    rotPrim.GetXRangeAttr().Get(&mXRange);
    rotPrim.GetYRangeAttr().Get(&mYRange);
    rotPrim.GetZRangeAttr().Get(&mZRange);
    rotPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    rotPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);
    rotPrim.GetSeedAttr().Get(&mSeed);
    if (mCurrentSeed != mSeed)
    {
        mRandomGenerator.seed(mSeed);
        mCurrentSeed = mSeed;
    }

    mPaths.clear();
    pxr::UsdRelationship primPaths = rotPrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());

    update();
    CARB_LOG_INFO("Rotation Update: %s", mCompName.c_str());
}
void DRComponentRotation::stop()
{
    CARB_LOG_INFO("DR Rotation Component Stopped");
}
void DRComponentRotation::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            float x = randomRangeFloat(mXRange[0], mXRange[1]);
            float y = randomRangeFloat(mYRange[0], mYRange[1]);
            float z = randomRangeFloat(mZRange[0], mZRange[1]);
            // Set random rotation
            pxr::GfTransform bodyPose;
            pxr::GfRotation rowRot(pxr::GfVec3d(1, 0, 0), x), pitchRot(pxr::GfVec3d(0, 1, 0), y),
                yawRot(pxr::GfVec3d(0, 0, 1), z);
            bodyPose.SetRotation(rowRot * pitchRot * yawRot);
            // Get current translation and scale
            pxr::GfMatrix4d currentTransformMat, scaledTransformMat, scaleMat;
            currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
            pxr::GfTransform currentTr(currentTransformMat);
            bodyPose.SetTranslation(currentTr.GetTranslation());
            scaleMat.SetScale(currentTr.GetScale());
            // Multiply current scale with random pose
            scaledTransformMat = scaleMat * bodyPose.GetMatrix();
            omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
        }
    }
}

}
}
}
