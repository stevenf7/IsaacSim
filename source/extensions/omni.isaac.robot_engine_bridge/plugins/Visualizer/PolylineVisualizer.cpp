// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "PolylineVisualizer.h"

#include "../Core/IsaacComponent.h"
#include "../Thirdparty/csscolorparser.hpp"

#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/debug_draw/Curves.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

PolylineVisualizer::PolylineVisualizer() : IsaacComponent()
{


    mDebugDrawPtr = carb::getCachedInterface<omni::renderer::IDebugDraw>();
    if (!mDebugDrawPtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
        return;
    }
    mFastCachePtr = carb::getCachedInterface<carb::fastcache::FastCache>();
    if (!mFastCachePtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire FastCache interface\n");
        return;
    }

    mJsonSerializer = carb::getCachedInterface<carb::dictionary::ISerializer>("carb.dictionary.serializer-json.plugin");
    if (!mJsonSerializer)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::ISerializer interface");
        return;
    }

    mIDict = carb::getCachedInterface<carb::dictionary::IDictionary>();

    if (!mIDict)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::IDictionary interface");
        return;
    }
    mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
}

PolylineVisualizer::~PolylineVisualizer()
{
}

void PolylineVisualizer::onStart()
{
    onComponentChange();
    mUnitScale = 1.0f / UsdGeomGetStageMetersPerUnit(mStage);
}


pxr::GfVec3f getOrientation(pxr::GfVec3f& normal, pxr::GfVec3f& tangent)
{
    pxr::GfVec3f binormal = pxr::GfCross(tangent.GetNormalized(), normal);
    return binormal.GetNormalized();
}

