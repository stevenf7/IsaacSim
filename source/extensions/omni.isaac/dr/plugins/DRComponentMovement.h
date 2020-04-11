#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentMovement : public DRComponentBase
{
public:
    DRComponentMovement();
    ~DRComponentMovement();
    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();

private:
    void update();
    void stop();

    std::vector<std::string> mPaths;
    pxr::GfVec2f mXRange, mYRange, mZRange;
    std::vector<pxr::UsdPrim> mAllPrims;
};

}
}
}
