// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/GxfComponent.h"
#include "extensions/atlas/atlas_frontend.hpp"
#include "gems/pose_tree/pose_tree.hpp"

#include <carb/Types.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/timeline/ITimeline.h>
#include <robotEngineBridgeSchema/robotEnginePoseTree.h>

#include <regex>
#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{
class PoseTreeComponent : public GxfComponent
{
public:
    /**
     * @brief Construct a new Component object
     */
    PoseTreeComponent(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

    /**
     * @brief Destroy the Component object
     *
     */
    ~PoseTreeComponent();


    /**
     * @brief The sensor pointer might not be valid, so force update on start
     *
     */
    virtual void onStart();

    /**
     * @brief
     *
     */
    virtual void tick();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    // Get handle to Atlas Frontend
    bool getAtlasFrontend();
    // Adds a prim and its children up to a certain depth to the pose tree recursively
    void addPrimToPoseTree(const pxr::UsdPrim& prim,
                           const int depth,
                           const nvidia::isaac::PoseTree::frame_t parentUid,
                           nvidia::isaac::PoseTree& poseTree,
                           bool useLocalPose);

    omni::timeline::ITimeline* mTimeline = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    /// The name of the channel for AtlasFrontend component
    std::string mOutputComponent = "";
    std::string mOutputChannel = "frontend";

    pxr::SdfPathVector mPrims;
    pxr::VtArray<int> mDepthLimits;
    std::string mPrimRegexStr = "";
    std::regex mPrimRegex;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;
    nvidia::isaac::PoseTree::frame_t mRootUid;
    bool mPoseTreeInitialized = false;

    double mUnitScale = 1.0;
};
}
}
}
