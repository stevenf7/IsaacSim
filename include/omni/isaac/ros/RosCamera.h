// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>

namespace omni
{
namespace isaac
{
namespace ros_base
{
void getCameraIntrinsics(pxr::UsdGeomCamera cameraPrim,
                         carb::sensors::SensorInfo imgInfo,
                         float& fx,
                         float& fy,
                         float& cx,
                         float& cy,
                         float& fthetaPolyA,
                         float& fthetaPolyB,
                         float& fthetaPolyC,
                         float& fthetaPolyD,
                         float& fthetaPolyE,
                         pxr::TfToken& projectionType)
{

    float focalLength;
    cameraPrim.GetFocalLengthAttr().Get(&focalLength);

    float horizontalAperture, verticalAperture;
    cameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    cameraPrim.GetVerticalApertureAttr().Get(&verticalAperture);

    // verticalAperture =
    //     static_cast<float>(imgInfo.tex.height) / static_cast<float>(imgInfo.tex.width) * horizontalAperture;

    fx = imgInfo.tex.width * focalLength / horizontalAperture;
    fy = imgInfo.tex.height * focalLength / verticalAperture;
    cx = imgInfo.tex.width * 0.5f;
    cy = imgInfo.tex.height * 0.5;

    pxr::UsdPrim prim = cameraPrim.GetPrim();
    prim.GetAttribute(pxr::TfToken("cameraProjectionType")).Get(&projectionType);
    prim.GetAttribute(pxr::TfToken("fthetaPolyA")).Get(&fthetaPolyA);
    prim.GetAttribute(pxr::TfToken("fthetaPolyB")).Get(&fthetaPolyB);
    prim.GetAttribute(pxr::TfToken("fthetaPolyC")).Get(&fthetaPolyC);
    prim.GetAttribute(pxr::TfToken("fthetaPolyD")).Get(&fthetaPolyD);
    prim.GetAttribute(pxr::TfToken("fthetaPolyE")).Get(&fthetaPolyE);
}
}
}
}
