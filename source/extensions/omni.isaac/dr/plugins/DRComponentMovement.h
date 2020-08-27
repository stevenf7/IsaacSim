#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <DrSchema/baseComponent.h>
#include <DrSchema/movementComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentMovement : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentMovement();
    ~DRComponentMovement();
    virtual void initialize(const pxr::DrSchemaMovementComponent& prim, pxr::UsdStageWeakPtr stage);
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths, mLookAtTargetPaths;
    pxr::GfVec2f mXRange, mYRange, mZRange;
    std::vector<pxr::UsdPrim> mAllPrims;
    bool mEnableLookAtTarget;
    pxr::GfVec3d mLookAtTargetOffset = pxr::GfVec3d(0.0, 0.0, 0.0);
    pxr::GfVec3d mUpUsd;
};

}
}
}
