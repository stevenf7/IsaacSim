// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "MjcfParser.h"
#include "MjcfTypes.h"
#include "MjcfUsd.h"
#include "MjcfUtils.h"
#include "core/mesh.h"

#include <carb/logging/Log.h>

#include <omni/isaac/math/core/maths.h>
#include <omni/isaac/mjcf/mjcf.h>

#include <iostream>
#include <iterator>
#include <map>
#include <queue>
#include <set>
#include <string>
#include <tinyxml2.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace mjcf
{

class MJCFImporter
{
public:
    std::string baseDirPath;
    std::string defaultClassName;
    std::map<std::string, MJCFClass> classes;

    MJCFCompiler compiler;
    std::vector<MJCFBody*> bodies;
    std::vector<MJCFGeom*> collisionGeoms;
    std::vector<MJCFActuator> actuators;
    std::vector<MJCFTendon> tendons;
    std::vector<MJCFContact> contacts;

    std::map<std::string, pxr::UsdPhysicsRevoluteJoint> revoluteJointsMap;
    std::map<std::string, pxr::UsdPhysicsPrismaticJoint> prismaticJointsMap;

    std::queue<MJCFBody*> bodyQueue;
    std::map<std::string, int> jointToKinematicHierarchy;

    std::map<std::string, int> jointToActuatorIdx;

    std::map<std::string, MeshInfo> simulationMeshCache;

    std::vector<ContactNode> contactGraph;

    std::map<std::string, MJCFBody*> nameToBody;
    std::map<std::string, int> geomNameToIdx;

    std::map<std::string, std::string> nameToUsdCollisionPrim;

    bool createBodyForFixedJoint;

    bool isLoaded = false;

    MJCFImporter(const std::string fullPath);
    ~MJCFImporter();

    void populateBodyLookup(MJCFBody* body);
    bool AddPhysicsEntities(pxr::UsdStageWeakPtr stage,
                            const Transform trans,
                            const std::string& rootPrimPath,
                            const ImportConfig& config);

    void CreateInstanceableMeshes(pxr::UsdStageRefPtr stage,
                                  MJCFBody* body,
                                  const std::string rootPrimPath,
                                  const bool isRoot,
                                  const ImportConfig& config);

    void CreatePhysicsBodyAndJoint(pxr::UsdStageWeakPtr stage,
                                   MJCFBody* body,
                                   const std::string rootPrimPath,
                                   const Transform trans,
                                   const bool isRoot,
                                   const std::string parentBodyPath,
                                   const ImportConfig& config,
                                   const std::string instanceableUsdPath);

    void computeJointFrame(Transform& origin, int* axisMap, const MJCFBody* body);

    bool contactBodyExclusion(MJCFBody* body1, MJCFBody* body2);
    bool createContactGraph();

    void computeKinematicHierarchy();
};

}
}
}
