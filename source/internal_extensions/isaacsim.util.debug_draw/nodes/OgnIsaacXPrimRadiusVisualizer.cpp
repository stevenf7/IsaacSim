// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on
#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Pose.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <OgnIsaacXPrimRadiusVisualizerDatabase.h>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{
class OgnIsaacXPrimRadiusVisualizer : public isaacsim::core::includes::BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacXPrimRadiusVisualizerDatabase::sPerInstanceState<OgnIsaacXPrimRadiusVisualizer>(nodeObj, instanceId);
        state.m_lineDrawing = std::make_shared<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(),
            isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
    }

    static bool compute(OgnIsaacXPrimRadiusVisualizerDatabase& db)
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
        auto& state = db.perInstanceState<OgnIsaacXPrimRadiusVisualizer>();
        state.m_radius = db.inputs.radius();
        state.m_thickness = db.inputs.thickness();
        state.m_segments = db.inputs.segments();
        state.m_xAxisColor = (carb::ColorRgba*)db.inputs.xAxisColor().data();
        state.m_yAxisColor = (carb::ColorRgba*)db.inputs.yAxisColor().data();
        state.m_zAxisColor = (carb::ColorRgba*)db.inputs.zAxisColor().data();
        state.m_drawXAxis = db.inputs.drawXAxis();
        state.m_drawYAxis = db.inputs.drawYAxis();
        state.m_drawZAxis = db.inputs.drawZAxis();

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

        const carb::ColorRgba* color[3] = { state.m_xAxisColor, state.m_yAxisColor, state.m_zAxisColor };
        const bool drawAxis[3] = { state.m_drawXAxis, state.m_drawYAxis, state.m_drawZAxis };
        return state.drawSphere(
            primPath, usdTransform, state.m_segments, state.m_radius, state.m_thickness, color, drawAxis);
    }

    bool drawSphere(const pxr::SdfPath& primPath,
                    usdrt::GfMatrix4d& usdTransform,
                    const int& segments,
                    const float& radius,
                    const float& thickness,
                    const carb::ColorRgba* color[],
                    const bool drawAxis[])
    {
        // will not visualize if the visualize flag is off or if radius is <=0 (full body sensor)
        if (radius <= 0)
        {
            CARB_LOG_ERROR_ONCE(
                "Could not draw sphere, input radius is 0 or negative. To visualzie position, please use IsaacXPrimAxisVisualizer");
            return false;
        }

        float step = static_cast<float>(2 * 3.1415926 / segments);

        omni::math::linalg::vec3d translation = usdTransform.ExtractTranslation();
        usdTransform.Orthonormalize();

        carb::Float3 position;
        float width = thickness;

        float angle = 0.0f;
        if (drawAxis[0])
        {
            for (int i = 0; i < segments; i++, angle += step)
            {
                omni::math::linalg::vec3d point =
                    usdTransform.TransformDir(omni::math::linalg::vec3d(0, radius * cos(angle), radius * sin(angle))) +
                    translation;
                position.x = static_cast<float>(point.GetArray()[0]);
                position.y = static_cast<float>(point.GetArray()[1]);
                position.z = static_cast<float>(point.GetArray()[2]);

                m_lineDrawing->addVertex(position, *color[0], width);
            }
        }

        if (drawAxis[1])
        {
            angle = 0.0f;
            for (int i = 0; i < segments; i++, angle += step)
            {
                omni::math::linalg::vec3d point =
                    usdTransform.TransformDir(omni::math::linalg::vec3d(radius * cos(angle), 0, radius * sin(angle))) +
                    translation;
                position.x = static_cast<float>(point.GetArray()[0]);
                position.y = static_cast<float>(point.GetArray()[1]);
                position.z = static_cast<float>(point.GetArray()[2]);

                m_lineDrawing->addVertex(position, *color[1], width);
            }
        }

        if (drawAxis[2])
        {
            angle = 0.0f;
            for (int i = 0; i < segments; i++, angle += step)
            {
                omni::math::linalg::vec3d point =
                    usdTransform.TransformDir(omni::math::linalg::vec3d(radius * cos(angle), radius * sin(angle), 0)) +
                    translation;
                position.x = static_cast<float>(point.GetArray()[0]);
                position.y = static_cast<float>(point.GetArray()[1]);
                position.z = static_cast<float>(point.GetArray()[2]);

                m_lineDrawing->addVertex(position, *color[2], width);
            }
        }

        m_lineDrawing->draw();
        return true;
    }

    virtual void reset()
    {
        m_lineDrawing->clear();
        m_lineDrawing->draw();
    }

private:
    float m_radius{ 1 };
    float m_thickness{ 1 };
    int m_segments{ 1 };
    long m_stageId;
    carb::ColorRgba* m_xAxisColor{ nullptr };
    carb::ColorRgba* m_yAxisColor{ nullptr };
    carb::ColorRgba* m_zAxisColor{ nullptr };
    bool m_drawXAxis{ true };
    bool m_drawYAxis{ true };
    bool m_drawZAxis{ true };
    std::shared_ptr<drawing::PrimitiveDrawingHelper> m_lineDrawing{ nullptr };
    pxr::UsdStageRefPtr m_stage{ nullptr };
    usdrt::UsdStageRefPtr m_usdrtStage{ nullptr };
};

REGISTER_OGN_NODE()
}
}
}
