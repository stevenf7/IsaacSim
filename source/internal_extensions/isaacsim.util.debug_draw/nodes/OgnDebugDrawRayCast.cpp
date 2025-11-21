// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

// Take an array of ray start/end points as input and display it in the scene.
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>

#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Conversions.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>

#include <OgnDebugDrawRayCastDatabase.h>
#include <iostream>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{

class OgnDebugDrawRayCast : public isaacsim::core::includes::BaseResetNode
{
public:
    static void setLineDrawing(isaacsim::util::debug_draw::OgnDebugDrawRayCast& state)
    {
        state.m_lineDrawing = std::make_shared<drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), drawing::PrimitiveDrawingHelper::RenderingMode::eLines,
            true /*World Coords*/);
    }

    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnDebugDrawRayCastDatabase::sPerInstanceState<OgnDebugDrawRayCast>(nodeObj, instanceId);
        setLineDrawing(state);
    }


    static bool compute(OgnDebugDrawRayCastDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Debug Draw Ray Cast");

        auto& state = db.perInstanceState<OgnDebugDrawRayCast>();
        if (!state.m_lineDrawing.get())
        {
            setLineDrawing(state);
        }
        // Clear vectors and line drawing
        state.m_lineDrawing->clear();
        state.m_startPoints.clear();
        state.m_endPoints.clear();

        // get inputs
        const carb::ColorRgba* color = (const carb::ColorRgba*)db.inputs.color().data();
        float width = db.inputs.beamWidth();
        const pxr::GfVec3f* beamOrigins = db.inputs.beamOrigins().data();
        const pxr::GfVec3f* beamEndPoints = db.inputs.beamEndPoints().data();
        int numRays = db.inputs.numRays();

        if (!beamOrigins && numRays > 0)
        {
            numRays = 0;
        }

        for (int i = 0; i < numRays; i++)
        {
            auto beamOrigin = isaacsim::core::includes::conversions::asCarbFloat3(beamOrigins[i]);
            auto beamEndPoint = isaacsim::core::includes::conversions::asCarbFloat3(beamEndPoints[i]);
            state.m_startPoints.push_back(beamOrigin);
            state.m_endPoints.push_back(beamEndPoint);
        }

        for (int i = 0; i < numRays; i++)
        {
            state.m_lineDrawing->addVertex(state.m_startPoints[i], *color, width);
            state.m_lineDrawing->addVertex(state.m_endPoints[i], *color, width);
        }

        // if there is no transform input, then don't use it.
        auto& nodeObj = db.abi_node();
        const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, inputs::transform.m_token);
        if (db.inputs.doTransform() && attr.iAttribute->getUpstreamConnectionCount(attr))
        {
            state.m_lineDrawing->transformVertices(db.inputs.transform().data());
        }
        state.m_lineDrawing->draw();
        return true;
    }

    virtual void reset()
    {
        if (m_lineDrawing)
        {
            m_lineDrawing->clear();
            m_lineDrawing->draw();
        }
    }

private:
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> m_lineDrawing{ nullptr };
    std::vector<carb::Float3> m_startPoints;
    std::vector<carb::Float3> m_endPoints;
};

REGISTER_OGN_NODE()
}
}
}
