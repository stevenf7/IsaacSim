// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/isaac/utils/BaseResetNode.h>

#include <OgnDebugDrawPointCloudDatabase.h>
#include <iostream>

namespace omni
{
namespace isaac
{
namespace debug_draw
{

class OgnDebugDrawPointCloud : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnDebugDrawPointCloudDatabase::sInternalState<OgnDebugDrawPointCloud>(nodeObj);
        omni::renderer::IDebugDraw* debugDrawPtr = carb::getCachedInterface<omni::renderer::IDebugDraw>();
        if (!debugDrawPtr)
        {
            CARB_LOG_ERROR("*** OgnDebugDrawPointCloud failed to acquire debugdraw interface\n");
        }
        state.m_pointDrawing = std::make_shared<drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr, drawing::PrimitiveDrawingHelper::RenderingMode::ePoints,
            true /*World Coords*/);
    }


    static bool compute(OgnDebugDrawPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Debug Draw Point Cloud");

        const carb::Float3* input = reinterpret_cast<const carb::Float3*>(db.inputs.dataPtr());
        size_t numVerts = db.inputs.bufferSize() / sizeof(carb::Float3); // assumes float3 input.
        if (!input)
        {
            if (numVerts)
                db.logError("DebugDrawPointCloud Buffer is invalid, but should have %d vertices.", numVerts);
            return false;
        }
        auto& state = db.internalState<OgnDebugDrawPointCloud>();

        const carb::ColorRgba* color = (const carb::ColorRgba*)db.inputs.color().data();
        float size = db.inputs.size();
        state.m_pointDrawing->clear();
        state.m_pointDrawing->clear();

        if (numVerts > 0)
        {
            state.m_pointDrawing->setVertices(input, numVerts);
            state.m_pointDrawing->setColor(*color);
            state.m_pointDrawing->setWidth(size);
            // if there is no transform input, then don't use it.
            auto& nodeObj = db.abi_node();
            const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, inputs::transform.m_token);
            if (attr.iAttribute->getUpstreamConnectionCount(attr))
            {
                state.m_pointDrawing->transformVertices(db.inputs.transform().data());
            }
        }
        state.m_pointDrawing->draw();
        return true;
    }

    virtual void reset()
    {
        if (m_pointDrawing)
        {
            m_pointDrawing->clear();
            m_pointDrawing->draw();
        }
    }

private:
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> m_pointDrawing{ nullptr };
};

REGISTER_OGN_NODE()
} // debug_draw
} // isaac
} // omni
