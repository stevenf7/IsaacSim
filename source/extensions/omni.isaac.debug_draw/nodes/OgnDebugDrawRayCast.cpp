// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

// Take an array of ray start/end points as input and display it in the scene.
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>

#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/isaac/utils/Conversions.h>

#include <OgnDebugDrawRayCastDatabase.h>
#include <PrimitiveDrawingHelper.h>
#include <iostream>

namespace omni
{
namespace isaac
{
namespace debug_draw
{

class OgnDebugDrawRayCast : public BaseResetNode
{
public:
    static void setLineDrawing(omni::isaac::debug_draw::OgnDebugDrawRayCast& state)
    {
        omni::renderer::IDebugDraw* debugDrawPtr = carb::getCachedInterface<omni::renderer::IDebugDraw>();
        if (!debugDrawPtr)
        {
            CARB_LOG_ERROR("*** OgnDebugDrawRayCast failed to acquire debugdraw interface\n");
        }
        state.mLineDrawing = std::make_shared<drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr, drawing::PrimitiveDrawingHelper::RenderingMode::eLines,
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
        if (!state.mLineDrawing.get())
        {
            setLineDrawing(state);
        }
        // Clear vectors and line drawing
        state.mLineDrawing->clear();
        state.mStartPoints.clear();
        state.mEndPoints.clear();

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
            auto beamOrigin = omni::isaac::utils::conversions::asCarbFloat3(beamOrigins[i]);
            auto beamEndPoint = omni::isaac::utils::conversions::asCarbFloat3(beamEndPoints[i]);
            state.mStartPoints.push_back(beamOrigin);
            state.mEndPoints.push_back(beamEndPoint);
        }

        for (int i = 0; i < numRays; i++)
        {
            state.mLineDrawing->addVertex(state.mStartPoints[i], *color, width);
            state.mLineDrawing->addVertex(state.mEndPoints[i], *color, width);
        }

        // if there is no transform input, then don't use it.
        auto& nodeObj = db.abi_node();
        const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, inputs::transform.m_token);
        if (db.inputs.doTransform() && attr.iAttribute->getUpstreamConnectionCount(attr))
        {
            state.mLineDrawing->transformVertices(db.inputs.transform().data());
        }
        state.mLineDrawing->draw();
        return true;
    }

    virtual void reset()
    {
        if (mLineDrawing)
        {
            mLineDrawing->clear();
            mLineDrawing->draw();
        }
    }

private:
    std::shared_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> mLineDrawing{ nullptr };
    std::vector<carb::Float3> mStartPoints;
    std::vector<carb::Float3> mEndPoints;
};

REGISTER_OGN_NODE()
} // debug_draw
} // isaac
} // omni
