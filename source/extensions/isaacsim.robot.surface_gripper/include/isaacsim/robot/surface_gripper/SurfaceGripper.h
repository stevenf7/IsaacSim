// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include "isaacsim/core/includes/Math.h"

#include <omni/physics/tensors/BodyTypes.h>
#include <omni/physx/IPhysxSceneQuery.h>

#include <DynamicControl.h>

namespace isaacsim
{
namespace robot
{
namespace surface_gripper
{


using namespace omni::isaac::dynamic_control;
using namespace isaacsim::core::includes::math;
using omni::physics::tensors::Transform;

/**
 * @brief Helper function to convert uint64_t to SdfPath reference
 * @param path Integer representation of path
 * @return Reference to corresponding SdfPath
 */
inline const pxr::SdfPath& intToPath(const uint64_t& path)
{
    static_assert(sizeof(pxr::SdfPath) == sizeof(uint64_t), "Change to make the same size as pxr::SdfPath");

    return reinterpret_cast<const pxr::SdfPath&>(path);
}

/**
 * @brief Configuration properties for surface gripper functionality
 */
struct SurfaceGripperProperties
{
    std::string d6JointPath; ///< USD path of the joint prim
    std::string parentPath; ///< USD path of parent rigid body prim
    Transform offset; ///< Local transform from parent to grip point

    float gripThreshold; ///< Maximum grip distance in meters
    float forceLimit; ///< Breaking force limit in Newtons
    float torqueLimit; ///< Breaking torque limit in Newton-meters
    float bendAngle; ///< Maximum bend angle in radians
    float stiffness; ///< Joint stiffness in N/m
    float damping; ///< Joint damping in N·s/m

    bool disableGravity; ///< Disable gravity on gripped object to compensate for object's mass on robotic controllers
    bool retryClose; ///< Flag to indicate if gripper should keep attempting to close until it grips some object
};

/**
 * @brief Manages surface gripper (suction-cup style gripper)
 */
class SurfaceGripper
{
public:
    /**
     * @brief Default constructor
     */
    SurfaceGripper();

    /**
     * @brief Destructor
     */
    ~SurfaceGripper();

    /**
     * @brief Initializes the surface gripper with the provided properties
     * @param[in] props Configuration properties for the gripper
     * @return True if initialization was successful, false otherwise
     */
    bool initialize(const SurfaceGripperProperties& props);

    /**
     * @brief Checks if the gripper is currently closed
     * @return True if the gripper is closed, false otherwise
     */
    bool isClosed() const;

    /**
     * @brief Checks if the gripper is currently attempting to close
     * @return True if the gripper is attempting to close, false otherwise
     */
    bool isAttemptingClose() const;

    /**
     * @brief Updates the gripper state
     * @details Should be called every simulation step to update the gripper's internal state
     */
    void update();

    /**
     * @brief Closes the gripper
     * @details Attempts to grip an object within the grip threshold distance
     * @return True if the close operation was initiated successfully, false otherwise
     */
    bool close();

    /**
     * @brief Opens the gripper
     * @details Releases any currently gripped object
     * @return True if the open operation was successful, false otherwise
     */
    bool open();

private:
    /**
     * @brief Attempts to close the gripper with an additional offset
     * @param[in] additionalOffset Additional distance offset for the grip attempt
     * @return True if the gripper successfully gripped an object, false otherwise
     */
    bool attemptClose(float additionalOffset = 0.0f);

    DynamicControl* m_dc = nullptr;
    omni::physx::IPhysxSceneQuery* m_physxQuery = nullptr;
    DcHandle m_jointHandle = kDcInvalidHandle;
    DcD6JointProperties m_jointProperties;
    SurfaceGripperProperties m_props;
    bool m_closed;
    bool m_initialized;
    bool m_attemptingClose;
};

} // namespace surface_gripper
} // namespace robot
} // namespace isaacsim
