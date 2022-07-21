// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/dictionary/IDictionary.h>
#include <carb/dictionary/ISerializer.h>
#include <carb/fastcache/FastCache.h>

#include <omni/renderer/IDebugDraw.h>
#include <omni/timeline/ITimeline.h>
#include <robotEngineBridgeSchema/robotEnginePolylineVisualizer.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

struct DebugData
{
    carb::Float3 startPos;
    carb::Float3 endPos;
    uint32_t color;
};

class PolylineVisualizer : public IsaacComponent
{


public:
    /**
     * @brief
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    PolylineVisualizer();

    /**
     * @brief
     *
     */
    ~PolylineVisualizer();


    /**
     * @brief
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
    virtual void onStop();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    void createDebugLineList(size_t size);
    void releaseDebugLineList();

    carb::fastcache::FastCache* mFastCachePtr = nullptr;
    omni::renderer::IDebugDraw* mDebugDrawPtr = nullptr;
    carb::dictionary::ISerializer* mJsonSerializer = nullptr;
    carb::dictionary::IDictionary* mIDict = nullptr;
    omni::timeline::ITimeline* mTimeline = nullptr;

    omni::renderer::SimplexBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;

    /// The name of the channel on which state informations is published
    std::string mInputComponent = "input";
    std::string mInputChannel = "plan";
    float mWidth = 1.0f;
    pxr::GfVec4f mColor = pxr::GfVec4f(1, 1, 1, 1);
    pxr::SdfPath mParentPath = pxr::SdfPath("");
    pxr::UsdPrim mParentPrim;
    double mUnitScale;
    pxr::GfVec3f mOffset = pxr::GfVec3f(0, 0, 0);
    std::vector<DebugData> mLineData;
    uint32_t mColorValue = 0;
    int mRed = 255, mGreen = 255, mBlue = 255, mAlpha = 255;
    pxr::VtArray<pxr::GfVec4f> tessellatedPoints;
    pxr::VtArray<pxr::GfVec4f> tessellatedTangents;
};
}
}
}
