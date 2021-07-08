// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Types.h>
#include <carb/dictionary/DictionaryUtils.h>

struct VisualizerStyle
{
    carb::ColorRgba color;
    float width;
    bool filled;
};

pxr::GfVec3f getOrientation(pxr::GfVec3f& normal, pxr::GfVec3f& tangent)
{
    pxr::GfVec3f binormal = pxr::GfCross(tangent.GetNormalized(), normal);
    return binormal.GetNormalized();
}


void drawSpline(VisualizerStyle& style, std::vector<carb::Float3>& controlPoints)
{
    utils::curves::BSpline curve(utils::curves::eBasisCurveWrap::Pinned, 1);

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


VisualizerStyle parseStyle(carb::dictionary::IDictionary* mIDict,
                           const carb::dictionary::Item* style,
                           VisualizerStyle& visualStyle)
{

    std::string styleStr = mIDict->getItemName(style);
    const carb::dictionary::Item* fillType = mIDict->getItem(style, "f");

    if (fillType && mIDict->getItemType(fillType) == carb::dictionary::ItemType::eBool)
    {
        visualStyle.filled = mIDict->getAsBool(fillType);
    }
    const carb::dictionary::Item* size = mIDict->getItem(style, "s");
    const carb::dictionary::Item* color = mIDict->getItem(style, "c");
    const carb::dictionary::Item* alpha = mIDict->getItem(style, "a");
    if (size && mIDict->getItemType(size) == carb::dictionary::ItemType::eFloat)
    {
        visualStyle.width = mIDict->getAsFloat(size);
    }

    if (color && mIDict->getItemType(color) == carb::dictionary::ItemType::eString)
    {
        std::string colorStr = mIDict->getStringBuffer(color);

        auto color = CSSColorParser::parse(colorStr);
        if (color)
        {
            visualStyle.color.r = color->r / 255.0f;
            visualStyle.color.g = color->g / 255.0f;
            visualStyle.color.b = color->b / 255.0f;
        }
    }
    if (alpha && mIDict->getItemType(alpha) == carb::dictionary::ItemType::eFloat)
    {
        visualStyle.color.a = mIDict->getAsFloat(alpha);
    }
    return visualStyle;
}
void parseDataItem(carb::dictionary::IDictionary* mIDict,
                   const carb::dictionary::Item* dataItem,
                   std::vector<carb::Float3>& controlPoints,
                   std::string& typeStr)
{

    std::string dataStr = mIDict->getItemName(dataItem);
    const carb::dictionary::Item* dataType = mIDict->getItem(dataItem, "t");

    if (dataType && mIDict->getItemType(dataType) == carb::dictionary::ItemType::eString)
    {
        typeStr = mIDict->getStringBuffer(dataType);
    }
    const carb::dictionary::Item* pointData = mIDict->getItem(dataItem, "p");
    size_t numPoints = mIDict->getArrayLength(pointData);


    for (size_t i = 0; i < numPoints; i++)
    {
        // Parse depending on whether the data is 2d or 3d
        const carb::dictionary::Item* point = mIDict->getItemAt(pointData, i);
        if (mIDict->getArrayLength(point) == 2)
        {
            carb::Float2 p = mIDict->get<carb::Float2>(point);
            controlPoints.push_back({ p.x, p.y, 0 });
        }
        else if (mIDict->getArrayLength(point) == 3)
        {
            controlPoints.push_back(mIDict->get<carb::Float3>(point));
        }
        else
        {
            continue;
        }
    }
}

void parseData(carb::dictionary::IDictionary* mIDict, const carb::dictionary::Item* data, VisualizerStyle& style)
{
    size_t numDataItems = mIDict->getArrayLength(data);


    for (size_t i = 0; i < numDataItems; i++)
    {
        const carb::dictionary::Item* dataItem = mIDict->getItemAt(data, i);
        if (!dataItem || mIDict->getItemType(dataItem) != carb::dictionary::ItemType::eDictionary)
        {
            continue;
        }
        std::string typeStr = "pnts";

        std::vector<carb::Float3> controlPoints;
        parseDataItem(mIDict, dataItem, controlPoints, typeStr);

        if (typeStr == "pnts") // polyline or line
        {
            if (controlPoints.size() < 2) // Need atleast two points
            {
                continue;
            }

            // genenerate spline
        }
        else if (typeStr == "line")
        {
            if (controlPoints.size() != 2) // Need atleast two points
            {
                continue;
            }
            // add a single line
        }
        else if (typeStr == "point_cloud")
        {
            // add all to points renderer
        }
        else
        {
            return; // type is not supported
        }
    }
}


void parseItem(carb::dictionary::IDictionary* mIDict, const carb::dictionary::Item* arrayItem)
{

    // const carb::dictionary::Item* type = mIDict->getItem(arrayItem, "t");
    const carb::dictionary::Item* style = mIDict->getItem(arrayItem, "s");
    const carb::dictionary::Item* data = mIDict->getItem(arrayItem, "d");

    // if (type && mIDict->getItemType(type) == carb::dictionary::ItemType::eString)
    // {
    //     std::string typeStr = mIDict->getItemName(type);
    // }
    VisualizerStyle visualStyle;
    if (style && mIDict->getItemType(style) == carb::dictionary::ItemType::eDictionary)
    {
        parseStyle(mIDict, style, visualStyle);
    }
    if (data && mIDict->getArrayLength(data) > 0)
    {
        parseData(mIDict, data, visualStyle);
    }
}


void parseSightJson(carb::dictionary::IDictionary* mIDict, const carb::dictionary::Item* view)
{
    const carb::dictionary::Item* viewData = mIDict->getItem(view, "d");
    if (!viewData)
    {
        return;
    }

    for (size_t i = 0; i < mIDict->getArrayLength(viewData); i++)
    {
        const carb::dictionary::Item* arrayItem = mIDict->getItemAt(viewData, i);
        parseItem(mIDict, arrayItem);
    }
}
