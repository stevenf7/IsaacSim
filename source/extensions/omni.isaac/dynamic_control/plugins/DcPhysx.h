// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "DcCommon.h"

#include <extensions/PxD6Joint.h>
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

#ifndef DC_TRACK_EDITOR_SIMULATION_STATE
#    define DC_TRACK_EDITOR_SIMULATION_STATE true
#endif

namespace std
{
// hash function for SdfPath
template <>
struct hash<pxr::SdfPath>
{
    size_t operator()(const pxr::SdfPath& path) const
    {
        return path.GetHash();
    }
};
}

namespace carb
{
namespace physics
{
struct PhysX;
}
}

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
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

    physx::PxRigidBody* pxRigidBody = nullptr;

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
    physx::PxArticulationJointReducedCoordinate* pxArticulationJoint = nullptr;

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

    physx::PxArticulationJointReducedCoordinate* pxArticulationJoint = nullptr;
    physx::PxArticulationAxis::Enum pxAxis = physx::PxArticulationAxis::eTWIST;

    DcDriveMode driveMode = DcDriveMode::eNone;

    // helper values used to compute the cacheIdx
    int linkIndex = 0;
    size_t count = 0;

    int cacheIdx = -1; // index in PxArticulationCache

    DcHandle joint = kDcInvalidHandle;

    // can get these from joint
    // DcHandle parentBody;
    // DcHandle childBody;
};

struct DcArticulation
{
    int numRigidBodies() const
    {
        return int(rigidBodies.size());
    }

    int numJoints() const
    {
        return int(joints.size());
    }

    int numDofs() const
    {
        return int(dofs.size());
    }

    bool refreshCache() const;

    DcHandle handle = kDcInvalidHandle;

    DcContext* ctx = nullptr;

    physx::PxArticulationReducedCoordinate* pxArticulation = nullptr;

    std::string name;
    pxr::SdfPath path;
    std::set<pxr::SdfPath> componentPaths;

    std::vector<DcRigidBody*> rigidBodies;
    std::vector<DcJoint*> joints;
    std::vector<DcDof*> dofs;

    std::map<std::string, DcRigidBody*> rigidBodyMap;
    std::map<std::string, DcJoint*> jointMap;
    std::map<std::string, DcDof*> dofMap;

    mutable physx::PxArticulationCache* pxArticulationCache = nullptr;
    mutable int64_t cacheAge = -1;

    mutable std::vector<DcRigidBodyState> rigidBodyStateCache;
    mutable std::vector<DcDofState> dofStateCache;
};

struct DcAttractor
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;
    physx::PxD6Joint* pxJoint = nullptr;
    DcAttractorProperties props{};
    pxr::SdfPath path;
};

struct DcD6Joint
{
    DcHandle handle = kDcInvalidHandle;
    DcContext* ctx = nullptr;
    physx::PxD6Joint* pxJoint = nullptr;
    DcD6JointProperties props{};
    pxr::SdfPath path;
};

class DcContext
{
public:
    explicit DcContext(uint32_t ctxId) : mId(ctxId)
    {
    }

    uint32_t getId() const
    {
        return mId;
    }

    DcHandle registerRigidBody(const pxr::SdfPath& usdPath);
    DcHandle registerJoint(const pxr::SdfPath& usdPath);
    DcHandle registerDof(const pxr::SdfPath& usdPath);
    DcHandle registerArticulation(const pxr::SdfPath& usdPath);
    DcHandle registerD6Joint(const pxr::SdfPath& usdPath);

    DcHandle addRigidBody(std::unique_ptr<DcRigidBody>&& rb, const pxr::SdfPath& usdPath)
    {
        uint32_t id = mRigidBodies.add(std::move(rb));
        DcHandle handle = makeHandle(id, eDcObjectRigidBody, mId);
        mRigidBodyMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
        return handle;
    }

    DcHandle addJoint(std::unique_ptr<DcJoint>&& joint, const pxr::SdfPath& usdPath)
    {
        uint32_t id = mJoints.add(std::move(joint));
        DcHandle handle = makeHandle(id, eDcObjectJoint, mId);
        mJointMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
        return handle;
    }

    DcHandle addDof(std::unique_ptr<DcDof>&& dof, const pxr::SdfPath& usdPath)
    {
        uint32_t id = mDofs.add(std::move(dof));
        DcHandle handle = makeHandle(id, eDcObjectDof, mId);
        mDofMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
        return handle;
    }

