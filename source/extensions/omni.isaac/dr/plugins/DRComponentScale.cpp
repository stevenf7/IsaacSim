// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentScale.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>

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
    std::string primPaths;

    mPrim.GetAttribute(pxr::TfToken("compName")).Get(&mCompName);
    mPrim.GetAttribute(pxr::TfToken("primPaths")).Get(&primPaths);
    mPrim.GetAttribute(pxr::TfToken("xRange")).Get(&mXRange);
    mPrim.GetAttribute(pxr::TfToken("yRange")).Get(&mYRange);
    mPrim.GetAttribute(pxr::TfToken("zRange")).Get(&mZRange);
    mPrim.GetAttribute(pxr::TfToken("duration")).Get(&mRandomizationDurationInterval);
    mPrim.GetAttribute(pxr::TfToken("includeChildren")).Get(&mIncludeChild);

    boost::split(mPaths, primPaths, [](char c) { return c == ','; });
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
