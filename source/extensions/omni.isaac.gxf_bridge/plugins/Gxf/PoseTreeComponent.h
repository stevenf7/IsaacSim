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
namespace gxf_bridge
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
    // Adds a prim and its children up to a certain depth to the pose tree recursively
    gxf_result_t addPrim(nvidia::gxf::Entity& message,
                         const pxr::UsdPrim& prim,
                         const int depth,
                         const nvidia::isaac::PoseTree::frame_t parentUid,
                         bool useLocalPose);

    omni::timeline::ITimeline* mTimeline = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    /// The name of the channel for publishing pose messages
    std::string mOutputComponent = "output";
    std::string mOutputChannel = "pose_tree";

    pxr::SdfPathVector mPrims;
    pxr::VtArray<int> mDepthLimits;
    std::string mPrimRegexStr = "";
    std::regex mPrimRegex;
    nvidia::isaac::PoseTree::frame_t mRootUid;
    int mEdgeCount = 0;

    double mUnitScale = 1.0;
};
}
}
}