    DcHandle addArticulation(std::unique_ptr<DcArticulation>&& art, const pxr::SdfPath& usdPath)
    {
#if 1
        // assign this articulation to the specified usdPath
        uint32_t id = mArticulations.add(std::move(art));
        DcHandle handle = makeHandle(id, eDcObjectArticulation, mId);
        mArticulationMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
#else
        // assign this articulation handle to all the component paths
        DcArticulation* artPtr = art.get();
        uint32_t id = mArticulations.add(std::move(art));
        DcHandle handle = makeHandle(id, eDcObjectArticulation, mId);
        for (auto& path : artPtr->componentPaths)
        {
            mArticulationMap[path] = handle;
            mHandleMap[path].insert(handle);
        }
#endif
        return handle;
    }

    DcHandle addAttractor(std::unique_ptr<DcAttractor>&& attractor, const pxr::SdfPath& usdPath)
    {
        uint32_t id = mAttractors.add(std::move(attractor));
        DcHandle handle = makeHandle(id, eDcObjectAttractor, mId);
        mAttractorMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
        return handle;
    }

    DcHandle addD6Joint(std::unique_ptr<DcD6Joint>&& dc_joint, const pxr::SdfPath& usdPath)
    {
        uint32_t id = mD6Joints.add(std::move(dc_joint));
        DcHandle handle = makeHandle(id, eDcObjectD6Joint, mId);
        mD6JointMap[usdPath] = handle;
        mHandleMap[usdPath].insert(handle);
        return handle;
    }


    DcHandle getRigidBodyHandle(const pxr::SdfPath& usdPath) const
    {
        auto it = mRigidBodyMap.find(usdPath);
        if (it != mRigidBodyMap.end())
        {
            return it->second;
        }
        return kDcInvalidHandle;
    }

    DcHandle getJointHandle(const pxr::SdfPath& usdPath) const
    {
        auto it = mJointMap.find(usdPath);
        if (it != mJointMap.end())
        {
            return it->second;
        }
        return kDcInvalidHandle;
    }

    // HMMM, there could be multiple DOFs at a single USD path (e.g. spherical joint)
    DcHandle getDofHandle(const pxr::SdfPath& usdPath) const
    {
        auto it = mDofMap.find(usdPath);
        if (it != mDofMap.end())
        {
            return it->second;
        }
        return kDcInvalidHandle;
    }

    DcHandle getArticulationHandle(const pxr::SdfPath& usdPath) const
    {
        // look up articulation
        auto artIt = mArticulationMap.find(usdPath);
        if (artIt != mArticulationMap.end())
        {
            return artIt->second;
        }

        // is it an articulation link?
        auto bodyIt = mRigidBodyMap.find(usdPath);
        if (bodyIt != mRigidBodyMap.end())
        {
            DcHandle bodyHandle = bodyIt->second;
            DcRigidBody* body = getRigidBody(bodyHandle);
            if (body && body->art)
            {
                return body->art->handle;
            }
        }

        // is it an articulation joint?
        auto jointIt = mJointMap.find(usdPath);
        if (jointIt != mJointMap.end())
        {
            DcHandle jointHandle = jointIt->second;
            DcJoint* joint = getJoint(jointHandle);
            if (joint && joint->art)
            {
                return joint->art->handle;
            }
        }

        return kDcInvalidHandle;
    }

    DcHandle getAttractorHandle(const pxr::SdfPath& usdPath) const
    {
        auto it = mAttractorMap.find(usdPath);
        if (it != mAttractorMap.end())
        {
            return it->second;
        }
        return kDcInvalidHandle;
    }

