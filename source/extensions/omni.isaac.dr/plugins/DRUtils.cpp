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
void getEulerAngles(const pxr::GfQuath& q, pxr::GfVec3f& angles)
{
    // https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles

    pxr::GfVec3h imag = q.GetImaginary();
    pxr::GfHalf real = q.GetReal();

    const float sinr_cosp = 2 * (real * imag[0] + imag[1] * imag[2]);
    const float cosr_cosp = 1 - 2 * (imag[0] * imag[0] + imag[1] * imag[1]);
    angles[0] = atan2f(sinr_cosp, cosr_cosp);

    // pitch (y-axis rotation)
    const float sinp = 2 * (real * imag[1] - imag[2] * imag[0]);
    if (fabsf(sinp) >= 1)
        angles[1] = copysignf(float(1.57079632679489661923), sinp); // use 90 degrees if out of range
    else
        angles[1] = asinf(sinp);

    // yaw (z-axis rotation)
    const float siny_cosp = 2 * (real * imag[2] + imag[0] * imag[1]);
    const float cosy_cosp = 1 - 2 * (imag[1] * imag[1] + imag[2] * imag[2]);
    angles[2] = atan2f(siny_cosp, cosy_cosp);
}

float radianToAngle(float radian)
{
    return (90.0f * radian) / float(1.57079632679489661923);
}

pxr::GfRotation getCombinedRotation(pxr::UsdPrim& prim, pxr::GfRotation roll, pxr::GfRotation pitch, pxr::GfRotation yaw)
{
    pxr::UsdGeomXformable xform(prim);
    bool resetXFormStack;
    auto xformOps = xform.GetOrderedXformOps(&resetXFormStack);
    PXR_NS::VtTokenArray xformOpOrders;
    xform.GetXformOpOrderAttr().Get(&xformOpOrders);

    for (auto xformOp : xformOps)
    {
        // set based on prim's rotation order
        if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateXYZ)
            return roll * pitch * yaw;
        else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateXZY)
            return roll * yaw * pitch;
        else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateYXZ)
            return pitch * roll * yaw;
        else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateYZX)
            return pitch * yaw * roll;
        else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateZXY)
            return yaw * roll * pitch;
        else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeRotateZYX)
            return yaw * pitch * roll;
    }
    // Default rotation order is XYZ
    return roll * pitch * yaw;
}
}
}
}
