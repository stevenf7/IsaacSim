// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/RangeSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <isaacsim/core/includes/Color.h>
#include <isaacsim/sensors/physx/IPhysxSensorInterface.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/lidar.h>

#include <vector>

namespace isaacsim
{
namespace sensors
{
namespace physx
{

/**
 * @class LidarSensor
 * @brief A LiDAR (Light Detection and Ranging) sensor implementation
 * @details This class simulates a LiDAR sensor with configurable parameters such as
 *          rotation rate, field of view, and resolution. It provides both depth and
 *          intensity data, along with optional semantic information about detected objects.
 *          The sensor performs ray casting in the physics scene to detect objects and
 *          measure distances.
 */
class LidarSensor : public RangeSensorComponent
{

public:
    /**
     * @brief Constructs a new LiDAR sensor instance
     * @param[in] physxPtr Pointer to the PhysX interface for physics simulation
     * @param[in] syntheticDataPtr Pointer to the synthetic data interface for semantic information
     */
    LidarSensor(omni::physx::IPhysx* physxPtr, omni::syntheticdata::SyntheticData* syntheticDataPtr);

    /**
     * @brief Virtual destructor for proper cleanup
     */
    ~LidarSensor();

    /**
     * @brief Initializes the LiDAR sensor when the component starts
     * @details Sets up initial parameters, allocates memory for scan data, and prepares the sensor for operation
     */
    virtual void onStart();

    /**
     * @brief Performs pre-tick operations before the main sensor update
     * @details Updates sensor parameters and prepares for the next scan cycle
     */
    virtual void preTick();

    /**
     * @brief Performs the main sensor update during each tick
     * @details Executes the LiDAR scanning operation, updates sensor data, and processes results
     */
    virtual void tick();

    /**
     * @brief Handles component property changes
     * @details Updates sensor configuration when properties are modified through the interface
     */
    virtual void onComponentChange();

    /**
     * @brief Gets the number of columns (horizontal samples) in the scan pattern
     * @return Number of columns in the scan grid
     */
    int getNumCols() const
    {
        return mCols;
    }

    /**
     * @brief Gets the number of rows (vertical samples) in the scan pattern
     * @return Number of rows in the scan grid
     */
    int getNumRows() const
    {
        return mRows;
    }

    /**
     * @brief Gets the number of columns processed in the last tick
     * @return Number of columns processed in the most recent update
     */
    int getNumColsTicked() const
    {
        return mLastNumColsTicked;
    }

    /**
     * @brief Gets the latest depth data from the sensor
     * @return Reference to vector containing normalized depth values (0-65535)
     */
    std::vector<uint16_t>& getDepthData()
    {
        return mLastDepth;
    }

    /**
     * @brief Gets the timestamp for each beam in the scan
     * @return Reference to vector containing beam timestamps in seconds
     */
    std::vector<float>& getBeamTimeData()
    {
        return mLastBeamTime;
    }

    /**
     * @brief Gets the latest linear depth data in meters
     * @return Reference to vector containing depth values in meters
     */
    std::vector<float>& getLinearDepthData()
    {
        return mLastLinearDepth;
    }

    /**
     * @brief Gets the latest intensity data from the sensor
     * @return Reference to vector containing intensity values (0-255)
     */
    std::vector<uint8_t>& getIntensityData()
    {
        return mLastIntensity;
    }

    /**
     * @brief Gets the zenith angles for each sensor ray
     * @return Reference to vector containing zenith angles in radians
     */
    std::vector<float>& getZenithData()
    {
        return mZenith;
    }

    /**
     * @brief Gets the azimuth angles for each sensor ray
     * @return Reference to vector containing azimuth angles in radians
     */
    std::vector<float>& getAzimuthData()
    {
        return mLastAzimuth;
    }

    /**
     * @brief Gets the primitive data for each hit point
     * @return Reference to vector containing primitive names/identifiers
     */
    std::vector<std::string>& getPrimData()
    {
        return mLastPrimData;
    }

    /**
     * @brief Gets the azimuth angle range of the sensor
     * @return Pair of minimum and maximum azimuth angles in radians
     */
    carb::Float2 getAzimuthRange()
    {
        return mAzimuthRange;
    }

    /**
     * @brief Gets the zenith angle range of the sensor
     * @return Pair of minimum and maximum zenith angles in radians
     */
    carb::Float2 getZenithRange()
    {
        return mZenithRange;
    }

private:
    /**
     * @brief Dumps sensor data for debugging purposes
     * @param[in] start Starting index in the scan pattern
     * @param[in] stop Ending index in the scan pattern
     * @param[in] elapsedTime Time elapsed during the scan in seconds
     */
    void dumpData(int start, int stop, double elapsedTime);

