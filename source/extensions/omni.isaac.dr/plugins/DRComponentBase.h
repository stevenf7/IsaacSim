// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "plugins/core/Component.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <omni/renderer/IDebugDraw.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

template <class PrimType>
class DRComponentBase : public utils::ComponentBase<PrimType>
{
public:
    DRComponentBase()
    {
        mRandomizationDurationInterval = -1;
        mIncludeChild = false;
        mDRLayerName = "";
        mCompName = "";
        mSeed = 12345;
        mCurrentSeed = 0;
    }
    virtual ~DRComponentBase()
    {
        // Empty
    }
    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
    }
    virtual void onStart() = 0;
    virtual void tick() = 0;
    virtual void onComponentChange() = 0;

    double mRandomizationDurationInterval;
    double mLastTickTime = 0.0;
    bool mIncludeChild;
    std::vector<std::string> mIgnoreClassList;
    std::string mDRLayerName, mCompName;
    int mSeed, mCurrentSeed;
    std::default_random_engine mRandomGenerator;
    omni::renderer::LineBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;

protected:
    float randomRangeFloat(float low, float high)
    {
        std::uniform_real_distribution<float> p(low, high);
        return p(mRandomGenerator);
    }

    int randomRangeInt(int low, int high)
    {
        std::uniform_int_distribution<int> p(low, high);
        return p(mRandomGenerator);
    }

    bool ignoreClass(std::string prim, std::vector<std::string>& groupClassList)
    {
        for (std::string& ignoreClass : mIgnoreClassList)
        {
            if (prim.find(ignoreClass) != std::string::npos)
                return true;
        }
        if (mIgnoreClassList[0] == "all_except_group_classes")
        {
            for (std::string& groupClass : groupClassList)
            {
                if (prim.find(groupClass) != std::string::npos)
                    return false;
            }
            return true;
        }
        return false;
    }

    void createDebugLineList(size_t size, omni::renderer::IDebugDraw* mDebugDrawPtr)
    {
        if (mShapeDebugLineBuffer == omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mShapeDebugLineBuffer = mDebugDrawPtr->allocateLineBuffer(size);
            mShapeDebugRenderInstanceBuffer = mDebugDrawPtr->allocateRenderInstanceBuffer(mShapeDebugLineBuffer, 1);
            float transform[16] = {};
            transform[0] = 1.f;
            transform[1 + 4] = 1.f;
            transform[2 + 8] = 1.f;
            transform[3 + 12] = 1.f;

            mDebugDrawPtr->setRenderInstance(mShapeDebugRenderInstanceBuffer, 0, &transform[0], 0);
        }
    }

    void releaseDebugLineList(omni::renderer::IDebugDraw* mDebugDrawPtr)
    {
        if (mShapeDebugLineBuffer != omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mDebugDrawPtr->deallocateLineBuffer(mShapeDebugLineBuffer);
            mDebugDrawPtr->deallocateRenderInstanceBuffer(mShapeDebugRenderInstanceBuffer);
            mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
            mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        }
    }
};
}
}
}
