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
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/isaac/utils/Pose.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <OgnIsaacXPrimAxisVisualizerDatabase.h>

namespace omni
{
namespace isaac
{
namespace debug_draw
{
class OgnIsaacXPrimAxisVisualizer : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacXPrimAxisVisualizerDatabase::sInternalState<OgnIsaacXPrimAxisVisualizer>(nodeObj);
        omni::renderer::IDebugDraw* debugDrawPtr = carb::getCachedInterface<omni::renderer::IDebugDraw>();
        if (!debugDrawPtr)
        {
            CARB_LOG_ERROR("*** OgnIsaacXPrimAxisVisualizer failed to acquire debugdraw interface\n");
        }
        state.mLineDrawing = std::make_shared<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), debugDrawPtr,
            omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
    }

    static bool compute(OgnIsaacXPrimAxisVisualizerDatabase& db)
    {
        const auto& input_prim = db.inputs.xPrim();
        pxr::SdfPath primPath;
        if (input_prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(input_prim[0]);
        }
        else
        {
            db.logError("Omnigraph Error: no input prim found for visualization");
            return false;
        }

        auto& state = db.internalState<OgnIsaacXPrimAxisVisualizer>();
        state.mLength = db.inputs.length();
        state.mThickness = db.inputs.thickness();

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

        auto prim = state.mStage->GetPrimAtPath(primPath);

        if (prim.IsValid() == false)
        {
            state.mLineDrawing->clear();
            state.mLineDrawing->draw();
            db.logError("Could not find USD prim at path: %s", primPath.GetText());
            return false;
        }

        state.mLineDrawing->clear();

        usdrt::GfMatrix4d usdTransform =
            omni::isaac::utils::pose::computeWorldXformNoCache(state.mStage, state.mUsdrtStage, primPath);

        state.drawAxis(usdTransform, state.mLength, state.mThickness);
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
        carb::scenerenderer::PrimitiveVertex center;
        center.position.x = static_cast<float>(translation.GetArray()[0]);
        center.position.y = static_cast<float>(translation.GetArray()[1]);
        center.position.z = static_cast<float>(translation.GetArray()[2]);
        center.width = axisThickness;
        // x axis - red
        center.color = carb::ColorRgba{ 1.0f, 0.0f, 0.0f, 1.0f };
        carb::scenerenderer::PrimitiveVertex x_axis;
        x_axis.position =
            carb::Float3{ static_cast<float>(xtransform.GetArray()[0]), static_cast<float>(xtransform.GetArray()[1]),
                          static_cast<float>(xtransform.GetArray()[2]) };
        x_axis.width = center.width;
        x_axis.color = center.color;
        mLineDrawing->addVertex(center);
        mLineDrawing->addVertex(x_axis);

        // y axis - green
        center.color = carb::ColorRgba{ 0.0f, 1.0f, 0.0f, 1.0f };
        carb::scenerenderer::PrimitiveVertex y_axis;
        y_axis.position =
            carb::Float3{ static_cast<float>(ytransform.GetArray()[0]), static_cast<float>(ytransform.GetArray()[1]),
                          static_cast<float>(ytransform.GetArray()[2]) };
        y_axis.width = center.width;
        y_axis.color = center.color;
        mLineDrawing->addVertex(center);
        mLineDrawing->addVertex(y_axis);

        // z axis - blue
        center.color = carb::ColorRgba{ 0.0f, 0.0f, 1.0f, 1.0f };
        carb::scenerenderer::PrimitiveVertex z_axis;
        z_axis.position =
            carb::Float3{ static_cast<float>(ztransform.GetArray()[0]), static_cast<float>(ztransform.GetArray()[1]),
                          static_cast<float>(ztransform.GetArray()[2]) };
        z_axis.width = center.width;
        z_axis.color = center.color;
        mLineDrawing->addVertex(center);
        mLineDrawing->addVertex(z_axis);

        mLineDrawing->draw();
    }

    virtual void reset()
    {
        mLineDrawing->clear();
        mLineDrawing->draw();
    }


private:
    float mLength{ 1 };
    float mThickness{ 1 };
    long mStageId;
    std::shared_ptr<drawing::PrimitiveDrawingHelper> mLineDrawing{ nullptr };
    pxr::UsdStageRefPtr mStage{ nullptr };
    usdrt::UsdStageRefPtr mUsdrtStage{ nullptr };
};

REGISTER_OGN_NODE()
}
}
}