    /**
     * @brief Performs the LiDAR scanning operation
     * @tparam drawPoints Enable/disable point visualization
     * @tparam drawLines Enable/disable line visualization
     * @tparam enableSemantics Enable/disable semantic data collection
     * @param[in] start Starting column index for the scan
     * @param[in] stop Ending column index for the scan
     * @param[in] rows Number of vertical samples
     * @param[in] cols Number of horizontal samples
     * @param[in] origin Origin point of the sensor in world space
     * @param[in] worldRotation Rotation of the sensor in world space
     * @param[in] zUp Whether the world coordinate system is Z-up
     * @details Performs ray casting for each point in the scan pattern and processes hit results
     */
    template <bool drawPoints, bool drawLines, bool enableSemantics>
    void scan(int start,
              int stop,
              int rows,
              int cols,
              const ::physx::PxVec3& origin,
              const ::physx::PxQuat& worldRotation,
              bool zUp)
    {
        if (!mPxScene)
        {
            return;
        }
        float invMaxDepth = 1.0f / mMaxDepth;
        // This isn't correct because the same prim (like carter) would have a different lidar axis if it was in a Y up
        // vs Z up stage. So commented this out and using the pure Z up rotation version
        // ::physx::PxVec3 azimuthDir = zUp ? ::physx::PxVec3(0.0f, 0.0f, 1.0f) : ::physx::PxVec3(0.0f, 1.0f, 0.0f);
        // ::physx::PxVec3 zenithDir = zUp ? ::physx::PxVec3(0.0f, 1.0f, 0.0f) : ::physx::PxVec3(0.0f, 0.0f, 1.0f);

        ::physx::PxVec3 azimuthDir = ::physx::PxVec3(0.0f, 0.0f, 1.0f);
        ::physx::PxVec3 zenithDir = ::physx::PxVec3(0.0f, 1.0f, 0.0f);

        auto lidarLambda = [&](int colPreMod)
        {
            int col = colPreMod % cols;
            ::physx::PxQuat mainrot = worldRotation * ::physx::PxQuat(mAzimuth[col], azimuthDir);

            for (int row = 0; row < rows; row++)
            {
                int i = row + colPreMod * rows % (rows * cols);

                // Time will be the same for all beams in this bucket - note beams are not interpolated over frame.
                mBeamTime[i] = static_cast<float>(mTimeSeconds);
                // Pitch then yaw
                ::physx::PxQuat rot = mainrot * ::physx::PxQuat(mZenith[row], zenithDir);
                ::physx::PxVec3 unitDir = rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized();
                ::physx::PxRaycastHit raycastHit;
                // Project the start point out to prevent collisions from origin

                const bool hit = ::physx::PxSceneQueryExt::raycastSingle(
                    *mPxScene, origin + unitDir * mMinDepth, unitDir, mMaxDepth, mHitFlags, raycastHit);

                if (hit)
                {
                    // the distance of the ray should be from center of lidar
                    mDepth[i] = static_cast<uint16_t>((raycastHit.distance + mMinDepth) * invMaxDepth * 65535.0f);
                    mLinearDepth[i] = (raycastHit.distance + mMinDepth) * mMetersPerUnit; // in meters
                    mIntensity[i] = 255;

                    carb::Float3 hitPos = { raycastHit.position.x, raycastHit.position.y, raycastHit.position.z };
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(raycastHit.position - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z }; // relative to the sensor location
                    if (enableSemantics)
                    {
                        const char* hitActorName = raycastHit.actor->getName();
                        mPrimData[i] = hitActorName;
                    }
                    if (drawPoints)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        // ::physx::PxVec3 diff = raycastHit.position - origin;

                        // auto temp = raycastHit.position - diff.getNormalized();
                        // set ratio for color.  should be zero at mMinDepth and unity at mMaxDepth
                        auto ratio =
                            (mLinearDepth[i] - mMinDepth * mMetersPerUnit) / ((mMaxDepth - mMinDepth) * mMetersPerUnit);

                        data.position = hitPos;
                        data.color = isaacsim::core::includes::color::distToRgba(ratio);
                        data.width = 5.0;

                        mPointDrawing->addVertex(data);
                        // data.position = { temp.x, temp.y, temp.z };
                        // mPointDrawing->addVertex(data);
                    }

                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        ::physx::PxVec3 diff = raycastHit.position - origin;
                        auto temp = origin + diff.getNormalized() * mMinDepth;
                        // set ratio for color.  should be zero at mMinDepth and unity at mMaxDepth
                        auto ratio =
                            (mLinearDepth[i] - mMinDepth * mMetersPerUnit) / ((mMaxDepth - mMinDepth) * mMetersPerUnit);

                        data.position = { temp.x, temp.y, temp.z };
                        data.color = isaacsim::core::includes::color::distToRgba(ratio);
                        data.width = 1.0;

                        mLineDrawing->addVertex(data);
                        data.position = hitPos;
                        mLineDrawing->addVertex(data);
                    }
                }
                else
                {
                    mDepth[i] = 65535;
                    mLinearDepth[i] = mMaxDepth * mMetersPerUnit; // in meters
                    mIntensity[i] = 0;
                    ::physx::PxVec3 hitPos = origin + unitDir * (mMaxDepth + mMinDepth);
                    ::physx::PxVec3 hitPosRel = worldRotation.rotateInv(hitPos - origin);
                    mHitPos[i] = { hitPosRel.x, hitPosRel.y, hitPosRel.z };
                    if (drawLines)
                    {
                        carb::scenerenderer::PrimitiveVertex data;

                        auto temp = origin + unitDir * mMinDepth;

                        data.position = { temp.x, temp.y, temp.z };
                        data.color = { 1, 1, 1, 50.0f / 255.0f };
                        data.width = 1.0;

                        mLineDrawing->addVertex(data);
                        data.position = { hitPos.x, hitPos.y, hitPos.z };
                        mLineDrawing->addVertex(data);
                    }
                }
            }
        };
        if (drawLines || drawPoints || enableSemantics)
        {
            for (int colPreMod = start; colPreMod < stop; colPreMod++)
            {
                lidarLambda(colPreMod);
            }
        }
        else
        {
            mTasking->parallelFor(start, stop, lidarLambda);
        }
    }

