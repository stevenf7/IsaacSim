#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/Types.h>
#include <carb/fastcache/FastCache.h>

#include <omni/renderer/IDebugDraw.h>
#include <robotEngineBridgeSchema/robotEnginePlan2Visualizer.h>

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

class Plan2Visualizer : public IsaacComponent
{


public:
    /**
     * @brief
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    Plan2Visualizer();

    /**
     * @brief
     *
     */
    ~Plan2Visualizer();


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

    carb::Framework* framework = nullptr;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;
    omni::renderer::IDebugDraw* mDebugDrawPtr = nullptr;
    omni::renderer::LineBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;

    /// The name of the channel on which state informations is published
    std::string mInputComponent = "input";
    std::string mInputChannel = "plan";
    float mWidth = 1.0f;
    pxr::GfVec4f mColor = pxr::GfVec4f(1, 1, 1, 1);
    pxr::SdfPath mParentPath = pxr::SdfPath("");
    double mUnitScale;
    pxr::GfVec3f mOffset = pxr::GfVec3f(0, 0, 0);
    std::vector<DebugData> mLineData;
    uint32_t mColorValue = 0;
    pxr::VtArray<pxr::GfVec4f> tessellatedPoints;
    pxr::VtArray<pxr::GfVec4f> tessellatedTangents;
};
}
}
}
