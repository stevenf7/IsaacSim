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


#define __DEBUG_PRINT_ON 0
namespace omni::isaac::debug_draw
{

class OgnDebugDrawPointCloud
{
public:
    // If the node fails we want to cleanup the output
    static bool returnCleanly(OgnDebugDrawPointCloudDatabase& db, bool passThroughReturnValue, int dbv)
    {
        auto& state = db.internalState<OgnDebugDrawPointCloud>();
        if (state.m_pointDrawing)
        {
            state.m_pointDrawing->clear();
            state.m_pointDrawing->draw();
        }
        state.m_pointDrawing.reset();
        state.m_pointDrawing = nullptr;
        state.m_initialized = false;
#if __DEBUG_PRINT_ON
        std::cout << dbv << "}";
#endif
        return passThroughReturnValue;
    }

    static bool compute(OgnDebugDrawPointCloudDatabase& db)
    {
#if __DEBUG_PRINT_ON
        std::cout << "DD[";
#endif
        CARB_PROFILE_ZONE(0, "Debug Draw Point Cloud");

        if (!db.inputs.pointCloudData.isValid())
        {
            db.logError("Buffer is invalid");
            return returnCleanly(db, true, 1);
        }
        auto& state = db.internalState<OgnDebugDrawPointCloud>();

        // The primitive drawing helper needs to be recreated if the depthTest var has changed.
        if (state.m_initialized && state.m_prevDepthTest != db.inputs.depthTest())
        {
            if (state.m_pointDrawing)
            {
                state.m_pointDrawing->clear();
            }
            state.m_pointDrawing.reset();
            state.m_initialized = false;
        }
        if (!state.m_initialized)
        {
            omni::renderer::IDebugDraw* debugDraw = carb::getCachedInterface<omni::renderer::IDebugDraw>();
            if (!debugDraw)
            {
                CARB_LOG_ERROR("*** OgnDebugDrawPointCloud Failed to acquire debugdraw interface\n");
                return returnCleanly(db, true, 2);
            }
            else
            {
                state.m_pointDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
                    omni::usd::UsdContext::getContext(), debugDraw,
                    omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints,
                    true /*World Coords*/, db.inputs.depthTest() /* Depth Test */);
            }
            state.m_prevDepthTest = db.inputs.depthTest();
            state.m_initialized = true;
        }
        const carb::ColorRgba* color = (const carb::ColorRgba*)db.inputs.color().data();
        float width = db.inputs.width();
        size_t numVerts = db.inputs.pointCloudData().size();

        if (numVerts > 0)
        {
            const carb::Float3* vp = (const carb::Float3*)db.inputs.pointCloudData()[0].data();
            state.m_pointDrawing->setVertices(vp, numVerts);
            state.m_pointDrawing->setColor(*color);
            state.m_pointDrawing->setWidth(width);
            // if there is no transform input, then don't use it.
            auto& nodeObj = db.abi_node();
            const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, inputs::transform.m_token);
            if (attr.iAttribute->getUpstreamConnectionCount(attr))
            {
                state.m_pointDrawing->transformVertices(db.inputs.transform().data());
            }
        }
        else
        {
            state.m_pointDrawing->clear();
        }
        state.m_pointDrawing->draw();
#if __DEBUG_PRINT_ON
        std::cout << "]";
#endif
        return true;
    }

    virtual void reset()
    {
        if (m_pointDrawing)
        {
            m_pointDrawing->clear();
        }
        m_pointDrawing.reset();
    }

private:
    bool m_initialized{ false }; // tells if nodes internal attribute values have been initialized yet
    bool m_prevDepthTest{ true };
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> m_pointDrawing{ nullptr };
};

REGISTER_OGN_NODE()
} // omni::isaac::debug_draw