    // From the prim
    float mRotationRate = 20.0f;

    /**
     * @brief High level of detail flag for sensor operation
     */
    bool mHighLod = true;

    /**
     * @brief Horizontal field of view in degrees
     */
    float mHorizontalFov = 360.0f;

    /**
     * @brief Vertical field of view in degrees
     */
    float mVerticalFov = 30.0f;

    /**
     * @brief Horizontal angular resolution in degrees
     */
    float mHorizontalResolution = 0.4f;

    /**
     * @brief Vertical angular resolution in degrees
     */
    float mVerticalResolution = 4.0f;

    /**
     * @brief Yaw offset angle in degrees
     */
    float mYawOffset = 0.0f;

    /**
     * @brief Minimum depth range in world units
     */
    float mMinDepth = 0;

    /**
     * @brief Maximum depth range in world units
     */
    float mMaxDepth = 1e8;

    /**
     * @brief Maximum step size for scanning
     */
    float mMaxStepSize = 0;

    /**
     * @brief Maximum number of columns to process per tick
     */
    int mMaxColsPerTick = 0;

    /**
     * @brief Last processed column index
     */
    int mLastCol = 0;

    /**
     * @brief Scanning speed in columns per second
     */
    float mColScanSpeed = 0;

    /**
     * @brief Remaining time for the current scan cycle
     */
    double mRemainingTime = 0;

    /**
     * @brief Number of vertical samples (rows)
     */
    int mRows = 0;

    /**
     * @brief Number of horizontal samples (columns)
     */
    int mCols = 0;

    /**
     * @brief Number of columns processed in the last tick
     */
    int mLastNumColsTicked = 0;

    /**
     * @brief Vector of zenith angles for each row
     */
    std::vector<float> mZenith;

    /**
     * @brief Current and last azimuth angles for each column
     */
    std::vector<float> mAzimuth, mLastAzimuth;

    /**
     * @brief Range of azimuth angles (min, max) in radians
     */
    carb::Float2 mAzimuthRange;

    /**
     * @brief Range of zenith angles (min, max) in radians
     */
    carb::Float2 mZenithRange;

    /**
     * @brief Current and last beam timestamps
     */
    std::vector<float> mBeamTime, mLastBeamTime;

    /**
     * @brief Current and last linear depth measurements in meters
     */
    std::vector<float> mLinearDepth, mLastLinearDepth;

    /**
     * @brief Current and last intensity measurements
     */
    std::vector<uint8_t> mIntensity, mLastIntensity;

    /**
     * @brief Current and last normalized depth measurements
     */
    std::vector<uint16_t> mDepth, mLastDepth;

    /**
     * @brief Hit positions in sensor local space
     */
    std::vector<carb::Float3> mHitPos;

    /**
     * @brief PhysX ray cast hit flags configuration
     */
    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;

    /**
     * @brief Final translation of the sensor in world space
     */
    ::physx::PxVec3 mFinalTranslation;

    /**
     * @brief Final rotation of the sensor in world space
     */
    ::physx::PxQuat mFinalRotation;

    /**
     * @brief Pointer to synthetic data interface for semantic information
     */
    omni::syntheticdata::SyntheticData* mSyntheticDataPtr = nullptr;

    /**
     * @brief Flag to enable/disable semantic data collection
     */
    bool mEnableSemantics;

    /**
     * @brief Current and last primitive data for semantic information
     */
    std::vector<std::string> mPrimData, mLastPrimData;
};


}
}
}
