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
void DRComponentMovement::initialize(const pxr::DrSchemaMovementComponent& prim, pxr::UsdStageRefPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentMovement::onStart()
{
    CARB_LOG_INFO("DR Movement Component Started");
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
    std::string primPaths;

    const pxr::DrSchemaMovementComponent& movPrim = (pxr::DrSchemaMovementComponent)mPrim;
    movPrim.GetCompNameAttr().Get(&mCompName);
    movPrim.GetPrimPathsAttr().Get(&primPaths);
    movPrim.GetXRangeAttr().Get(&mXRange);
    movPrim.GetYRangeAttr().Get(&mYRange);
    movPrim.GetZRangeAttr().Get(&mZRange);
    movPrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    movPrim.GetIncludeChildrenAttr().Get(&mIncludeChild);

    boost::split(mPaths, primPaths, [](char c) { return c == ','; });
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
            float x = randomRange(mXRange[0], mXRange[1]);
            float y = randomRange(mYRange[0], mYRange[1]);
            float z = randomRange(mZRange[0], mZRange[1]);
            // Set random translation
            pxr::GfTransform bodyPose;
            bodyPose.SetTranslation(pxr::GfVec3f(x, y, z));
            // Get current rotation and scale
            pxr::GfMatrix4d currentTransformMat, scaledTransformMat, scaleMat;
            currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
            pxr::GfTransform currentTr(currentTransformMat);
            bodyPose.SetRotation(currentTr.GetRotation());
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
