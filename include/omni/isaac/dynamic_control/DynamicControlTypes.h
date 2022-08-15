// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <limits>

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
using DcHandle = uint64_t;

constexpr DcHandle kDcInvalidHandle = DcHandle(0);

enum DcObjectType : uint32_t
{
    eDcObjectNone,
    eDcObjectRigidBody,
    eDcObjectJoint,
    eDcObjectDof,
    eDcObjectArticulation,
    eDcObjectAttractor,
    eDcObjectD6Joint,

    kDcObjectTypeCount
};

/// Transform
/**
 * Represents a pose (e.g. of a rigid body)
 */
struct DcTransform
{
    carb::Float3 p{ 0.0f, 0.0f, 0.0f }; //!< Position, in meters
    carb::Float4 r{ 0.0f, 0.0f, 0.0f, 1.0f }; //!< Rotation Quaternion, represented in the format $x\hat{i} + y\hat{j} +
                                              //!< z\hat{k} + w$
};

/// Velocity
/**
 * Holds linear and angular velocities, in $m/s$ and $radians/s$
 */
struct DcVelocity
{
    carb::Float3 linear{ 0.0f, 0.0f, 0.0f }; //!< Linear velocity component
    carb::Float3 angular{ 0.0f, 0.0f, 0.0f }; //!< angular velocity component
};

// useful constants

constexpr carb::Float3 kFloat3Zero = { 0.0f, 0.0f, 0.0f };

constexpr carb::Float4 kQuatIdentity = { 0.0f, 0.0f, 0.0f, 1.0f };
constexpr carb::Float4 kQuatZero = { 0.0f, 0.0f, 0.0f, 0.0f };

constexpr DcTransform kTransformIdentity = { kFloat3Zero, kQuatIdentity };
constexpr DcTransform kTransformZero = { kFloat3Zero, kQuatIdentity };

constexpr DcVelocity kVelocityZero{ kFloat3Zero, kFloat3Zero };

/** @defgroup DcStateFlags
 * States that can be get/set from Degrees of Freedom and Rigid Bodies
 * @{
 */
using DcStateFlags = int;
constexpr DcStateFlags kDcStateNone = 0; //!< No state selected
constexpr DcStateFlags kDcStatePos = 1 << 0; //!< Position states
constexpr DcStateFlags kDcStateVel = 1 << 1; //!< Velocity states
constexpr DcStateFlags kDcStateEffort = 1 << 2; //!< Forces/Torques states
constexpr DcStateFlags kDcStateAll = (kDcStatePos | kDcStateVel | kDcStateEffort); //!< All states
/** @} */ // end of DcStateFlags group

/// Drive modes for degrees-of-freedom.
/**
 * A DoF that is set on a specific drive mode will ignore drive target
 * commands sent for a different mode.
 * Joint limits, if they exist, will still be enforced.
 */
enum class DcDriveMode : int32_t
{
    eForce, //!< The output of the implicit spring drive controller is a force/torque.
    eAcceleration, //!< The output of the implicit spring drive controller is a joint acceleration (use this to get
                   //!< (spatial)-inertia-invariant behavior of the drive).
};

/**
 * @brief Result of a Raycast
 *
 */
struct DcRayCastResult
{
    bool hit; //!< an object was hit
    DcHandle rigidBody; //!< which object was hit
    float distance; //!< distance to object surface from raycast source
};

/**
 * State of a rigid body
 */
struct DcRigidBodyState
{
    DcTransform pose; //!< Transform with position and orientation of rigid body
    DcVelocity vel; //!< Set of angular and linear velocities of rigid body
};

/**
 * State of a degree of freedom
 */
struct DcDofState
{
    float pos; //!< DOF position, in radians if it's a revolute DOF, or meters, if it's a prismatic DOF
    float vel; //!< DOF velocity, in radians/s if it's a revolute DOF, or m/s, if it's a prismatic DOF
    float effort; //!< DOF effort, torque if it's a revolute DOF, or force if it's a prismatic DOF
};

/// Types of joint
/**
 */
enum class DcJointType : int32_t
{
    eNone, //!< invalid/unknown/uninitialized joint type
    eFixed,
    eRevolute,
    ePrismatic,
    eSpherical,
};

/// Types of degree of freedom
/**
 */
enum class DcDofType : int32_t
{
    eNone, //!< invalid/unknown/uninitialized DOF type
    eRotation, //!< The degrees of freedom correspond to a rotation between bodies
    eTranslation, //!< The degrees of freedom correspond to a translation between bodies.
};

struct DcArticulationProperties
{

    // float stabilizationThreshold = 10.0;
    // float sleepThreshold = 50.0;
    uint32_t solverPositionIterationCount = 32;
    uint32_t solverVelocityIterationCount = 1;
    bool enableSelfCollisions = false;
};

struct DcRigidBodyProperties
{
    float mass;
    carb::Float3 moment;
    carb::Float3 cMassLocalPose;
    float maxDepenetrationVelocity = std::numeric_limits<float>::max();
    float maxContactImpulse = std::numeric_limits<float>::max();
    uint32_t solverPositionIterationCount = 16;
    uint32_t solverVelocityIterationCount = 1;
    // float stabilizationThreshold = 10.0;
    // bool enableSpeculativeCCD = false;
    // bool enableGyroscopicForces = true;
    // bool retainAccelerations = false;
};
/**
 * Properties of a degree-of-freedom
 */
