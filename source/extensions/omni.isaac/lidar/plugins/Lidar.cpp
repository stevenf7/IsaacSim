// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "Lidar.h"

#include <carb/physx/physx.h>
#include <carb/InterfaceUtils.h>

#include <omni/usd/UsdUtils.h>
#include <omni/isaac/utils/Conversions.h>

using namespace physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace lidar
{


carb::physics::PhysX* Lidar::physx = nullptr;
UsdStageRefPtr Lidar::stage = nullptr;
float Lidar::metersPerUnit = 1.0f;


Lidar::~Lidar()
{
    clearDebugLines();
}

Lidar::Lidar(const LidarSchemaLidar& prim)
{

    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mDynamicControlPtr = framework->acquireInterface<omni::isaac::dynamic_control::DynamicControl>();
    if (!mDynamicControlPtr)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }

    init(prim);
}


void Lidar::init(const pxr::LidarSchemaLidar& prim)
{
    this->prim = prim;

    // NOTE : Gross
    // TODO : Not this
    valid = prim.GetHorizontalFovAttr().HasValue() && prim.GetVerticalFovAttr().HasValue() &&
            prim.GetRotationRateAttr().HasValue() && prim.GetHorizontalResolutionAttr().HasValue() &&
            prim.GetVerticalResolutionAttr().HasValue() && prim.GetMinRangeAttr().HasValue() &&
            prim.GetMaxRangeAttr().HasValue() && prim.GetHighLodAttr().HasValue() &&
            prim.GetDrawLidarPointsAttr().HasValue();

    if (!valid)
        return;


    // Copy over the stuff from the prim
    prim.GetHorizontalFovAttr().Get(&horizontalFov);
    prim.GetVerticalFovAttr().Get(&verticalFov);
    prim.GetRotationRateAttr().Get(&rotationRate);
    prim.GetHorizontalResolutionAttr().Get(&horizontalResolution);
    prim.GetVerticalResolutionAttr().Get(&verticalResolution);
    prim.GetMinRangeAttr().Get(&minRange);
    prim.GetMaxRangeAttr().Get(&maxRange);
    prim.GetHighLodAttr().Get(&highLod);
    prim.GetDrawLidarPointsAttr().Get(&drawLidarPoints);

    // printf("%f %f %f %f %f %f %f %d %d\n",
    //        horizontalFov,
    //        verticalFov,
    //        rotationRate,
    //        horizontalResolution,
    //        verticalResolution,
    //        minRange,
    //        maxRange,
    //        highLod,
    //        drawLidarPoints);


    minDepth = minRange / metersPerUnit;
    maxDepth = maxRange / metersPerUnit;

    maxStepSize = float(1.0 / 30.0);

    cols = int(horizontalFov / horizontalResolution);

    // Add one so that we have symmetry
    // Otherwise we are missing one angle for the Velodyne 16 case as 30/2 = 15
    rows = highLod ? int(verticalFov / verticalResolution) + 1 : 1;

    if (rotationRate != 0.0f && rotationRate > 1.0 / maxStepSize)
        rotationRate = float(1.0 / maxStepSize);


    colScanSpeed = cols * rotationRate;
    maxColsPerTick = int(colScanSpeed * maxStepSize);

    depth.assign(rows * cols, 0);
    intensity.assign(rows * cols, 0);
    zenith.assign(rows, 0.0f);
    azimuth.assign(cols, 0.0f);

    float startAzimuth = -0.5f * horizontalFov;
    float startZenith = -0.5f * verticalFov;

    for (int col = 0; col < cols; col++)
        azimuth[col] = float((startAzimuth + col * horizontalResolution) * M_PI / 180.0f);

    for (int row = 0; row < rows; row++)
        zenith[row] = float((startZenith + row * verticalResolution) * M_PI / 180.0f);

    if (!highLod)
        zenith[0] = 0.0f;

    lastAzimuth.assign(maxColsPerTick, 0.0f);
    lastDepth.assign(rows * maxColsPerTick, 0);

    lastCol = 0;
    lastNumColsTicked = 0;
    remainingTime = 0.0f;

    clearDebugLines();

    omni::isaac::dynamic_control::DcObjectType primType =
        mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
    if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        omni::isaac::dynamic_control::DcHandle artculationHandle =
            mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
        mRigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
    }
    else if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
    {
        mRigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
    }
    else
    {
        mRigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    }
}

