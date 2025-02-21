// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "isaacsim/core/utils/Math.h"

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
using namespace isaacsim::core::utils::math;
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
    SurfaceGripper();
    ~SurfaceGripper();

    bool initialize(const SurfaceGripperProperties& props);
    bool isClosed() const;
    bool isAttemptingClose() const;
    void update();
    bool close();
    bool open();

private:
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
