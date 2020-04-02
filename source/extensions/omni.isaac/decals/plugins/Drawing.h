// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Framework.h>

namespace omni
{
namespace isaac
{
namespace decals
{

class IDrawingManager
{
public:
    virtual void updateGraphics() = 0;
    virtual void release() = 0;

    // Drawing API
    virtual void setPenColor(const carb::Float3& rgbColor) = 0;
    virtual void setPenWidth(float width) = 0;
    virtual void setPenOffset(float offset) = 0;
    virtual void setPenThreshold(float threshold) = 0;
    virtual void setSurfacePrim(pxr::UsdPrim prim = pxr::UsdPrim()) = 0;
    virtual void setPen(bool down, const carb::Float3& position, const carb::Float3& normal) = 0;
    virtual bool clearSurfacePrim(pxr::UsdPrim prim) = 0;
    virtual void clearAllSurfacePrims() = 0;

protected:
    IDrawingManager()
    {
    }
    virtual ~IDrawingManager()
    {
    }
};


// Create a drawing manager object using this function, and destroy with the release() function.
IDrawingManager* createDrawingManager(pxr::UsdStageRefPtr stage);

} // namespace omni
} // namespace isaac
} // namespace decals
