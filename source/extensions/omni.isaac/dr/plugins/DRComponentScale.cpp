// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentScale.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <DrSchema/scaleComponent.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentScale::DRComponentScale() : DRComponentBase()
{
}
DRComponentScale::~DRComponentScale()
{
    stop();
}
void DRComponentScale::initialize(const pxr::DrSchemaScaleComponent& prim, pxr::UsdStageWeakPtr stage)
{
    DRComponentBase::initialize(prim, stage);
}
void DRComponentScale::onStart()
{
    CARB_LOG_INFO("DR Scale Component Started");
}
void DRComponentScale::update()
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
void DRComponentScale::onComponentChange()
{
    const pxr::DrSchemaScaleComponent& scalePrim = (pxr::DrSchemaScaleComponent)mPrim;
    scalePrim.GetCompNameAttr().Get(&mCompName);
    scalePrim.GetXRangeAttr().Get(&mXRange);
    scalePrim.GetYRangeAttr().Get(&mYRange);
    scalePrim.GetZRangeAttr().Get(&mZRange);
    scalePrim.GetDurationAttr().Get(&mRandomizationDurationInterval);
    scalePrim.GetIncludeChildrenAttr().Get(&mIncludeChild);

    mPaths.clear();
    pxr::UsdRelationship primPaths = scalePrim.GetPrimPathsRel();
    pxr::SdfPathVector targets;
    primPaths.GetTargets(&targets);
    for (auto target : targets)
        mPaths.push_back(target.GetString());

    update();
    CARB_LOG_INFO("Scale Update: %s", mCompName.c_str());
}
void DRComponentScale::stop()
{
    CARB_LOG_INFO("DR Scale Component Stopped");
}
void DRComponentScale::tick()
{
    for (auto& prim : mAllPrims)
    {
        if (prim)
        {
            // Randomized scale parameters
            float x = randomRange(mXRange[0], mXRange[1]);
            float y = randomRange(mYRange[0], mYRange[1]);
            float z = randomRange(mZRange[0], mZRange[1]);
            pxr::GfVec3d doubleScale(x, y, z);
            auto currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
            pxr::GfVec3d currentTrans = currentTransformMat.ExtractTranslation();
            pxr::GfRotation currentRot = currentTransformMat.ExtractRotation();
            pxr::GfMatrix4d scaledMat, transformMat, scaledTransformMat;
            transformMat.SetTransform(currentRot, currentTrans);
            scaledMat.SetScale(doubleScale);
            scaledTransformMat = scaledMat * transformMat;
            omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
        }
    }
}

}
}
}
