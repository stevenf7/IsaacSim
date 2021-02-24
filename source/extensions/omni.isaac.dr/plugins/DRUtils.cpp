// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "DRUtils.h"

namespace omni
{
namespace isaac
{
namespace dr
{
std::vector<std::vector<pxr::GfVec3f>> triangulatePolygon(std::vector<pxr::GfVec3f>& samplePoints)
{
    std::vector<std::vector<pxr::GfVec3f>> triangulatedPolygon;
    for (unsigned int i = 0; i < samplePoints.size() - 2; i++)
    {
        std::vector<pxr::GfVec3f> triplets;
        triplets.push_back(samplePoints[i]);
        triplets.push_back(samplePoints[i + 1]);
        triplets.push_back(samplePoints[i + 2]);
        triangulatedPolygon.push_back(triplets);
    }
    return triangulatedPolygon;
}
// A utility function to find distance between two points in a plane
double dist(pxr::GfVec3f p1, pxr::GfVec3f p2)
{
    return sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]));
}
double areaTriangle(std::vector<pxr::GfVec3f> trianglePts)
{
    double a = dist(trianglePts[0], trianglePts[1]);
    double b = dist(trianglePts[1], trianglePts[2]);
    double c = dist(trianglePts[0], trianglePts[2]);
    double s = (a + b + c) / 2.0;
    return sqrt(s * (s - a) * (s - b) * (s - c));
}
std::vector<double> generateDistribution(std::vector<std::vector<pxr::GfVec3f>> allTriangles)
{
    double totalArea = 0.0;
    std::vector<double> cumulativeAreaDistribution;
    cumulativeAreaDistribution.push_back(totalArea);
    for (std::vector<pxr::GfVec3f> triangle : allTriangles)
    {
        double newArea = areaTriangle(triangle);
        totalArea += newArea;
        cumulativeAreaDistribution.push_back(totalArea);
    }
    for (unsigned int i = 0; i < cumulativeAreaDistribution.size(); i++)
        cumulativeAreaDistribution[i] /= totalArea;
    return cumulativeAreaDistribution;
}
}
}
}
