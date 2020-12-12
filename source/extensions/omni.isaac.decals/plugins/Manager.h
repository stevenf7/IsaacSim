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

#include <omni/kit/IStageUpdate.h>
#include <omni/kit/KitTypes.h>

namespace omni
{
namespace isaac
{
namespace decals
{

class ISceneQueryHandler;
class IDrawingManager;

class Manager
{
public:
    Manager();
    ~Manager();

    bool init(pxr::UsdStageWeakPtr stage);
    void term();

    bool initialized()
    {
        return m_stage != nullptr;
    }

    void setPenColor(float r, float g, float b);
    void setPenWidth(float width);
    void setPenOffset(float offset);
    void setPenThreshold(float threshold);

    void setPenSurface(const char* primPath);
    void setPenPosition(const carb::Float3& worldPosition);
    void setPenDown(bool penDown);

    bool eraseSurface(const char* primPath);
    void eraseAllSurfaces();

    void setPickingEnabled(bool pickingEnabled);

    void onPrimRemove(const pxr::SdfPath& primPath);
    void onRaycast(const float* orig, const float* dir, bool input);

private:
    void updateDrawing();

    pxr::UsdStageWeakPtr m_stage;
    ISceneQueryHandler* m_sceneQueryHandler;
    IDrawingManager* m_drawingManager;
    kit::SubscriptionId m_updateSubId;
    bool m_penDown;
    bool m_pickingEnabled;
};


} // namespace omni
} // namespace isaac
} // namespace decals
