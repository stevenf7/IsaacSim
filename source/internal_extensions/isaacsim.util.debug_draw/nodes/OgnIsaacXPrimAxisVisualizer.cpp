// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on
#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Pose.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <OgnIsaacXPrimAxisVisualizerDatabase.h>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{
class OgnIsaacXPrimAxisVisualizer : public isaacsim::core::includes::BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacXPrimAxisVisualizerDatabase::sPerInstanceState<OgnIsaacXPrimAxisVisualizer>(nodeObj, instanceId);
        state.m_lineDrawing = std::make_shared<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(),
            isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
    }

    static bool compute(OgnIsaacXPrimAxisVisualizerDatabase& db)
    {
        const auto& inputPrim = db.inputs.xPrim();
        pxr::SdfPath primPath;
        if (!inputPrim.empty())
        {
            primPath = omni::fabric::toSdfPath(inputPrim[0]);
        }
        else
        {
            db.logError("Omnigraph Error: no input prim found for visualization");
            return false;
        }

        auto& state = db.perInstanceState<OgnIsaacXPrimAxisVisualizer>();
        state.m_length = db.inputs.length();
        state.m_thickness = db.inputs.thickness();

        if (state.m_stage == nullptr)
        {
            //  Find our stage
            const GraphContextObj& context = db.abi_context();
            state.m_stageId = context.iContext->getStageId(context);
            state.m_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(state.m_stageId));
            omni::fabric::IStageReaderWriter* iStageReaderWriter =
                carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
            omni::fabric::StageReaderWriterId stageInProgress = iStageReaderWriter->get(state.m_stageId);
            state.m_usdrtStage = usdrt::UsdStage::Attach(state.m_stageId, stageInProgress);
            if (!state.m_stage)
            {
                db.logError("Could not find USD stage %ld", state.m_stageId);
                return false;
            }
        }

        auto prim = state.m_stage->GetPrimAtPath(primPath);

        if (prim.IsValid() == false)
        {
            state.m_lineDrawing->clear();
            state.m_lineDrawing->draw();
            db.logError("Could not find USD prim at path: %s", primPath.GetText());
            return false;
        }

        state.m_lineDrawing->clear();

        usdrt::GfMatrix4d usdTransform =
            isaacsim::core::includes::pose::computeWorldXformNoCache(state.m_stage, state.m_usdrtStage, primPath);

        state.drawAxis(usdTransform, state.m_length, state.m_thickness);
        return true;
    }


    void drawAxis(usdrt::GfMatrix4d usdTransform, const float axisLength, const float axisThickness)
    {
        omni::math::linalg::vec3d translation = usdTransform.ExtractTranslation();
        usdTransform.Orthonormalize();

        omni::math::linalg::vec3d xtransform =
            usdTransform.TransformDir(omni::math::linalg::vec3d(static_cast<double>(axisLength), 0.0, 0.0));
        omni::math::linalg::vec3d ytransform =
            usdTransform.TransformDir(omni::math::linalg::vec3d(0.0, static_cast<double>(axisLength), 0.0));
        omni::math::linalg::vec3d ztransform =
            usdTransform.TransformDir(omni::math::linalg::vec3d(0.0, 0.0, static_cast<double>(axisLength)));

        xtransform += translation;
        ytransform += translation;
        ztransform += translation;

        // draw the axis in global frame
        carb::Float3 centerPosition = { static_cast<float>(translation.GetArray()[0]),
                                        static_cast<float>(translation.GetArray()[1]),
                                        static_cast<float>(translation.GetArray()[2]) };
        float lineWidth = axisThickness;

        // x axis - red
        carb::ColorRgba xColor = { 1.0f, 0.0f, 0.0f, 1.0f };
        carb::Float3 xAxisPosition = { static_cast<float>(xtransform.GetArray()[0]),
                                       static_cast<float>(xtransform.GetArray()[1]),
                                       static_cast<float>(xtransform.GetArray()[2]) };
        m_lineDrawing->addVertex(centerPosition, xColor, lineWidth);
        m_lineDrawing->addVertex(xAxisPosition, xColor, lineWidth);

        // y axis - green
        carb::ColorRgba yColor = { 0.0f, 1.0f, 0.0f, 1.0f };
        carb::Float3 yAxisPosition = { static_cast<float>(ytransform.GetArray()[0]),
                                       static_cast<float>(ytransform.GetArray()[1]),
                                       static_cast<float>(ytransform.GetArray()[2]) };
        m_lineDrawing->addVertex(centerPosition, yColor, lineWidth);
        m_lineDrawing->addVertex(yAxisPosition, yColor, lineWidth);

        // z axis - blue
        carb::ColorRgba zColor = { 0.0f, 0.0f, 1.0f, 1.0f };
        carb::Float3 zAxisPosition = { static_cast<float>(ztransform.GetArray()[0]),
                                       static_cast<float>(ztransform.GetArray()[1]),
                                       static_cast<float>(ztransform.GetArray()[2]) };
        m_lineDrawing->addVertex(centerPosition, zColor, lineWidth);
        m_lineDrawing->addVertex(zAxisPosition, zColor, lineWidth);

        m_lineDrawing->draw();
    }

    virtual void reset()
    {
        m_lineDrawing->clear();
        m_lineDrawing->draw();
    }


private:
    float m_length{ 1 };
    float m_thickness{ 1 };
    long m_stageId;
    std::shared_ptr<drawing::PrimitiveDrawingHelper> m_lineDrawing{ nullptr };
    pxr::UsdStageRefPtr m_stage{ nullptr };
    usdrt::UsdStageRefPtr m_usdrtStage{ nullptr };
};

REGISTER_OGN_NODE()
}
}
}
