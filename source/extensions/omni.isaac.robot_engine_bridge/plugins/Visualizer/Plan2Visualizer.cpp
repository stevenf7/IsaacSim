// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/Types.h>
#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"
#include "Plan2Visualizer.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/isaac/utils/Curves.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

Plan2Visualizer::Plan2Visualizer() : IsaacComponent()
{

    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mDebugDrawPtr = framework->acquireInterface<omni::renderer::IDebugDraw>();
    if (!mDebugDrawPtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
        return;
    }
    mFastCachePtr = framework->acquireInterface<carb::fastcache::FastCache>();
    if (!mFastCachePtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire FastCache interface\n");
        return;
    }
}

Plan2Visualizer::~Plan2Visualizer()
{
}

void Plan2Visualizer::onStart()
{
    onComponentChange();
    mUnitScale = 1.0f / UsdGeomGetStageMetersPerUnit(mStage);
}


pxr::GfVec3f getOrientation(pxr::GfVec3f& normal, pxr::GfVec3f& tangent)
{
    pxr::GfVec3f binormal = pxr::GfCross(tangent.GetNormalized(), normal);
    return binormal.GetNormalized();
}

void Plan2Visualizer::tick()
{

    IsaacMessage<isaac_message::Plan2> plan2;
    {
        // Receive current command
        std::vector<IsaacHostBuffer> buffers;
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mInputChannel, header, plan2, buffers)))
        {
            isaac_message::Plan2::Reader plan = plan2.getProto();
            const auto& poseList = plan.getPoses();
            // Need atleast two points
            if (poseList.size() < 2)
            {
                return;
            }

            utils::curves::BSpline curve(utils::curves::eBasisCurveWrap::Pinned, 1);
            pxr::VtArray<pxr::GfVec3f> ctrlPoints;
            mLineData.clear();
            for (uint32_t i = 0; i < poseList.size(); i++)
            {
                const auto pose = poseList[i].getTranslation();

                ctrlPoints.push_back(pxr::GfVec3f(pose.getX(), pose.getY(), 0));
            }
            tessellatedPoints.clear();
            tessellatedTangents.clear();
            curve.tessellate(ctrlPoints, tessellatedPoints, tessellatedTangents);
            if (tessellatedPoints.size() < 2 || tessellatedPoints.size() != tessellatedTangents.size())
            {
                return;
            }
            for (uint32_t i = 0; i < tessellatedPoints.size() - 1; ++i)
            {
                const float* pointPtr = tessellatedPoints[i].data();
                const float* tangentPtr = tessellatedTangents[i].data();
                pxr::GfVec3f normal(0, 0, 1);
                pxr::GfVec3f cpi = { pointPtr[0], pointPtr[1], pointPtr[2] };
                pxr::GfVec3f tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
                pxr::GfVec3f binormal = getOrientation(normal, tangent);
                pxr::GfVec3f offset = binormal * mWidth;
                pxr::GfVec3f a1 = cpi - offset;
                pxr::GfVec3f b1 = cpi + offset;


                pointPtr = tessellatedPoints[i + 1].data();
                tangentPtr = tessellatedTangents[i + 1].data();
                cpi = { pointPtr[0], pointPtr[1], pointPtr[2] };
                tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
                binormal = getOrientation(normal, tangent);
                offset = binormal * mWidth;
                pxr::GfVec3f a2 = cpi - offset;
                pxr::GfVec3f b2 = cpi + offset;
                DebugData temp;

                temp.startPos = { a1[0], a1[1], a1[2] };
                temp.endPos = { a2[0], a2[1], a2[2] };

                mLineData.push_back(temp);

                temp.startPos = { b1[0], b1[1], b1[2] };
                temp.endPos = { b2[0], b2[1], b2[2] };

                mLineData.push_back(temp);

                temp.startPos = { b1[0], b1[1], b1[2] };
                temp.endPos = { a2[0], a2[1], a2[2] };

                mLineData.push_back(temp);

                // First line
                if (i == 0)
                {
                    temp.startPos = { b1[0], b1[1], b1[2] };
                    temp.endPos = { a1[0], a1[1], a1[2] };

                    mLineData.push_back(temp);
                }
                // last line
                if (i == tessellatedPoints.size() - 2)
                {
                    temp.startPos = { b2[0], b2[1], b2[2] };
                    temp.endPos = { a2[0], a2[1], a2[2] };

                    mLineData.push_back(temp);
                }
            }
        }
    }
    pxr::GfMatrix4d trans = pxr::GfMatrix4d(1);

    if (mParentPath != pxr::SdfPath())
    {
        carb::fastcache::Transform parentTrans;
        mFastCachePtr->getTransform(mParentPath, parentTrans);
        trans = utils::conversions::asGfMatrix4d(parentTrans);
    }


    releaseDebugLineList();
    createDebugLineList(mLineData.size());
    size_t drawIndex = 0;


    for (auto& line : mLineData)
    {

        auto start = (utils::conversions::asGfVec3f(line.startPos) + mOffset) * mUnitScale;
        auto end = (utils::conversions::asGfVec3f(line.endPos) + mOffset) * mUnitScale;

        if (mParentPath != pxr::SdfPath())
        {
            start = trans.Transform(start);
            end = trans.Transform(end);
        }
        mDebugDrawPtr->setLine(mShapeDebugLineBuffer, drawIndex++, { start[0], start[1], start[2] }, mColorValue,
                               { end[0], end[1], end[2] }, mColorValue);
    }
}

void Plan2Visualizer::onStop()
{
    releaseDebugLineList();
}

void Plan2Visualizer::onComponentChange()
{
    // CARB_LOG_ERROR("Plan2Visualizer Update");
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEnginePlan2Visualizer& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEnginePlan2Visualizer)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mInputChannel);
    isaac::utils::safeGetAttribute(typedPrim.GetWidthAttr(), mWidth);
    isaac::utils::safeGetAttribute(typedPrim.GetColorAttr(), mColor);
    isaac::utils::safeGetAttribute(typedPrim.GetOffsetAttr(), mOffset);

    int red = 255 * mColor[0];
    int grn = 255 * mColor[1];
    int blu = 255 * mColor[2];
    int alpha = 255 * mColor[3];

    mColorValue = blu + (grn << 8) + (red << 16) + (alpha << 24);

    pxr::SdfPathVector targets;
    typedPrim.GetParentPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mParentPath = targets[0];
}


void Plan2Visualizer::createDebugLineList(size_t size)
{
    if (mShapeDebugLineBuffer == omni::renderer::IDebugDraw::eInvalidBuffer)
    {
        mShapeDebugLineBuffer = mDebugDrawPtr->allocateLineBuffer(size);
        mShapeDebugRenderInstanceBuffer = mDebugDrawPtr->allocateRenderInstanceBuffer(mShapeDebugLineBuffer, 1);
        float transform[16] = {};
        transform[0] = 1.f;
        transform[1 + 4] = 1.f;
        transform[2 + 8] = 1.f;
        transform[3 + 12] = 1.f;

        mDebugDrawPtr->setRenderInstance(mShapeDebugRenderInstanceBuffer, 0, &transform[0], 0);
    }
}

void Plan2Visualizer::releaseDebugLineList()
{
    if (mShapeDebugLineBuffer != omni::renderer::IDebugDraw::eInvalidBuffer)
    {
        mDebugDrawPtr->deallocateLineBuffer(mShapeDebugLineBuffer);
        mDebugDrawPtr->deallocateRenderInstanceBuffer(mShapeDebugRenderInstanceBuffer);
        mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    }
}
}
}
}
