// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

// Take a point cloud as input and display it in the scene.
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>

#include <OgnDebugDrawPointCloudDatabase.h>
#include <iostream>


namespace omni
{
namespace isaac
{
namespace debug_draw
{

class OgnDebugDrawPointCloud
{
    bool m_initialized{ false }; // State information that tells if nodes internal attribute values have been
                                 // initialized yet
    bool m_prevDepthTest{ true };
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> m_pointDrawing{ nullptr };

public:
    // After a node is removed it will get a release call where anything set up in initialize() can be torn down
    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnDebugDrawPointCloudDatabase::sInternalState<OgnDebugDrawPointCloud>(nodeObj);
        state.m_pointDrawing.reset();
    }

    static bool compute(OgnDebugDrawPointCloudDatabase& db)
    {

        CARB_PROFILE_ZONE(0, "Debug Draw Point Cloud");

        if (!db.inputs.pointCloudData.isValid())
        {
            db.logError("Buffer is invalid");
            return false;
        }
        auto& state = db.internalState<OgnDebugDrawPointCloud>();

        // The primitive drawing helper needs to be recreated if the depthTest var has changed.
        if (state.m_initialized && state.m_prevDepthTest != db.inputs.depthTest())
        {
            state.m_pointDrawing.reset();
            state.m_initialized = false;
        }
        if (!state.m_initialized)
        {

            omni::renderer::IDebugDraw* debugDraw = carb::getCachedInterface<omni::renderer::IDebugDraw>();
            if (!debugDraw)
            {
                CARB_LOG_ERROR("*** OgnDebugDrawPointCloud Failed to acquire debugdraw interface\n");
                return false;
            }
            else
            {
                state.m_pointDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
                    omni::usd::UsdContext::getContext(), debugDraw,
                    omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints,
                    true /*World Coords*/, db.inputs.depthTest() /* Depth Test */);
            }
            state.m_initialized = true;
            state.m_prevDepthTest = db.inputs.depthTest();
        }
        const carb::ColorRgba* color = (const carb::ColorRgba*)db.inputs.color().data();
        float width = db.inputs.width();
        size_t numVerts = db.inputs.pointCloudData().size();

        if (numVerts > 0)
        {
            const carb::Float3* vp = (const carb::Float3*)db.inputs.pointCloudData()[0].data();
            state.m_pointDrawing->setVertices(vp, numVerts, *color, width);
        }
        else
        {
            state.m_pointDrawing->clear();
        }
        state.m_pointDrawing->draw();

        return true;
    }
};

REGISTER_OGN_NODE()
}
}
}
