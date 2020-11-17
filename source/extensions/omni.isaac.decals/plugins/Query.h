// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
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
namespace kit
{
struct IEditor;
}
}

namespace omni
{
namespace isaac
{
namespace decals
{

struct SceneQueryResult
{
    enum Flags
    {
        eSurfaceFound = (1 << 0),
        eSurfaceChanged = (1 << 1)
    };

    uint32_t flags;
    pxr::UsdPrim surfacePrim;
    carb::Float3 localPosition;
    carb::Float3 localNormal;

    SceneQueryResult() : flags(0)
    {
    }
};

class ISceneQueryHandler
{
public:
    virtual void updateSurface(const char* primPath) = 0;
    virtual void updateQueryPosition(const carb::Float3& worldPosition) = 0;
    virtual void updateFromPicking() = 0;
    virtual const SceneQueryResult& getResult() const = 0;
    virtual void release() = 0;

protected:
    ISceneQueryHandler()
    {
    }
    virtual ~ISceneQueryHandler()
    {
    }
};


// Create a scene query handler object using this function, and destroy with the release() function.
ISceneQueryHandler* createSceneQueryHandler(pxr::UsdStageWeakPtr stage);

} // namespace omni
} // namespace isaac
} // namespace decals
