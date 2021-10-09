// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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
namespace dr
{
std::vector<std::vector<pxr::GfVec3f>> triangulatePolygon(std::vector<pxr::GfVec3f>& samplePoints);

double dist(pxr::GfVec3f p1, pxr::GfVec3f p2);

double areaTriangle(std::vector<pxr::GfVec3f> trianglePts);

std::vector<double> generateDistribution(std::vector<std::vector<pxr::GfVec3f>> allTriangles);

void getEulerAngles(const pxr::GfQuath& q, pxr::GfVec3f& angles);

float radianToAngle(float radian);

pxr::GfRotation getCombinedRotation(pxr::UsdPrim& prim, pxr::GfRotation roll, pxr::GfRotation pitch, pxr::GfRotation yaw);
}
}
}