struct DcDofProperties
{
    DcDofType type = DcDofType::eNone; //!< Type of dof (read-only property)

    bool hasLimits = false; //!< Flags whether the DOF has limits. (read-only property)
    float lower = 0.0f; //!< lower limit of DOF. In radians or meters (read-only property)
    float upper = 0.0f; //!< upper limit of DOF. In radians or meters (read-only property)

    DcDriveMode driveMode = DcDriveMode::eAcceleration; //!< Drive mode for the DOF. See DcDriveMode.
    float maxVelocity = std::numeric_limits<float>::max(); //!< Maximum velocity of DOF. In Radians/s, or m/s
    float maxEffort = std::numeric_limits<float>::max(); //!< Maximum effort of DOF. in N or Nm.
    float stiffness = 0.0f; //!< Stiffness of DOF.
    float damping = 0.0f; //!< Damping of DOF.
};

/** @defgroup DcAxisFlags transform axis flags
 * Flags for Axes used in Attractor setup
 * @{
 */
using DcAxisFlags = int;
constexpr DcAxisFlags kDcAxisNone = 0; //!< No axis selected
constexpr DcAxisFlags kDcAxisX = (1 << 0); //!< Corresponds to translation around the body x-axis
constexpr DcAxisFlags kDcAxisY = (1 << 1); //!< Corresponds to translation around the body y-axis
constexpr DcAxisFlags kDcAxisZ = (1 << 2); //!< Corresponds to translation around the body z-axis
constexpr DcAxisFlags kDcAxisTwist = (1 << 3); //!< Corresponds to rotation around the body x-axis
constexpr DcAxisFlags kDcAxisSwing1 = (1 << 4); //!< Corresponds to rotation around the body y-axis
constexpr DcAxisFlags kDcAxisSwing2 = (1 << 5); //!< Corresponds to rotation around the body z-axis
constexpr DcAxisFlags kDcAxisAllTranslation = kDcAxisX | kDcAxisY | kDcAxisZ; //!< Corresponds to all Translation axes
constexpr DcAxisFlags kDcAxisAllRotation = kDcAxisTwist | kDcAxisSwing1 | kDcAxisSwing2; //!< Corresponds to all
                                                                                         //!< Rotation axes
constexpr DcAxisFlags kDcAxisAll = kDcAxisAllTranslation | kDcAxisAllRotation; //!< Corresponds to all axes
/** @} */ // end of group DcAxisFlags

/// Properties to set up a pose attractor
/**
 * The Attractor is used to pull a rigid body towards a pose. Each pose axis can be individually selected. *
 */
struct DcAttractorProperties
{
    DcHandle rigidBody = kDcInvalidHandle; //!< Rigid body to set the attractor to
    DcAxisFlags axes = 0; //!< Axes to set the attractor, using DcTransformAxesFlags. Multiple axes can be selected
                          //!< using bitwise combination of each axis flag. if axis flag is set to zero, the attractor
                          //!< will be disabled and won't impact in solver computational complexity.
    DcTransform target{ kTransformIdentity }; //!< Target pose to attract to.
    DcTransform offset{ kTransformIdentity }; //!< Offset from rigid body origin to set the attractor pose.
    float stiffness = 1e5f; //!< Stiffness to be used on attraction for solver. Stiffness value should be larger than
                            //!< the largest agent kinematic chain stifness
    float damping = 1e3f; //!< Damping to be used on attraction solver.
    float forceLimit = std::numeric_limits<float>::max(); //!< Maximum force to be applied by drive
};

/// Properties to set up a D6 Joint
/**
 * The Joint is used to connect two rigid bodies.
 */
struct DcD6JointProperties
{
    char* name{ nullptr };
    DcHandle body0 = kDcInvalidHandle; //!< Rigid body to set the joint to
    DcHandle body1 = kDcInvalidHandle; //!< Rigid body to set the joint to
    DcAxisFlags axes = kDcAxisNone; //!< Joint Axes, using DcTransformAxesFlags. Multiple axes can be selected
                                    //!< using bitwise combination of each axis flag. if axis flag is set to zero, the
                                    //!< joint will be disabled and won't impact in solver computational complexity.
    DcTransform pose0{ kTransformIdentity }; //!< Offset from Rigid Body 0 to Joint.
    DcTransform pose1{ kTransformIdentity }; //!< Offset from Rigid Body 1 to Joint.
    DcJointType jointType; //!< Joint type being defined
    bool hasLimits[6]; //!< Flag for determining if joint has limits or is locked
    bool softLimit{ true }; ///!< whether joint limits are progressively harder
    float lowerLimit; //!< lower joint limit, same for all axes
    float upperLimit; //!< upper joint limit, same for all axes
    float limitStiffness{ 1e5f }; //!< Joint Stiffness
    float limitDamping = { 1e3f }; //!< Joint Damping
    float stiffness = { 1e5f }; //!< Joint Stiffness
    float damping = { 1e3f }; //!< Joint Damping
    float forceLimit = std::numeric_limits<float>::max(); //!< Joint Breaking Force
    float torqueLimit = std::numeric_limits<float>::max(); //!< Joint Breaking torque
};

/////////////////////////////

constexpr int kMaxDims = 8;

struct DcShape
{
    int ndims = 0;
    int dims[kMaxDims] = { 0 };
};

enum class DcDtype
{
    kVoid,
    kFloat32,
};

struct DcTensor;

struct DcActuator;
struct DcActuatorGroup;

}
}
}
