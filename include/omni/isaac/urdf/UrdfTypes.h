// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <float.h>
#include <iostream>
#include <map>
#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace urdf
{

// The default values and data structures are mostly the same as defined in the official URDF documentation
// http://wiki.ros.org/urdf/XML

struct UrdfOrigin
{
    // Position
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    // Orientation
    float roll = 0.0f;
    float pitch = 0.0f;
    float yaw = 0.0f;
};

struct UrdfInertia
{
    float ixx = 0.0f;
    float ixy = 0.0f;
    float ixz = 0.0f;
    float iyy = 0.0f;
    float iyz = 0.0f;
    float izz = 0.0f;
};

struct UrdfInertial
{
    UrdfOrigin origin; // This is the pose of the inertial reference frame, relative to the link reference frame. The
                       // origin of the inertial reference frame needs to be at the center of gravity
    float mass = 0.0f;
    UrdfInertia inertia;
    bool hasOrigin = false;
    bool hasMass = false; // Whether the inertial field defined a mass
    bool hasInertia = false; // Whether the inertial field defined an inertia
};

struct UrdfAxis
{
    float x = 1.0f;
    float y = 0.0f;
    float z = 0.0f;
};

// By Default a UrdfColor struct will have an invalid color unless it was found in the xml
struct UrdfColor
{
    float r = -1.0f;
    float g = -1.0f;
    float b = -1.0f;
    float a = 1.0f;
};

enum class UrdfJointType
{
    REVOLUTE = 0, // A hinge joint that rotates along the axis and has a limited range specified by the upper and lower
                  // limits
    CONTINUOUS = 1, // A continuous hinge joint that rotates around the axis and has no upper and lower limits
    PRISMATIC = 2, // A sliding joint that slides along the axis, and has a limited range specified by the upper and
                   // lower limits
    FIXED = 3, // this is not really a joint because it cannot move. All degrees of freedom are locked. This type of
               // joint does not require the axis, calibration, dynamics, limits or safety_controller
    FLOATING = 4, // This joint allows motion for all 6 degrees of freedom
    PLANAR = 5 // This joint allows motion in a plane perpendicular to the axis
};

enum class UrdfJointTargetType
{
    NONE = 0,
    POSITION = 1,
    VELOCITY = 2
};

enum class UrdfJointDriveType
{
    ACCELERATION = 0,
    FORCE = 2
};

struct UrdfDynamics
{
    float damping = 0.0f;
    float friction = 0.0f;
    float stiffness = 0.0f;
};

struct UrdfJointDrive
{
    float target = 0.0;
    UrdfJointTargetType targetType = UrdfJointTargetType::POSITION;
    UrdfJointDriveType driveType = UrdfJointDriveType::ACCELERATION;
};

struct UrdfLimit
{
    float lower = -FLT_MAX; // An attribute specifying the lower joint limit (radians for revolute joints, meters for
                            // prismatic joints)
    float upper = FLT_MAX; // An attribute specifying the upper joint limit (radians for revolute joints, meters for
                           // prismatic joints)
    float effort = FLT_MAX; // An attribute for enforcing the maximum joint effort
    float velocity = FLT_MAX; // An attribute for enforcing the maximum joint velocity
};

enum class UrdfGeometryType
{
    BOX = 0,
    CYLINDER = 1,
    SPHERE = 2,
    MESH = 3
};

struct UrdfGeometry
{
    UrdfGeometryType type;
    // Box
    float size_x = 0.0f;
    float size_y = 0.0f;
    float size_z = 0.0f;
    // Cylinder and Sphere
    float radius = 0.0f;
    float length = 0.0f;
    // Mesh
    float scale_x = 1.0f;
    float scale_y = 1.0f;
    float scale_z = 1.0f;
    std::string meshFilePath;
};

struct UrdfMaterial
{
    std::string name;
    UrdfColor color;
    std::string textureFilePath;
};

struct UrdfVisual
{
    std::string name;
    UrdfOrigin origin; // The reference frame of the visual element with respect to the reference frame of the link
    UrdfGeometry geometry;
    UrdfMaterial material;
};

struct UrdfCollision
{
    std::string name;
    UrdfOrigin origin; // The reference frame of the collision element, relative to the reference frame of the link
    UrdfGeometry geometry;
};

struct UrdfLink
{
    std::string name;
    UrdfInertial inertial;
    std::vector<UrdfVisual> visuals;
    std::vector<UrdfCollision> collisions;
};

struct UrdfJoint
{
    std::string name;
    UrdfJointType type;
    UrdfOrigin origin; // This is the transform from the parent link to the child link. The joint is located at the
                       // origin of the child link
    std::string parentLinkName;
    std::string childLinkName;
    UrdfAxis axis;
    UrdfDynamics dynamics;
    UrdfLimit limit;
    UrdfJointDrive drive;
};

struct UrdfRobot
{
    std::string name;
    std::map<std::string, UrdfLink> links;
    std::map<std::string, UrdfJoint> joints;
    std::map<std::string, UrdfMaterial> materials;
};


} // namespace urdf
}
}