void Lidar::scan(int start, int stop)
{
    // printf("%f %f %f %f %f %f %f %d %d\n",
    //        horizontalFov,
    //        verticalFov,
    //        rotationRate,
    //        horizontalResolution,
    //        verticalResolution,
    //        minRange,
    //        maxRange,
    //        highLod,
    //        drawLidarPoints);

    GfMatrix4d worldTransform;
    if (mRigidBodyHandle)
    {
        worldTransform = utils::conversions::asGfMatrix4d(mDynamicControlPtr->getRigidBodyPose(mRigidBodyHandle));
    }
    else
    {
        worldTransform = omni::usd::UsdUtils::getWorldTransformMatrix(prim.GetPrim());
    }
    GfMatrix4d worldTransformInv = worldTransform.GetInverse();

    // GfRotation startingRotation(GfVec3f(1.0f, 0.0f, 0.0f), 180.0f);
    // startingRotation *= worldTransform.ExtractRotation();
    GfRotation worldRotation = worldTransform.RemoveScaleShear().ExtractRotation();

    GfVec3f origin = worldTransform.Transform(GfVec3f(0.0f, 0.0f, 0.0f));


    int i = start * rows;
    int j = start;

    for (int colPreMod = start; colPreMod < stop; colPreMod++)
    {
        for (int row = 0; row < rows; row++)
        {
            int col = colPreMod % cols;

            // Pitch then yaw
            GfRotation pitchYaw(GfVec3f(0.0f, 0.0f, 1.0f), zenith[row] * 180.0f / M_PI);
            pitchYaw *= GfRotation(GfVec3f(0.0f, 1.0f, 0.0f), azimuth[col] * 180.0f / M_PI);


            GfRotation rot = pitchYaw;
            // rot *= startingRotation;
            rot *= worldRotation;

            GfVec3f unitDir = rot.TransformDir(GfVec3f(1.0f, 0.0f, 0.0f));

            carb::Float3 carbOrigin = { origin[0], origin[1], origin[2] };
            carb::Float3 carbUnitDir = { unitDir[0], unitDir[1], unitDir[2] };
            carb::physics::RaycastHit raycastHit;

            bool hit = physx->raycastClosest(carbOrigin, carbUnitDir, maxDepth, raycastHit, true);

            if (hit)
            {
                depth[i] = uint16_t(raycastHit.distance / maxDepth * 65535.0f);
                intensity[i] = 255;

                if (drawLidarPoints)
                {
                    GfVec3f hitPos = worldTransformInv.Transform(
                        GfVec3f(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z));
                    addDebugLine(GfVec3f(0, 0, 0), hitPos, { 0.4f, 1.0f, 1.0f }, col * rows + row);
                }
            }
            else
            {
                depth[i] = 65535;
                intensity[i] = 0;
                if (drawLidarPoints)
                {
                    GfVec3f hitPos = worldTransformInv.TransformDir(unitDir) * maxDepth;
                    addDebugLine(GfVec3f(0, 0, 0), hitPos, { 0.0f, 0.4f, 0.4f }, col * rows + row);
                }
            }

            if (zenith[row] == 0.0f)
                ++j %= cols;
            ++i %= (cols * rows);
        }
    }
}

