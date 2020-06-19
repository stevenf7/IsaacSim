// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "Manager.h"

#include "Drawing.h"
#include "Query.h"

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/filesystem/IFileSystem.h>

#include <omni/kit/IEditor.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>


using namespace carb;


namespace omni
{
namespace isaac
{
namespace decals
{


Manager::Manager()
    : m_stage(nullptr),
      m_sceneQueryHandler(nullptr),
      m_drawingManager(nullptr),
      m_updateSubId(0),
      m_penDown(false),
      m_pickingEnabled(false)
{
}

Manager::~Manager()
{
    term();
}

bool Manager::init(pxr::UsdStageWeakPtr stage)
{
    if (initialized() || stage == nullptr)
        return false;

    m_stage = stage;

    carb::Framework* framework = carb::getFramework();
    omni::kit::IEditor* editor = framework->acquireInterface<omni::kit::IEditor>();
    carb::input::IInput* input = carb::getFramework()->acquireInterface<carb::input::IInput>();

    // Create scene query handler
    CARB_ASSERT(m_sceneQueryHandler == nullptr);
    m_sceneQueryHandler = createSceneQueryHandler(m_stage);
    if (m_sceneQueryHandler == nullptr)
    {
        term();
        return false;
    }

    // Create drawing manager
    CARB_ASSERT(m_drawingManager == nullptr);
    m_drawingManager = createDrawingManager(m_stage);
    if (m_drawingManager == nullptr)
    {
        term();
        return false;
    }

    // Subscribe to stage update events for tick
    CARB_ASSERT(m_updateSubId == 0);
    m_updateSubId = editor->subscribeToUpdateEvents(
        [](float elapsedTime, void* userData) {
            CARB_UNUSED(elapsedTime);
            Manager& decals = *reinterpret_cast<Manager*>(userData);

            if (!decals.initialized())
                return;

            if (decals.m_pickingEnabled)
            {
                decals.m_sceneQueryHandler->updateFromPicking(); // Get picked surface info
                decals.updateDrawing();
            }
        },
        this);
    if (m_updateSubId == 0)
    {
        term();
        return false;
    }

    return true;
}

void Manager::term()
{
    carb::Framework* framework = carb::getFramework();
    omni::kit::IEditor* editor = framework->acquireInterface<omni::kit::IEditor>();

    m_stage = nullptr;

    if (m_updateSubId != 0)
        editor->unsubscribeToUpdateEvents(m_updateSubId);

    if (m_sceneQueryHandler != nullptr)
        m_sceneQueryHandler->release();

    if (m_drawingManager != nullptr)
        m_drawingManager->release();

    m_sceneQueryHandler = nullptr;
    m_drawingManager = nullptr;
    m_updateSubId = 0;
    m_penDown = false;
    m_pickingEnabled = false;
}

void Manager::setPenColor(float r, float g, float b)
{
    m_drawingManager->setPenColor({ r, g, b });
}

void Manager::setPenWidth(float width)
{
    m_drawingManager->setPenWidth(width);
}

void Manager::setPenOffset(float offset)
{
    m_drawingManager->setPenOffset(offset);
}

void Manager::setPenThreshold(float threshold)
{
    m_drawingManager->setPenThreshold(threshold);
}

void Manager::setPenSurface(const char* primPath)
{
    m_sceneQueryHandler->updateSurface(primPath);
    updateDrawing();
}

void Manager::setPenPosition(const carb::Float3& worldPosition)
{
    m_sceneQueryHandler->updateQueryPosition(worldPosition);
    updateDrawing();
}

void Manager::setPenDown(bool penDown)
{
    m_penDown = penDown;
    updateDrawing();
}

bool Manager::eraseSurface(const char* primPath)
{
    pxr::UsdPrim prim = m_stage->GetPrimAtPath(pxr::SdfPath(primPath));
    return m_drawingManager->clearSurfacePrim(prim);
}

void Manager::eraseAllSurfaces()
{
    m_drawingManager->clearAllSurfacePrims();
}

void Manager::setPickingEnabled(bool pickingEnabled)
{
    if (m_pickingEnabled != pickingEnabled)
    {
        if (pickingEnabled)
        {
            // So that we can query the picked position
            carb::Framework* framework = carb::getFramework();
            omni::kit::IEditor* editor = framework->acquireInterface<omni::kit::IEditor>();
            editor->requestPicking();
        }
        m_pickingEnabled = pickingEnabled;
    }
}

void Manager::onPrimRemove(const pxr::SdfPath& primPath)
{
    if (!initialized())
        return; // This could be called from a callback after the manager is shut down

    m_drawingManager->setSurfacePrim();
}

void Manager::onRaycast(const float* orig, const float* dir, bool input)
{
    CARB_UNUSED(orig, dir);

    if (!m_pickingEnabled)
        return;

    if (!initialized())
        return; // This could be called from a callback after the manager is shut down

    m_penDown = input;
}

void Manager::updateDrawing()
{
    const SceneQueryResult& result = m_sceneQueryHandler->getResult();

    // Send surface and pen info to drawing manager
    //    if (result.flags & SceneQueryResult::eSurfaceChanged)
    m_drawingManager->setSurfacePrim(result.surfacePrim);

    if (result.flags & SceneQueryResult::eSurfaceFound)
        m_drawingManager->setPen(m_penDown, result.localPosition, result.localNormal);

    m_drawingManager->updateGraphics();
}

} // namespace omni
} // namespace isaac
} // namespace decals
