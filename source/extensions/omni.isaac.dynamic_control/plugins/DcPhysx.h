// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DcCommon.h"
#include "DcTypes.h"


namespace omni
{
namespace physx
{
struct IPhysx;
struct IPhysxSceneQuery;

}
}

namespace omni
{
namespace isaac
{
namespace dynamic_control
{

class DcContext
{
public:
    explicit DcContext(uint32_t ctxId);

    uint32_t getId() const;
    DcHandle registerRigidBody(const pxr::SdfPath& usdPath);
    DcHandle registerJoint(const pxr::SdfPath& usdPath);
    DcHandle registerDof(const pxr::SdfPath& usdPath);
    DcHandle registerArticulation(const pxr::SdfPath& usdPath);
    DcHandle registerD6Joint(const pxr::SdfPath& usdPath);

    DcHandle addRigidBody(std::unique_ptr<DcRigidBody>&& rb, const pxr::SdfPath& usdPath);

    DcHandle addJoint(std::unique_ptr<DcJoint>&& joint, const pxr::SdfPath& usdPath);

    DcHandle addDof(std::unique_ptr<DcDof>&& dof, const pxr::SdfPath& usdPath);

    DcHandle addArticulation(std::unique_ptr<DcArticulation>&& art, const pxr::SdfPath& usdPath);

    DcHandle addAttractor(std::unique_ptr<DcAttractor>&& attractor, const pxr::SdfPath& usdPath);

    DcHandle addD6Joint(std::unique_ptr<DcD6Joint>&& dc_joint, const pxr::SdfPath& usdPath);


    DcHandle getRigidBodyHandle(const pxr::SdfPath& usdPath) const;

    DcHandle getJointHandle(const pxr::SdfPath& usdPath) const;

    // HMMM, there could be multiple DOFs at a single USD path (e.g. spherical joint)
    DcHandle getDofHandle(const pxr::SdfPath& usdPath) const;
    DcHandle getArticulationHandle(const pxr::SdfPath& usdPath) const;

    DcHandle getAttractorHandle(const pxr::SdfPath& usdPath) const;
    DcRigidBody* getRigidBody(DcHandle handle) const;
    DcJoint* getJoint(DcHandle handle) const;

    DcDof* getDof(DcHandle handle) const;

    DcArticulation* getArticulation(DcHandle handle) const;

    DcAttractor* getAttractor(DcHandle handle) const;

    DcD6Joint* getD6Joint(DcHandle handle) const;

    void removeRigidBody(DcHandle handle);
    void removeJoint(DcHandle handle);

    void removeArticulation(DcHandle handle);

    void removeAttractor(DcHandle handle);

    void removeD6Joint(DcHandle handle);
    void remove(DcHandle handle);
    void removeUsdPath(const pxr::SdfPath& usdPath);

    int numAttractors() const;

    int numD6Joints() const;

    omni::physx::IPhysx* physx = nullptr;
    omni::physx::IPhysxSceneQuery* physxSceneQuery = nullptr;
    bool isSimulating = false;
    pxr::UsdStageWeakPtr mStage = nullptr;

    bool wasPaused = false;
    // refresh physics pointers after a reset
    void refreshPhysicsPointers(bool verbose);

private:
    // refresh after a physics reset
    bool refreshPhysicsPointers(DcRigidBody* body, bool verbose);
    bool refreshPhysicsPointers(DcJoint* joint, bool verbose);
    // bool refreshPhysicsPointers(DcDof* dof, bool verbose); // refreshing joint will refresh its dofs
    bool refreshPhysicsPointers(DcArticulation* art, bool verbose);
    bool refreshPhysicsPointers(DcAttractor* att, bool verbose);
    bool refreshPhysicsPointers(DcD6Joint* d6joint, bool verbose);

    uint32_t mId = 0;

    Bucket<DcRigidBody> mRigidBodies;
    Bucket<DcJoint> mJoints;
    Bucket<DcDof> mDofs;
    Bucket<DcArticulation> mArticulations;
    Bucket<DcAttractor> mAttractors;
    Bucket<DcD6Joint> mD6Joints;

    std::unordered_map<pxr::SdfPath, DcHandle> mRigidBodyMap;
    std::unordered_map<pxr::SdfPath, DcHandle> mJointMap;
    std::unordered_map<pxr::SdfPath, DcHandle> mDofMap;
    std::unordered_map<pxr::SdfPath, DcHandle> mArticulationMap;
    std::unordered_map<pxr::SdfPath, DcHandle> mAttractorMap;
    std::unordered_map<pxr::SdfPath, DcHandle> mD6JointMap;

    // Maps USD paths to handles.  There can be more than one handle per path.
    // e.g., articulation at same path as one of its links
    // e.g., dof at the same path as a revolute/prismatic joint
    // e.g., multiple dofs of a spherical joint
    std::unordered_map<pxr::SdfPath, std::set<DcHandle>> mHandleMap;
};

}
}
}
