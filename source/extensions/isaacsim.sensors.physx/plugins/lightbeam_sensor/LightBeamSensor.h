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
#include <isaacSensorSchema/isaacLightBeamSensor.h>
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <RangeSensorInterface.h>
#include <vector>

namespace isaacsim
{
namespace sensors
{
namespace physx
{
/**
 * @class LightBeamSensor
 * @brief A sensor that simulates a curtain of light beams for range detection
 * @details This sensor projects multiple light beams in a curtain pattern to detect
 *          objects and measure distances. It is useful for applications like safety
 *          curtains, area monitoring, and object detection along a plane.
 *          The sensor uses PhysX ray casting to detect intersections with objects
 *          and provides hit status, depth measurements, and hit positions for each beam.
 */
class LightBeamSensor : public RangeSensorComponent
{

public:
    /**
     * @brief Constructs a new Light Beam Sensor instance
     * @param[in] PhysXInterface Pointer to the PhysX interface for physics simulation
     */
    LightBeamSensor(omni::physx::IPhysx* PhysXInterface);

    /**
     * @brief Virtual destructor for proper cleanup
     */
    virtual ~LightBeamSensor() = default;

    /**
     * @brief Initializes the light beam sensor when the component starts
     * @details Sets up initial parameters, allocates memory for beam data, and prepares the sensor for operation
     */
    virtual void onStart();

    /**
     * @brief Performs pre-tick operations before the main sensor update
     * @details Empty implementation as no pre-tick operations are needed
     */
    virtual void preTick(){};

    /**
     * @brief Performs the main sensor update during each tick
     * @details Empty implementation as updates are handled in onPhysicsStep
     */
    virtual void tick(){};

    /**
     * @brief Cleans up resources when the component stops
     * @details Empty implementation as no specific cleanup is needed
     */
    virtual void onStop(){};

    /**
     * @brief Updates sensor data during physics simulation steps
     * @details Performs ray casting and updates beam hit data based on the current physics state
     */
    virtual void onPhysicsStep();

    /**
     * @brief Handles component property changes
     * @details Updates sensor configuration when properties are modified through the interface
     */
    void onComponentChange();

    /**
     * @brief Gets the number of rays in the light curtain
     * @return Number of individual light beams
     */
    int getNumRays() const
    {
        return mNumRays;
    }

    /**
     * @brief Gets the hit status for each beam
     * @return Reference to vector containing hit flags (0 for no hit, 1 for hit)
     */
    std::vector<uint8_t>& getBeamHitData()
    {
        return mBeamHit;
    }

    /**
     * @brief Gets the linear depth measurements for each beam
     * @return Reference to vector containing depth values in meters
     */
    std::vector<float>& getLinearDepthData()
    {
        return mLinearDepth;
    }

    /**
     * @brief Gets the hit positions for each beam
     * @return Reference to vector containing 3D hit positions
     */
    std::vector<carb::Float3>& getHitPosData()
    {
        return mHitPos;
    }

    /**
     * @brief Gets the current transform of the sensor
     * @param[out] matrixOutput Output matrix containing the sensor's position and orientation
     */
    void getTransformData(omni::math::linalg::matrix4d& matrixOutput)
    {
        // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
        omni::math::linalg::vec3d pos{ mWorldTranslation.x, mWorldTranslation.y, mWorldTranslation.z };
        omni::math::linalg::quatd rot{ mWorldRotation.w, mWorldRotation.x, mWorldRotation.y, mWorldRotation.z };
        matrixOutput.SetIdentity();
        matrixOutput.SetRotateOnly(rot);
        matrixOutput.SetTranslateOnly(pos);
    }

    /**
     * @brief Gets the origin points of all beams
     * @return Reference to vector containing 3D beam origin positions
     */
    std::vector<carb::Float3>& getBeamOrigins()
    {
        return mBeamOrigins;
    }

    /**
     * @brief Gets the end points of all beams
     * @return Reference to vector containing 3D beam end positions
     */
    std::vector<carb::Float3>& getBeamEndPoints()
    {
        return mBeamEndPoints;
    }

private:
    /**
     * @brief Performs a scan with the light curtain
     * @param[in] origin Origin point of the sensor in world space
     * @param[in] worldRotation Rotation of the sensor in world space
     * @details Projects all light beams from their origins and updates hit data,
     *          depths, and positions based on detected intersections
     */
    void scan(const ::physx::PxVec3& origin, const ::physx::PxQuat& worldRotation);

    /**
     * @brief Length of the light curtain in world units
     */
    float mCurtainLength = 0.0f;

    /**
     * @brief Number of individual light beams in the curtain
     */
    int mNumRays = 1;

    /**
     * @brief Forward direction axis of the sensor
     */
    pxr::GfVec3f mForwardAxis;

    /**
     * @brief Axis along which the light curtain is projected
     */
    pxr::GfVec3f mCurtainAxis;

    /**
     * @brief Current world position of the sensor
     */
    ::physx::PxVec3 mWorldTranslation;

    /**
     * @brief Current world rotation of the sensor
     */
    ::physx::PxQuat mWorldRotation;

    /**
     * @brief Previous enabled state of the sensor
     */
    bool mPreviousEnabled = true;

    /**
     * @brief Hit status for each beam (0 for no hit, 1 for hit)
     * @note Using uint8_t instead of bool because C++ doesn't support bool* pointer
     */
    std::vector<uint8_t> mBeamHit;

    /**
     * @brief Origin positions of all beams in world space
     */
    std::vector<carb::Float3> mBeamOrigins;

    /**
     * @brief End positions of all beams in world space
     */
    std::vector<carb::Float3> mBeamEndPoints;

    /**
     * @brief Minimum depth range for ray casting in world units
     */
    float mMinDepth = 0.0f;

    /**
     * @brief Maximum depth range for ray casting in world units
     */
    float mMaxDepth = 1e8;

    /**
     * @brief Linear depth measurements for each beam in meters
     */
    std::vector<float> mLinearDepth;

    /**
     * @brief Hit positions for each beam in world space
     */
    std::vector<carb::Float3> mHitPos;

    /**
     * @brief PhysX ray cast hit flags configuration
     */
    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
};


} // sensor
} // isaac
} // omni
