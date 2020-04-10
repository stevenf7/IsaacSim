// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentRotation.h"

#include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/InterfaceUtils.h>

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
            float x = randomRange(mXRange[0], mXRange[1]);
            float y = randomRange(mYRange[0], mYRange[1]);
            float z = randomRange(mZRange[0], mZRange[1]);
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
