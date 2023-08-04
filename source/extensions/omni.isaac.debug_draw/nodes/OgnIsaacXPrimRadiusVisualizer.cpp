// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on
#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/isaac/utils/Pose.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <OgnIsaacXPrimRadiusVisualizerDatabase.h>

namespace omni
{
namespace isaac
{
namespace debug_draw
{
class OgnIsaacXPrimRadiusVisualizer : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacXPrimRadiusVisualizerDatabase::sInternalState<OgnIsaacXPrimRadiusVisualizer>(nodeObj);
        omni::renderer::IDebugDraw* debugDrawPtr = carb::getCachedInterface<omni::renderer::IDebugDraw>();
        if (!debugDrawPtr)
        {
            CARB_LOG_ERROR("*** OgnIsaacXPrimRadiusVisualizer failed to acquire debugdraw interface\n");
        }
        state.mLineDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr,
            omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
    }

    static bool compute(OgnIsaacXPrimRadiusVisualizerDatabase& db)
    {
        auto primPath = pxr::SdfPath(db.inputs.xPrim.path());
        auto& state = db.internalState<OgnIsaacXPrimRadiusVisualizer>();
        state.mRadius = db.inputs.radius();
        state.mThickness = db.inputs.thickness();
        state.mSegments = db.inputs.segments();
        state.mXAxisColor = (carb::ColorRgba*)db.inputs.xAxisColor().data();
        state.mYAxisColor = (carb::ColorRgba*)db.inputs.yAxisColor().data();
        state.mZAxisColor = (carb::ColorRgba*)db.inputs.zAxisColor().data();
        state.mDrawXAxis = db.inputs.drawXAxis();
        state.mDrawYAxis = db.inputs.drawYAxis();
        state.mDrawZAxis = db.inputs.drawZAxis();

        if (state.mStage == nullptr)
        {
            //  Find our stage
            const GraphContextObj& context = db.abi_context();
            state.mStageId = context.iContext->getStageId(context);
            state.mStage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(state.mStageId));
            state.mUsdrtStage = usdrt::UsdStage::Attach({ (state.mStageId) });
            if (!state.mStage)
            {
                db.logError("Could not find USD stage %ld", state.mStageId);
                return false;
            }
        }
        state.mLineDrawing->clear();

        auto prim = state.mStage->GetPrimAtPath(primPath);
        usdrt::GfMatrix4d usdTransform =
            omni::isaac::utils::pose::computeWorldXformNoCache(state.mStage, state.mUsdrtStage, primPath);

        const carb::ColorRgba* color[3] = { state.mXAxisColor, state.mYAxisColor, state.mZAxisColor };
        const bool drawAxis[3] = { state.mDrawXAxis, state.mDrawYAxis, state.mDrawZAxis };
        return state.drawSphere(
            primPath, usdTransform, state.mSegments, state.mRadius, state.mThickness, color, drawAxis);
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

        carb::scenerenderer::PrimitiveVertex data;
        data.width = thickness;

        float angle = 0.0f;
        if (drawAxis[0])
        {
            for (int i = 0; i < segments; i++, angle += step)
            {
                omni::math::linalg::vec3d point =
                    usdTransform.TransformDir(omni::math::linalg::vec3d(0, radius * cos(angle), radius * sin(angle))) +
                    translation;
                data.position.x = static_cast<float>(point.GetArray()[0]);
                data.position.y = static_cast<float>(point.GetArray()[1]);
                data.position.z = static_cast<float>(point.GetArray()[2]);
                data.color = *color[0];

                mLineDrawing->addVertex(data);
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
                data.position.x = static_cast<float>(point.GetArray()[0]);
                data.position.y = static_cast<float>(point.GetArray()[1]);
                data.position.z = static_cast<float>(point.GetArray()[2]);
                data.color = *color[1];

                mLineDrawing->addVertex(data);
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
                data.position.x = static_cast<float>(point.GetArray()[0]);
                data.position.y = static_cast<float>(point.GetArray()[1]);
                data.position.z = static_cast<float>(point.GetArray()[2]);
                data.color = *color[2];

                mLineDrawing->addVertex(data);
            }
        }

        mLineDrawing->draw();
        return true;
    }

    virtual void reset()
    {
        mLineDrawing->clear();
        mLineDrawing->draw();
    }

private:
    float mRadius{ 1 };
    float mThickness{ 1 };
    int mSegments{ 1 };
    long mStageId;
    carb::ColorRgba* mXAxisColor{ nullptr };
    carb::ColorRgba* mYAxisColor{ nullptr };
    carb::ColorRgba* mZAxisColor{ nullptr };
    bool mDrawXAxis{ true };
    bool mDrawYAxis{ true };
    bool mDrawZAxis{ true };
    std::shared_ptr<drawing::PrimitiveDrawingHelper> mLineDrawing{ nullptr };
    pxr::UsdStageRefPtr mStage{ nullptr };
    usdrt::UsdStageRefPtr mUsdrtStage{ nullptr };
};

REGISTER_OGN_NODE()
}
}
}
