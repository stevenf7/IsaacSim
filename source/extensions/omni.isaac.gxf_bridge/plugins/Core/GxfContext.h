
// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#pragma once
#include "GxfPoseTreeMap.h"
#include "extensions/atlas/atlas_frontend.hpp"
#include "gxf/core/gxf.h"
#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/bridge/ViewportManager.h"

#include <gxf/std/clock.hpp>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IViewport.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

class GxfContext
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
    gxf_result_t destroy();
    uint64_t getContextHandle();

private:
    std::shared_ptr<gxf_context_t> mContext = nullptr;
    // GxfPoseTreeMap mPoseTreeMap;
    int64_t mTimeDifferenceNanoSeconds = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    omni::kit::IViewport* mViewportInterface = nullptr;
    std::unique_ptr<utils::ViewportManager> mViewportManager = nullptr;
    nvidia::gxf::Handle<nvidia::gxf::Allocator> mAllocator;
    nvidia::gxf::Handle<nvidia::gxf::Clock> mClock;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;
    bool mRunning = false;
    bool mActivate = false;
};
}
}
}
