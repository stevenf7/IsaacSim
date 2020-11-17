// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DRComponentBase.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <drSchema/baseComponent.h>
#include <drSchema/rotationComponent.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

class DRComponentRotation : public DRComponentBase<pxr::DrSchemaBaseComponent>
{
public:
    DRComponentRotation();
    ~DRComponentRotation();
    virtual void initialize(const pxr::DrSchemaRotationComponent& prim, pxr::UsdStageWeakPtr stage);
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
