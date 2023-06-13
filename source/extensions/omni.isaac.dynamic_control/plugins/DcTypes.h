// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#pragma once

#include "DcCommon.h"
#if defined(_WIN32)
#    include <extensions/PxD6Joint.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <extensions/PxD6Joint.h>
#    pragma GCC diagnostic pop
#endif

#include <omni/isaac/dynamic_control/DynamicControlTypes.h>
#include <pxr/usd/sdf/path.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
// Forward declarations
struct DcRigidBody;
struct DcJoint;
struct DcDof;
struct DcArticulation;
struct DcAttractor;
class DcContext;

struct DcRigidBody
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;

    // will only be set if body is an articulation link
    DcArticulation* art = nullptr;

    std::string name;
    pxr::SdfPath path;

    ::physx::PxRigidBody* pxRigidBody = nullptr;

    DcHandle parentJoint = kDcInvalidHandle;
    // std::vector<DcHandle> parentJoints;
    std::vector<DcHandle> childJoints;

    // location wrt which the body poses are set/get
    carb::Float3 origin{ 0.0f, 0.0f, 0.0f };
};

struct DcJoint
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;

    DcJointType type = DcJointType::eNone;

    // will only be set if joint is an articulation joint
    DcArticulation* art = nullptr;

    std::string name;
    pxr::SdfPath path;

    // only reduced coordinate articulation joints are supported for now
    ::physx::PxArticulationJointReducedCoordinate* pxArticulationJoint = nullptr;

    DcHandle parentBody = kDcInvalidHandle;
    DcHandle childBody = kDcInvalidHandle;

    std::vector<DcHandle> dofs;
};

struct DcDof
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;

    DcDofType type = DcDofType::eNone;

    DcArticulation* art = nullptr;

    std::string name;
    pxr::SdfPath path;

    ::physx::PxArticulationJointReducedCoordinate* pxArticulationJoint = nullptr;
    ::physx::PxArticulationAxis::Enum pxAxis = ::physx::PxArticulationAxis::eTWIST;

    DcDriveMode driveMode = DcDriveMode::eAcceleration;


    size_t cacheIdx = 0; // index in PxArticulationCache

    DcHandle joint = kDcInvalidHandle;

    // can get these from joint
    // DcHandle parentBody;
    // DcHandle childBody;
};

struct DcArticulation
{
    size_t numRigidBodies() const
    {
        return rigidBodies.size();
    }

    size_t numJoints() const
    {
        return joints.size();
    }

    size_t numDofs() const
    {
        return dofs.size();
    }

    bool refreshCache(const ::physx::PxArticulationCacheFlags& flags = ::physx::PxArticulationCacheFlag::eALL) const;

    DcHandle handle = kDcInvalidHandle;

    DcContext* ctx = nullptr;

    ::physx::PxArticulationReducedCoordinate* pxArticulation = nullptr;

    std::string name;
    pxr::SdfPath path;
    std::set<pxr::SdfPath> componentPaths;

    std::vector<DcRigidBody*> rigidBodies;
    std::vector<DcJoint*> joints;
    std::vector<DcDof*> dofs;

    std::map<std::string, DcRigidBody*> rigidBodyMap;
    std::map<std::string, DcJoint*> jointMap;
    std::map<std::string, DcDof*> dofMap;

    mutable ::physx::PxArticulationCache* pxArticulationCache = nullptr;
    mutable int64_t cacheAge = -1;

    mutable std::vector<DcRigidBodyState> rigidBodyStateCache;
    mutable std::vector<DcDofState> dofStateCache;
};

struct DcAttractor
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;
    ::physx::PxD6Joint* pxJoint = nullptr;
    DcAttractorProperties props{};
    pxr::SdfPath path;
};

struct DcD6Joint
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;
    ::physx::PxD6Joint* pxJoint = nullptr;
    DcD6JointProperties props{};
    pxr::SdfPath path;
};

}
}
}
