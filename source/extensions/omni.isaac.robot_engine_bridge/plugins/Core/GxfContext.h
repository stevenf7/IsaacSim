
// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#pragma once
#include "GxfComponent.h"
#include "GxfPoseTreeMap.h"
#include "gxf/core/gxf.h"
#include "plugins/bridge/BridgeApplication.h"

#include <gxf/std/clock.hpp>
#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{
class GxfContext : public utils::BridgeApplicationBase<GxfComponent>
{
public:
    GxfContext(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    ~GxfContext();
    gxf_result_t create(const std::string& basePath,
                        const std::string& manifestFile,
                        const std::vector<std::string>& graphFiles);

    gxf_result_t start();
    void tick(double dt);
    gxf_result_t stop();
    void onStop();
    void onComponentAdd(const pxr::UsdPrim& prim);
    gxf_result_t destroy();

private:
    gxf_context_t mContext = nullptr;
    GxfPoseTreeMap mPoseTreeMap;
    int64_t mTimeDifferenceNanoSeconds = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    nvidia::gxf::Handle<nvidia::gxf::Allocator> mAllocator;
    nvidia::gxf::Handle<nvidia::gxf::Clock> mClock;
    bool mRunning = false;
};
}
}
}
}
