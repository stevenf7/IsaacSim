// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "UrdfTypes.h"

#include <carb/Defines.h>

#include <pybind11/pybind11/pybind11.h>

#include <stdint.h>

namespace omni
{
namespace isaac
{
namespace urdf
{

struct ImportConfig
{
    bool mergeFixedJoints = false;
    bool convexDecomp = false;
    bool importInertiaTensor = false;
    bool fixBase = true;
    bool selfCollision = false;
    float density = 0.0f; // default density used for objects without mass/inertia, 0 to autocompute
    UrdfJointTargetType defaultDriveType = UrdfJointTargetType::POSITION;
    float defaultDriveStrength = 1e7f;
    float defaultPositionDriveDamping = 1e5f;
    float distanceScale = 1.0f;
    UrdfAxis upVector = { 0.0f, 0.0f, 1.0f };
    bool createPhysicsScene = false;
    bool makeDefaultPrim = false;
    UrdfNormalSubdivisionScheme subdivisionScheme = UrdfNormalSubdivisionScheme::BILINEAR;
    // bool flipVisuals = false;

    bool makeInstanceable = false;
    std::string instanceableMeshUsdPath = "./instanceable_meshes.usd";

    bool collisionFromVisuals = false; // Create collision geometry from visual geometry when missing collision.
};


struct Urdf
{
    CARB_PLUGIN_INTERFACE("omni::isaac::urdf::Urdf", 0, 1);

    // Parses a urdf file into a UrdfRobot data structure
    UrdfRobot(CARB_ABI* parseUrdf)(const std::string& assetRoot, const std::string& assetName, ImportConfig& importConfig);
    // Imports a UrdfRobot into the stage
    std::string(CARB_ABI* importRobot)(const std::string& assetRoot,
                                       const std::string& assetName,
                                       const UrdfRobot& robot,
                                       ImportConfig& importConfig,
                                       const std::string& stage);

    pybind11::dict(CARB_ABI* getKinematicChain)(const UrdfRobot& robot);
};
}
}
}