void PolylineVisualizer::tick()
{

    IsaacMessage<isaac_message::Json> jsonProto;
    {
        // Receive current command
        std::vector<IsaacHostBuffer> buffers;
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mInputChannel, header, jsonProto, buffers)))
        {
            std::string jsonString = jsonProto.getProto().getSerialized();
            // Uncomment to print out the json we receive to help debug
            // CARB_LOG_ERROR("%s", jsonString.c_str());
            carb::dictionary::Item* jsonBase = mJsonSerializer->createDictionaryFromStringBuffer(jsonString.c_str());
            // currently only supports plan2
            const carb::dictionary::Item* view = mIDict->getItem(jsonBase, "v");

            if (view)
            {
                std::string typeStr = mIDict->getItemName(view);
                // we have some data to deal with
                const carb::dictionary::Item* viewData = mIDict->getItem(view, "d");
                if (viewData)
                {
                    size_t numItems = mIDict->getArrayLength(viewData);
                    std::string typeStr = mIDict->getItemName(viewData);

                    for (size_t i = 0; i < numItems; i++)
                    {

                        const carb::dictionary::Item* arrayItem = mIDict->getItemAt(viewData, i);

                        const carb::dictionary::Item* type = mIDict->getItem(arrayItem, "t");
                        const carb::dictionary::Item* style = mIDict->getItem(arrayItem, "s");
                        const carb::dictionary::Item* data = mIDict->getItem(arrayItem, "d");

                        if (type && mIDict->getItemType(type) == carb::dictionary::ItemType::eString)
                        {
                            std::string typeStr = mIDict->getItemName(type);
                        }
                        if (style && mIDict->getItemType(style) == carb::dictionary::ItemType::eDictionary)
                        {
                            std::string styleStr = mIDict->getItemName(style);
                            const carb::dictionary::Item* fillType = mIDict->getItem(style, "f");

                            // fill type must be defined and also true currently
                            // TODO: support more rendering types
                            if (!fillType || mIDict->getAsBool(fillType) == false)
                            {
                                CARB_LOG_WARN("only filled supported, defaulting to that");
                            }

                            const carb::dictionary::Item* size = mIDict->getItem(style, "s");
                            const carb::dictionary::Item* color = mIDict->getItem(style, "c");
                            const carb::dictionary::Item* alpha = mIDict->getItem(style, "a");
                            if (size && mIDict->getItemType(size) == carb::dictionary::ItemType::eFloat)
                            {
                                mWidth = mIDict->getAsFloat(size);
                                // printf("SIZE %f\n", mWidth);
                            }

                            if (color && mIDict->getItemType(color) == carb::dictionary::ItemType::eString)
                            {
                                std::string colorStr = mIDict->getStringBuffer(color);

                                auto color = CSSColorParser::parse(colorStr);
                                if (color)
                                {
                                    mRed = color->r;
                                    mGreen = color->g;
                                    mBlue = color->b;
                                }
                            }
                            if (alpha && mIDict->getItemType(alpha) == carb::dictionary::ItemType::eFloat)
                            {
                                mAlpha = 255 * mIDict->getAsFloat(alpha);
                            }


                            mColorValue = mBlue + (mGreen << 8) + (mRed << 16) + (mAlpha << 24);
                        }
                        size_t numDataItems = mIDict->getArrayLength(data);
                        pxr::VtArray<pxr::GfVec3f> ctrlPoints;


                        for (size_t i = 0; i < numDataItems; i++)
                        {
                            const carb::dictionary::Item* dataItem = mIDict->getItemAt(data, i);

                            if (dataItem && mIDict->getItemType(dataItem) == carb::dictionary::ItemType::eDictionary)
                            {
                                std::string dataStr = mIDict->getItemName(dataItem);


                                const carb::dictionary::Item* dataType = mIDict->getItem(dataItem, "t");


                                if (dataType && mIDict->getItemType(dataType) == carb::dictionary::ItemType::eString)
                                {
                                    std::string typeStr = mIDict->getStringBuffer(dataType);
                                    if (typeStr == "pnts")
                                    {
                                        const carb::dictionary::Item* pointData = mIDict->getItem(dataItem, "p");
                                        size_t numPoints = mIDict->getArrayLength(pointData);
                                        // Need atleast two points
                                        if (numPoints < 2)
                                        {
                                            return;
                                        }

                                        for (size_t i = 0; i < numPoints; i++)
                                        {
                                            // Parse depending on whether the data is 2d or 3d
                                            const carb::dictionary::Item* point = mIDict->getItemAt(pointData, i);
                                            if (mIDict->getArrayLength(point) == 2)
                                            {
                                                carb::Float2 p = mIDict->get<carb::Float2>(point);
                                                ctrlPoints.push_back(pxr::GfVec3f(p.x, p.y, 0));
                                            }
                                            else if (mIDict->getArrayLength(point) == 3)
                                            {
                                                carb::Float3 p = mIDict->get<carb::Float3>(point);
                                                ctrlPoints.push_back(pxr::GfVec3f(p.x, p.y, p.z));
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        debug_draw::curves::BSpline curve(debug_draw::curves::eBasisCurveWrap::Pinned, 1);

                        mLineData.clear();
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
            }
        }
    }
    pxr::GfMatrix4d trans = pxr::GfMatrix4d(1);

    if (mParentPrim && mParentPrim.IsA<pxr::UsdGeomXformable>())
    {
        // mFastCachePtr->getTransform(mParentPrimPath, parentTrans);

        pxr::UsdTimeCode parentPrimTimeCode = pxr::UsdTimeCode::Default();
        std::vector<double> times;
        pxr::UsdGeomXformable(mParentPrim).GetTimeSamples(&times);

        if (times.size() > 1)
        {
            parentPrimTimeCode = round(mTimeline->getCurrentTime() * this->mStage->GetTimeCodesPerSecond());
        }

        trans = omni::usd::UsdUtils::getWorldTransformMatrix(mParentPrim, parentPrimTimeCode);
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
        // printf("pts: [%f %f %f] [%f %f %f]\n", start[0], start[1], start[2], end[0], end[1], end[2]);
        mDebugDrawPtr->setLine(mShapeDebugLineBuffer, drawIndex++, { start[0], start[1], start[2] }, mColorValue,
                               { end[0], end[1], end[2] }, mColorValue);
    }
}

void PolylineVisualizer::onStop()
{
    releaseDebugLineList();
}

void PolylineVisualizer::onComponentChange()
{
    // CARB_LOG_ERROR("PolylineVisualizer Update");
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEnginePolylineVisualizer& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEnginePolylineVisualizer)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mInputChannel);
    isaac::utils::safeGetAttribute(typedPrim.GetWidthAttr(), mWidth);
    isaac::utils::safeGetAttribute(typedPrim.GetColorAttr(), mColor);
    isaac::utils::safeGetAttribute(typedPrim.GetOffsetAttr(), mOffset);

    mRed = 255 * mColor[0];
    mGreen = 255 * mColor[1];
    mBlue = 255 * mColor[2];
    mAlpha = 255 * mColor[3];

    mColorValue = mBlue + (mGreen << 8) + (mRed << 16) + (mAlpha << 24);

    pxr::SdfPathVector targets;
    typedPrim.GetParentPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mParentPath = targets[0];
    mParentPrim = mStage->GetPrimAtPath(mParentPath);
    if (!mParentPrim)
    {
        CARB_LOG_ERROR("Parent Prim %s not valid", mParentPath.GetString().c_str());
    }
}


void PolylineVisualizer::createDebugLineList(size_t size)
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

void PolylineVisualizer::releaseDebugLineList()
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