void Lidar::dumpData(int start, int stop, float dt)
{

    // Size of lastDepth and lastIntensity == rows * lastNumColsTicked
    // Size of depth, and intensity == rows * cols
    // Size of azimuth == cols
    // Size of lastAzimuth == lastNumColsTicked

    int colsToTick = stop - start;

    int unwrappedSize = std::min(stop, cols) - start;
    int wrappedSize = std::max(0, stop - cols);

    lastDepth.resize(rows * colsToTick);
    lastIntensity.resize(rows * colsToTick);
    lastAzimuth.resize(colsToTick);

    std::copy(azimuth.begin() + start, azimuth.begin() + (start + unwrappedSize), lastAzimuth.begin());
    std::copy(depth.begin() + start * rows, depth.begin() + (start + unwrappedSize) * rows, lastDepth.begin());
    std::copy(
        intensity.begin() + start * rows, intensity.begin() + (start + unwrappedSize) * rows, lastIntensity.begin());

    // We wrapped around
    if (wrappedSize > 0)
    {
        std::copy(azimuth.begin(), azimuth.begin() + wrappedSize, lastAzimuth.begin() + unwrappedSize);
        std::copy(depth.begin(), depth.begin() + wrappedSize * rows, lastDepth.begin() + unwrappedSize * rows);
        std::copy(
            intensity.begin(), intensity.begin() + wrappedSize * rows, lastIntensity.begin() + unwrappedSize * rows);
    }
}


void Lidar::addDebugLine(const pxr::GfVec3f& pointA, const pxr::GfVec3f& pointB, const pxr::GfVec3f& color, const int index)
{

    pxr::SdfPath primPath(std::string(this->prim.GetPath().GetString() + std::string("/Line_") + std::to_string(index)));

    UsdGeomCube cube = UsdGeomCube::Define(stage, primPath);
    cube.CreateSizeAttr().Set(1.0);


    GfVec3f dir = pointB - pointA;

    float length = dir.GetLength();

    double phi = std::asin(dir[1] / length) * 180.0 / M_PI;
    double theta = std::atan2(-dir[2], dir[0]) * 180.0 / M_PI;


    GfRotation rot(GfVec3f(0.0f, 0.0f, 1.0f), phi);
    rot *= GfRotation(GfVec3f(0.0f, 1.0f, 0.0f), theta);

    GfVec3f translation = rot.TransformDir(GfVec3f(length * 0.5f, 0.0f, 0.0f));
    translation += pointA;


    cube.ClearXformOpOrder();
    cube.AddTransformOp().Set(GfMatrix4d(rot, translation));
    cube.AddScaleOp().Set(GfVec3f(length, 1.0f, 1.0f));


    cube.CreateDisplayColorAttr().Set(VtArray<GfVec3f>({ color }));

    activeDebugLines.insert(index);
}

void Lidar::clearDebugLines()
{

    // No stage or no lines, nothing to clear
    if (stage == nullptr || activeDebugLines.size() == 0)
        return;

    std::string basePrimPath = std::string(this->prim.GetPath().GetString() + std::string("/Line_"));

    for (const auto& index : activeDebugLines)
    {
        pxr::SdfPath primPath(basePrimPath + std::to_string(index));
        stage->RemovePrim(primPath);
    }

    activeDebugLines.clear();
}


void Lidar::update(float elapsedTime)
{

    if (!valid)
    {
        CARB_LOG_ERROR("Attempted to use an invalid Lidar, please specify all attributes on prim");
        return;
    }

    clearDebugLines();


    // Every tick does a full scan
    if (rotationRate == 0.0f)
    {
        lastNumColsTicked = cols;

        scan(0, cols);
        dumpData(0, cols, elapsedTime);

        lastCol = 0;
    }
    else
    {
        remainingTime += elapsedTime;


        lastNumColsTicked = int(colScanSpeed * remainingTime);

        // If too much time is remaining, cap the number of columns
        if (lastNumColsTicked > maxColsPerTick)
        {
            lastNumColsTicked = maxColsPerTick;
        }

        float simulateTime = lastNumColsTicked / colScanSpeed;
        remainingTime -= simulateTime;


        // In the case where we capped the number of columns, we drop from remainingTime
        // a multiple of maxStepSize
        remainingTime = std::fmod(remainingTime, maxStepSize);

        // Now scan the columns and dump the data
        scan(lastCol, lastCol + lastNumColsTicked);
        dumpData(lastCol, lastCol + lastNumColsTicked, simulateTime);

        lastCol = (lastCol + lastNumColsTicked) % cols;
    }
}


}
}
}