    DcRigidBody* getRigidBody(DcHandle handle) const
    {
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectRigidBody)
        {
            auto objId = getHandleObjectId(handle);
            return mRigidBodies.get(objId);
        }
        return nullptr;
    }

    DcJoint* getJoint(DcHandle handle) const
    {
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectJoint)
        {
            auto objId = getHandleObjectId(handle);
            return mJoints.get(objId);
        }
        return nullptr;
    }

    DcDof* getDof(DcHandle handle) const
    {
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectDof)
        {
            auto objId = getHandleObjectId(handle);
            return mDofs.get(objId);
        }
        return nullptr;
    }

    DcArticulation* getArticulation(DcHandle handle) const
    {
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectArticulation)
        {
            auto objId = getHandleObjectId(handle);
            return mArticulations.get(objId);
        }
        return nullptr;
    }

    DcAttractor* getAttractor(DcHandle handle) const
    {
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectAttractor)
        {
            auto objId = getHandleObjectId(handle);
            return mAttractors.get(objId);
        }
        return nullptr;
    }

    DcD6Joint* getD6Joint(DcHandle handle) const
    {
        // DC_LOG_INFO("searching for Dc D6 joint handle %ld (%d - %d)", handle,
        // getHandleTypeId(handle),eDcObjectD6Joint);
        if (getHandleContextId(handle) == mId && getHandleTypeId(handle) == eDcObjectD6Joint)
        {
            auto objId = getHandleObjectId(handle);
            return mD6Joints.get(objId);
        }
        return nullptr;
    }

    void removeRigidBody(DcHandle handle)
    {
        DcRigidBody* body = getRigidBody(handle);
        if (body)
        {
            auto bodyIt = mRigidBodyMap.find(body->path);
            if (bodyIt != mRigidBodyMap.end())
            {
                mRigidBodyMap.erase(bodyIt);
            }
            auto handleSet = mHandleMap.find(body->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mRigidBodies.remove(objId);
        }
    }

    void removeJoint(DcHandle handle)
    {
        DcJoint* joint = getJoint(handle);
        if (joint)
        {
            auto jointIt = mJointMap.find(joint->path);
            if (jointIt != mJointMap.end())
            {
                mJointMap.erase(jointIt);
            }
            auto handleSet = mHandleMap.find(joint->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mJoints.remove(objId);
        }
    }

    /*
    // don't remove individual dofs; remove joints instead
    void removeDof(DcHandle handle)
    {
        DcDof* dof = getDof(handle);
        if (dof)
        {
            auto dofIt = mDofMap.find(dof->path);
            if (dofIt != mDofMap.end())
            {
                mDofMap.erase(dofIt);
            }
            auto handleSet = mHandleMap.find(dof->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mDofs.remove(objId);
        }
    }
    */

    void removeArticulation(DcHandle handle)
    {
        DcArticulation* art = getArticulation(handle);
        if (art)
        {
            auto artIt = mArticulationMap.find(art->path);
            if (artIt != mArticulationMap.end())
            {
                mArticulationMap.erase(artIt);
            }
            auto handleSet = mHandleMap.find(art->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mArticulations.remove(objId);
        }
    }

    void removeAttractor(DcHandle handle)
    {
        DcAttractor* att = getAttractor(handle);
        if (att)
        {
            auto attIt = mAttractorMap.find(att->path);
            if (attIt != mAttractorMap.end())
            {
                mAttractorMap.erase(attIt);
            }
            auto handleSet = mHandleMap.find(att->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mAttractors.remove(objId);
        }
    }

    void removeD6Joint(DcHandle handle)
    {
        DcD6Joint* joint = getD6Joint(handle);
        if (joint)
        {
            auto jointIt = mD6JointMap.find(joint->path);
            if (jointIt != mD6JointMap.end())
            {
                mD6JointMap.erase(jointIt);
            }
            auto handleSet = mHandleMap.find(joint->path);
            if (handleSet != mHandleMap.end())
            {
                handleSet->second.erase(handle);
                if (handleSet->second.empty())
                {
                    mHandleMap.erase(handleSet);
                }
            }
            auto objId = getHandleObjectId(handle);
            mD6Joints.remove(objId);
        }
    }

    void remove(DcHandle handle)
    {
        DcObjectType type = (DcObjectType)getHandleTypeId(handle);
        switch (type)
        {
        case DcObjectType::eDcObjectRigidBody:
            removeRigidBody(handle);
            break;
        case DcObjectType::eDcObjectJoint:
            removeJoint(handle);
            break;
        case DcObjectType::eDcObjectArticulation:
            removeArticulation(handle);
            break;
        case DcObjectType::eDcObjectAttractor:
            removeAttractor(handle);
            break;
        case DcObjectType::eDcObjectD6Joint:
            removeD6Joint(handle);
            break;
        default:
            break;
        }
    }

    void removeUsdPath(const pxr::SdfPath& usdPath)
    {
        auto it = mHandleMap.find(usdPath);
        if (it != mHandleMap.end())
        {
            std::set<DcHandle>& handles = it->second;
            for (auto& h : handles)
            {
                remove(h);
            }
        }
    }

    int numAttractors() const
    {
        return int(mAttractorMap.size());
    }

    int numD6Joints() const
    {
        return int(mD6JointMap.size());
    }

    /*
    void clear()
    {
        mRigidBodies.clear();
        mDofs.clear();
        mArticulations.clear();
        mAttractors.clear();

        mRigidBodyMap.clear();
        mDofMap.clear();
        mArticulationMap.clear();
    }
    */

    carb::physics::PhysX* physx = nullptr;
    // physx::PxScene* pxScene = nullptr;

    int64_t frameno = 0;

#if DC_TRACK_EDITOR_SIMULATION_STATE
    bool isSimulating = false;
#endif

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
