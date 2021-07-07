// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DcPhysx.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>

#include <map>
#include <string>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.dynamic_control.plugin", "Isaac Dynamic Control",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::dynamic_control::DynamicControl)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::physx::IPhysxSceneQuery, omni::kit::IStageUpdate)

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
// private stuff
namespace
{

constexpr PxD6Axis::Enum g_dcToPxAxis[6]{
    PxD6Axis::eX, PxD6Axis::eY, PxD6Axis::eZ, PxD6Axis::eTWIST, PxD6Axis::eSWING1, PxD6Axis::eSWING2,
};

omni::kit::IStageUpdate* g_su = nullptr;
omni::kit::StageUpdateNode* g_suNode = nullptr;

// Only one "current" context is supported now.  This is due to limitations in the IStageUpdate interface.
uint32_t g_dcCtxId = 0;
std::unique_ptr<DcContext> g_dcCtx = nullptr;


#define DC_CHECK_SIMULATING() (checkSimulating(__func__))
#define DC_LOOKUP_RIGID_BODY(handle) (lookupRigidBody((handle), __func__))
#define DC_LOOKUP_JOINT(handle) (lookupJoint((handle), __func__))
#define DC_LOOKUP_DOF(handle) (lookupDof((handle), __func__))
#define DC_LOOKUP_ARTICULATION(handle) (lookupArticulation((handle), __func__))
#define DC_LOOKUP_ATTRACTOR(handle) (lookupAttractor((handle), __func__))
#define DC_LOOKUP_D6JOINT(handle) (lookupD6Joint((handle), __func__))

inline const pxr::SdfPath& intToPath(const uint64_t& path)
{
    static_assert(sizeof(pxr::SdfPath) == sizeof(uint64_t), "Change to make the same size as pxr::SdfPath");

    return reinterpret_cast<const pxr::SdfPath&>(path);
}


inline bool checkSimulating(const char* funcname)
{
    if (g_dcCtx && g_dcCtx->isSimulating)
    {
        return true;
    }
    else
    {
        CARB_LOG_WARN("%s: Function called while not simulating", funcname);
        return false;
    }
}

inline DcRigidBody* lookupRigidBody(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcRigidBody* body = ctx->getRigidBody(handle);
        if (!body)
        {
            CARB_LOG_ERROR("%s: Invalid or expired body handle", funcname);
        }
        return body;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

inline DcJoint* lookupJoint(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcJoint* joint = ctx->getJoint(handle);
        if (!joint)
        {
            CARB_LOG_ERROR("%s: Invalid or expired joint handle", funcname);
        }
        return joint;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

inline DcDof* lookupDof(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcDof* dof = ctx->getDof(handle);
        if (!dof)
        {
            CARB_LOG_ERROR("%s: Invalid or expired dof handle", funcname);
        }
        return dof;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

inline DcArticulation* lookupArticulation(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcArticulation* art = ctx->getArticulation(handle);
        if (!art)
        {
            CARB_LOG_ERROR("%s: Invalid or expired articulation handle", funcname);
        }
        return art;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

inline DcAttractor* lookupAttractor(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcAttractor* att = ctx->getAttractor(handle);
        if (!att)
        {
            CARB_LOG_ERROR("%s: Invalid or expired attractor handle", funcname);
        }
        return att;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

inline DcD6Joint* lookupD6Joint(DcHandle handle, const char* funcname)
{
    auto& ctx = g_dcCtx;
    if (ctx)
    {
        DcD6Joint* joint = ctx->getD6Joint(handle);
        if (!joint)
        {
            CARB_LOG_ERROR("%s: Invalid or expired D6 Joint handle", funcname);
        }
        return joint;
    }
    else
    {
        CARB_LOG_ERROR("%s: No context", funcname);
        return nullptr;
    }
}

template <typename T>
inline void ZeroArray(T* arr, size_t count)
{
    std::memset(arr, 0, count * sizeof(*arr));
}

inline carb::Float3 asFloat3(const PxVec3& v)
{
    return carb::Float3{ v.x, v.y, v.z };
}

inline carb::Float4 asFloat4(const PxQuat& q)
{
    return carb::Float4{ q.x, q.y, q.z, q.w };
}

inline DcTransform asDcTransform(const PxTransform& pose)
{
    return DcTransform{ asFloat3(pose.p), asFloat4(pose.q) };
}

inline PxVec3 asPxVec3(const carb::Float3& v)
{
    return PxVec3{ v.x, v.y, v.z };
}

inline PxQuat asPxQuat(const carb::Float4& q)
{
    return PxQuat{ q.x, q.y, q.z, q.w };
}

inline PxTransform asPxTransform(const DcTransform& pose)
{
    return PxTransform{ asPxVec3(pose.p), asPxQuat(pose.r) };
}

std::unique_ptr<DcContext> createContext()
{
    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return nullptr;
    }

    omni::physx::IPhysx* physx = framework->acquireInterface<omni::physx::IPhysx>();
    if (!physx)
    {
        CARB_LOG_ERROR("Failed to acquire PhysX interface");
        return nullptr;
    }
    else
    {
        auto desc = physx->getInterfaceDesc();
        CARB_LOG_INFO("Acquired interface '%s', version %d.%d\n", desc.name, desc.version.major, desc.version.minor);
    }

    omni::physx::IPhysxSceneQuery* physxSceneQuery = framework->acquireInterface<omni::physx::IPhysxSceneQuery>();
    if (!physxSceneQuery)
    {
        CARB_LOG_ERROR("Failed to acquire PhysX Scene Query interface");
        return nullptr;
    }
    else
    {
        auto desc = physxSceneQuery->getInterfaceDesc();
        CARB_LOG_INFO("Acquired interface '%s', version %d.%d\n", desc.name, desc.version.major, desc.version.minor);
    }

    ++g_dcCtxId;

    std::unique_ptr<DcContext> ctx = std::make_unique<DcContext>(g_dcCtxId);
    ctx->physx = physx;
    ctx->physxSceneQuery = physxSceneQuery;

    /*
    // get scene pointer
    PxScene* scene = nullptr;
    if (scenePath)
    {
        scene = (PxScene*)ctx->physx->getPhysXPtr(SdfPath(scenePath), omni::physx::PhysXType::ePTScene);
        printf("Got scene ptr %p\n", (void*)scene);
    }

    ctx->pxScene = scene;

    if (scene)
    {
        PxU32 numArts = scene->getNbArticulations();
        printf("Found %u articulation%s\n", numArts, numArts == 1 ? "" : "s");
        if (numArts > 0)
        {
            std::vector<PxArticulationReducedCoordinate*> arts(numArts);
            scene->getArticulations(arts.data(), numArts);
            for (PxU32 i = 0; i < numArts; i++)
            {
                if (arts[i]->getConcreteType() == PxConcreteType::eARTICULATION_REDUCED_COORDINATE)
                {
                    PxArticulationReducedCoordinate* arc = static_cast<PxArticulationReducedCoordinate*>(arts[i]);

                    // look up the USD path
                    size_t objId = (size_t)arc->userData;
                    printf("Found articulation id %llu\n", (unsigned long long)objId);
                }
            }
        }
    }
    */

    return std::move(ctx);
}

// void CARB_ABI DcDestroyContext(auto & ctx)
void destroyContext(std::unique_ptr<DcContext>& ctx)
{
    if (ctx)
    {
        ctx.reset();
    }
}

} // end of anonymous namespace

bool DcArticulation::refreshCache() const
{
    if (!pxArticulation)
    {
        return false;
    }

    if (!pxArticulation->getScene())
    {
        CARB_LOG_WARN("Failed to refresh articulation cache, not attached to scene");
        return false;
    }

    // make sure we have the articulation cache
    if (!pxArticulationCache)
    {
        pxArticulationCache = pxArticulation->createCache();
        if (!pxArticulationCache)
        {
            return false;
        }
    }

    // if (cacheAge < ctx->frameno)
    //{

    pxArticulation->copyInternalStateToCache(*pxArticulationCache, PxArticulationCacheFlag::eALL);

    // Call this before any inverse dynamics methods
    pxArticulation->commonInit();
    // Put joint force in cache
    pxArticulation->computeJointForce(*pxArticulationCache);
    //    cacheAge = ctx->frameno;
    //}
    if (pxArticulation->getArticulationFlags() & PxArticulationFlag::eCOMPUTE_JOINT_FORCES)
    {
        pxArticulation->copyInternalStateToCache(*pxArticulationCache, PxArticulationCacheFlag::eJOINT_SOLVER_FORCES);
    }

    return true;
}


void CARB_ABI DcWakeUpRigidBody(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        PxRigidBody* rigid = body->pxRigidBody;
        PxActorType::Enum type = rigid->getType();
        if (type == PxActorType::eRIGID_DYNAMIC)
        {
            // wake the body
            static_cast<PxRigidDynamic*>(rigid)->wakeUp();
        }
        else if (type == PxActorType::eARTICULATION_LINK && body->art && body->art->pxArticulation)
        {
            // wake the articulation
            body->art->pxArticulation->wakeUp();
        }
    }
}


void CARB_ABI DcHello()
{
    printf("Hello from Dynamic Control\n");
}

bool CARB_ABI DcIsSimulating()
{
    if (g_dcCtx)
    {
        return g_dcCtx->isSimulating;
    }
    else
    {
        return false;
    }
}

DcHandle CARB_ABI DcGetRigidBody(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        CARB_LOG_ERROR("No context");
        return kDcInvalidHandle;
    }

    if (!usdPath || !*usdPath)
    {
        CARB_LOG_ERROR("Invalid USD path");
        return kDcInvalidHandle;
    }

    return ctx->registerRigidBody(SdfPath(usdPath));
}

DcHandle CARB_ABI DcGetJoint(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        CARB_LOG_ERROR("No context");
        return kDcInvalidHandle;
    }

    if (!usdPath || !*usdPath)
    {
        CARB_LOG_ERROR("Invalid USD path");
        return kDcInvalidHandle;
    }

    return ctx->registerJoint(SdfPath(usdPath));
}

DcHandle CARB_ABI DcGetDof(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        CARB_LOG_ERROR("No context");
        return kDcInvalidHandle;
    }

    if (!usdPath || !*usdPath)
    {
        CARB_LOG_ERROR("Invalid USD path");
        return kDcInvalidHandle;
    }

    return ctx->registerDof(SdfPath(usdPath));
}

DcHandle CARB_ABI DcGetArticulation(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        CARB_LOG_ERROR("No context");
        return kDcInvalidHandle;
    }

    if (!usdPath || !*usdPath)
    {
        CARB_LOG_ERROR("Invalid USD path");
        return kDcInvalidHandle;
    }

    return ctx->registerArticulation(SdfPath(usdPath));
}

DcHandle CARB_ABI DcGetD6Joint(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        CARB_LOG_ERROR("No context");
        return kDcInvalidHandle;
    }

    if (!usdPath || !*usdPath)
    {
        CARB_LOG_ERROR("Invalid USD path");
        return kDcInvalidHandle;
    }

    return ctx->registerD6Joint(SdfPath(usdPath));
}

DcObjectType CARB_ABI DcPeekObjectType(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return eDcObjectNone;
    }

    if (!usdPath)
    {
        return eDcObjectNone;
    }

    omni::physx::IPhysx* physx = ctx->physx;

    // check if it's an articulation
    PxArticulationReducedCoordinate* abase =
        (PxArticulationReducedCoordinate*)physx->getPhysXPtr(SdfPath(usdPath), omni::physx::PhysXType::ePTArticulation);
    if (abase)
    {
        return eDcObjectArticulation;
    }

    // check if it's a rigid body
    PxActor* actor = (PxActor*)physx->getPhysXPtr(SdfPath(usdPath), omni::physx::PhysXType::ePTActor);
    if (actor)
    {
        PxActorType::Enum actorType = actor->getType();
        if (actorType == PxActorType::eRIGID_DYNAMIC || actorType == PxActorType::eARTICULATION_LINK)
        {
            return eDcObjectRigidBody;
        }
    }

    // check if it's an articulation link
    PxArticulationLink* link = (PxArticulationLink*)physx->getPhysXPtr(SdfPath(usdPath), omni::physx::PhysXType::ePTLink);
    if (link)
    {
        return eDcObjectRigidBody;
    }

    // check if it's a d6joint
    PxD6Joint* d6joint = (PxD6Joint*)physx->getPhysXPtr(SdfPath(usdPath), omni::physx::PhysXType::ePTJoint);
    if (d6joint)
    {
        return eDcObjectD6Joint;
    }

    // check if it's a joint
    PxJoint* joint = (PxJoint*)physx->getPhysXPtr(SdfPath(usdPath), omni::physx::PhysXType::ePTJoint);
    if (joint)
    {
        return eDcObjectJoint;
    }

    // check if it's an articulation joint
    PxArticulationJointReducedCoordinate* artJoint = (PxArticulationJointReducedCoordinate*)physx->getPhysXPtr(
        SdfPath(usdPath), omni::physx::PhysXType::ePTLinkJoint);
    if (artJoint)
    {
        return eDcObjectJoint;
    }

    return eDcObjectNone;
}

DcHandle CARB_ABI DcGetObject(const char* usdPath)
{
    (void)DC_CHECK_SIMULATING();

    DcObjectType type = DcPeekObjectType(usdPath);
    switch (type)
    {
    case eDcObjectRigidBody:
        return DcGetRigidBody(usdPath);
    case eDcObjectJoint:
        return DcGetJoint(usdPath);
    case eDcObjectD6Joint:
        return DcGetD6Joint(usdPath);
    case eDcObjectDof:
        return DcGetDof(usdPath);
    case eDcObjectArticulation:
        return DcGetArticulation(usdPath);
    default:
        return kDcInvalidHandle;
    }
}

DcObjectType CARB_ABI DcGetObjectType(DcHandle handle)
{
    (void)DC_CHECK_SIMULATING();

    uint32_t type = getHandleTypeId(handle);
    if (type < kDcObjectTypeCount)
    {
        return static_cast<DcObjectType>(type);
    }
    return eDcObjectNone;
}

const char* CARB_ABI DcGetObjectTypeName(DcHandle handle)
{
    (void)DC_CHECK_SIMULATING();

    DcObjectType type = DcGetObjectType(handle);
    switch (type)
    {
    case eDcObjectRigidBody:
        return "RigidBody";
    case eDcObjectJoint:
        return "Joint";
    case eDcObjectD6Joint:
        return "D6Joint";
    case eDcObjectDof:
        return "Dof";
    case eDcObjectArticulation:
        return "Articulation";
    case eDcObjectAttractor:
        return "Attractor";
    default:
        return "None";
    }
}

#if 0
int CARB_ABI DcGetArticulationCount(const auto & ctx)
{
    (void)DC_CHECK_SIMULATING();

    if (ctx && ctx->physx)
    {
        if (ctx->pxScene)
        {
            PxU32 totalCount = ctx->pxScene->getNbArticulations();

            // count reduced coordinate articulations, which are the only ones we support now
            std::vector<PxArticulationReducedCoordinate*> arts(totalCount);
            ctx->pxScene->getArticulations(arts.data(), totalCount);
            int count = 0;
            for (PxU32 i = 0; i < totalCount; i++)
            {
                if (arts[i]->getConcreteType() == PxConcreteType::eARTICULATION_REDUCED_COORDINATE)
                {
                    ++count;
                }
            }
            return count;
        }
    }
    return 0;
}

int CARB_ABI DcGetArticulations(auto & ctx, DcArticulation** userBuffer, int bufferSize)
{
    (void)DC_CHECK_SIMULATING();

    if (!ctx || !ctx->pxScene || !userBuffer || !bufferSize)
    {
        return 0;
    }

    int count = DcGetArticulationCount(ctx);
    int n = std::min(count, bufferSize);

    // TODO: finish me!
    for (int i = 0; i < n; i++)
    {
    }

    return n;
}
#endif


void CARB_ABI DcWakeUpArticulation(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && art->pxArticulation)
    {
        art->pxArticulation->wakeUp();
    }
}

const char* CARB_ABI DcGetArticulationName(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        return art->name.c_str();
    }
    return nullptr;
}

const char* CARB_ABI DcGetArticulationPath(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        return art->path.GetString().c_str();
    }
    return nullptr;
}

int CARB_ABI DcGetArticulationBodyCount(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        return art->numRigidBodies();
    }
    return 0;
}

DcHandle CARB_ABI DcGetArticulationBody(DcHandle artHandle, int bodyIdx)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        if (bodyIdx >= 0 && bodyIdx < art->numRigidBodies())
        {
            return art->rigidBodies[bodyIdx]->handle;
        }
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcFindArticulationBody(DcHandle artHandle, const char* bodyName)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && bodyName)
    {
        auto it = art->rigidBodyMap.find(bodyName);
        if (it != art->rigidBodyMap.end())
        {
            return it->second->handle;
        }
    }
    return kDcInvalidHandle;
}

int CARB_ABI DcFindArticulationBodyIndex(DcHandle artHandle, const char* bodyName)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && bodyName)
    {
        int numBodies = int(art->rigidBodies.size());
        for (int i = 0; i < numBodies; i++)
        {
            if (art->rigidBodies[i]->name == bodyName)
            {
                return i;
            }
        }
    }
    return -1;
}

DcHandle CARB_ABI DcGetArticulationRootBody(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        if (!art->rigidBodies.empty())
        {
            return art->rigidBodies[0]->handle;
        }
    }
    return kDcInvalidHandle;
}

DcRigidBodyState* CARB_ABI DcGetArticulationBodyStates(DcHandle artHandle, DcStateFlags flags)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art)
    {
        return nullptr;
    }

    for (int i = 0; i < art->numRigidBodies(); i++)
    {
        PxRigidBody* body = art->rigidBodies[i]->pxRigidBody;
        DcRigidBodyState& state = art->rigidBodyStateCache[i];
        if (body)
        {
            if (flags & kDcStatePos)
            {
                PxTransform pose = body->getGlobalPose();
                state.pose.p = asFloat3(pose.p);
                state.pose.r = asFloat4(pose.q);

                // apply offset
                carb::Float3& origin = art->rigidBodies[i]->origin;
                state.pose.p.x -= origin.x;
                state.pose.p.y -= origin.y;
                state.pose.p.z -= origin.z;
            }
            if (flags & kDcStateVel)
            {
                state.vel.linear = asFloat3(body->getLinearVelocity());
                state.vel.angular = asFloat3(body->getAngularVelocity());
            }
        }
        else
        {
            // hmmm
            return nullptr;
        }
    }

    return art->rigidBodyStateCache.data();
}

// bool CARB_ABI DcSetArticulationBodyStates(DcHandle artHandle, const DcRigidBodyState* states, DcStateFlags flags)
// {
//     (void)DC_CHECK_SIMULATING();

//     DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
//     if (!art || !flags)
//     {
//         return false;
//     }

//     for (int i = 0; i < art->numRigidBodies(); i++)
//     {
//         PxRigidBody* body = art->rigidBodies[i]->pxRigidBody;
//         const DcRigidBodyState& state = states[i];
//         if (body)
//         {
//             if (flags & kDcStatePos)
//             {
//                 PxTransform pose;
//                 pose.p = asPxVec3(state.pose.p);
//                 pose.q = asPxQuat(state.pose.r);

//                 // apply offset
//                 carb::Float3& origin = art->rigidBodies[i]->origin;
//                 pose.p.x += origin.x;
//                 pose.p.y += origin.y;
//                 pose.p.z += origin.z;

//                 body->setGlobalPose(pose);
//             }

//             if (flags & kDcStateVel)
//             {
//                 body->setLinearVelocity(asPxVec3(state.vel.linear));
//                 body->setAngularVelocity(asPxVec3(state.vel.angular));
//             }
//             else
//             {
//                 // zero velocities?
//             }
//         }
//         else
//         {
//             // hmmm
//             return false;
//         }

//         // should we zero link velocities and accelerations in articulation cache?
//     }

//     return true;
// }

// articulation joints

int CARB_ABI DcGetArticulationJointCount(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        return art->numJoints();
    }
    return 0;
}

DcHandle CARB_ABI DcGetArticulationJoint(DcHandle artHandle, int jointIdx)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        if (jointIdx >= 0 && jointIdx < art->numJoints())
        {
            return art->joints[jointIdx]->handle;
        }
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcFindArticulationJoint(DcHandle artHandle, const char* jointName)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && jointName)
    {
        auto it = art->jointMap.find(jointName);
        if (it != art->jointMap.end())
        {
            return it->second->handle;
        }
    }
    return kDcInvalidHandle;
}

// articulation batch dofs

bool CARB_ABI DcGetDofProperties(DcHandle dofHandle, DcDofProperties* props);
bool CARB_ABI DcSetDofProperties(DcHandle dofHandle, const DcDofProperties* props);
bool CARB_ABI DcSetDofPositionTarget(DcHandle dofHandle, float target);
bool CARB_ABI DcSetDofVelocityTarget(DcHandle dofHandle, float target);
float CARB_ABI DcGetDofPositionTarget(DcHandle dofHandle);
float CARB_ABI DcGetDofVelocityTarget(DcHandle dofHandle);

int CARB_ABI DcGetArticulationDofCount(DcHandle artHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        return art->numDofs();
    }
    return 0;
}

DcHandle CARB_ABI DcGetArticulationDof(DcHandle artHandle, int dofIdx)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art)
    {
        if (dofIdx >= 0 && dofIdx < art->numDofs())
        {
            return art->dofs[dofIdx]->handle;
        }
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcFindArticulationDof(DcHandle artHandle, const char* dofName)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && dofName)
    {
        auto it = art->dofMap.find(dofName);
        if (it != art->dofMap.end())
        {
            return it->second->handle;
        }
    }
    return kDcInvalidHandle;
}

int CARB_ABI DcFindArticulationDofIndex(DcHandle artHandle, const char* dofName)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (art && dofName)
    {
        int numDofs = int(art->dofs.size());
        for (int i = 0; i < numDofs; i++)
        {
            if (art->dofs[i]->name == dofName)
            {
                return i;
            }
        }
    }
    return -1;
}

bool CARB_ABI DcGetArticulationDofProperties(DcHandle artHandle, DcDofProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !props)
    {
        return false;
    }

    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        auto dof = art->dofs[i];
        if (!DcGetDofProperties(dof->handle, &props[i]))
        {
            return false;
        }
    }

    return true;
}

bool CARB_ABI DcSetArticulationDofProperties(DcHandle artHandle, const DcDofProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !props)
    {
        return false;
    }

    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        auto dof = art->dofs[i];
        if (!DcSetDofProperties(dof->handle, &props[i]))
        {
            return false;
        }
    }

    return true;
}

DcDofState* CARB_ABI DcGetArticulationDofStates(DcHandle artHandle, DcStateFlags flags)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art)
    {
        return nullptr;
    }

    if (!art->refreshCache())
    {
        return nullptr;
    }
    // if effors are requested, make sure the joint force flag is set of the articulation
    if (flags & kDcStateEffort)
    {
        if (!(art->pxArticulation->getArticulationFlags() & PxArticulationFlag::eCOMPUTE_JOINT_FORCES))
        {
            art->pxArticulation->setArticulationFlag(PxArticulationFlag::eCOMPUTE_JOINT_FORCES, true);
            // Zero cache if this was the first frame we set this flag.
            ZeroArray(art->pxArticulationCache->jointSolverForces, art->pxArticulation->getDofs());
        }
    }
    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        if (flags & kDcStatePos)
        {
            art->dofStateCache[i].pos = art->pxArticulationCache->jointPosition[art->dofs[i]->cacheIdx];
        }
        if (flags & kDcStateVel)
        {
            art->dofStateCache[i].vel = art->pxArticulationCache->jointVelocity[art->dofs[i]->cacheIdx];
        }
        if (flags & kDcStateEffort)
        {
            art->dofStateCache[i].effort = art->pxArticulationCache->jointSolverForces[art->dofs[i]->cacheIdx];
        }
    }

    return art->dofStateCache.data();
}

DcDofState* CARB_ABI DcGetArticulationDofStateDerivatives(DcHandle artHandle, const DcDofState* states, const float* efforts)
{

    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art)
    {
        return nullptr;
    }

    // make sure the articulation cache was created
    if (!art->pxArticulationCache)
    {
        art->pxArticulationCache = art->pxArticulation->createCache();
        if (!art->pxArticulationCache)
        {
            return nullptr;
        }
    }

    // TODO (preist@): Make input states optional and return derivative for current articulation state

    // write provided states and inputs to cache
    const int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        const int LLInd = art->dofs[i]->cacheIdx;
        art->pxArticulationCache->jointPosition[LLInd] = states[i].pos;
        art->pxArticulationCache->jointVelocity[LLInd] = states[i].vel;
        art->pxArticulationCache->jointForce[LLInd] = efforts[i];
    }

    // calculate accelerations in cache
    art->pxArticulation->applyCache(*(art->pxArticulationCache), PxArticulationCacheFlag::eFORCE |
                                                                     PxArticulationCacheFlag::ePOSITION |
                                                                     PxArticulationCacheFlag::eVELOCITY);
    art->pxArticulation->commonInit();
    art->pxArticulation->computeJointAcceleration(*(art->pxArticulationCache));

    // extract derivatives and put them in state cache for access:
    for (int i = 0; i < numDofs; i++)
    {
        const int LLInd = art->dofs[i]->cacheIdx;
        art->dofStateCache[i].pos = art->pxArticulationCache->jointVelocity[LLInd];
        art->dofStateCache[i].vel = art->pxArticulationCache->jointAcceleration[LLInd];
        art->dofStateCache[i].effort = 0; // art->pxArticulationCache->jointSolverForces[LLInd];
    }

    return art->dofStateCache.data();
}

bool CARB_ABI DcSetArticulationDofStates(DcHandle artHandle, const DcDofState* states, DcStateFlags flags)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !flags)
    {
        return false;
    }

    if (!art->refreshCache())
    {
        return false;
    }

    int numDofs = art->numDofs();
    PxArticulationCacheFlags pxFlags = PxArticulationCacheFlags(0);

    /*
    printf("Setting:");
    for (int i = 0; i < numDofs; i++)
    {
        printf(" %f", states[i].pos);
    }
    printf("\n");
    */

    // art->pxArticulation->zeroCache(*art->pxArticulationCache);

    if (flags & kDcStatePos)
    {
        pxFlags |= PxArticulationCacheFlag::ePOSITION;
        for (int i = 0; i < numDofs; i++)
        {
            int dofIndex = art->dofs[i]->cacheIdx;
            // printf(" ~ Setting %d %d %f\n", i, dofIndex, states[i].pos);
            art->pxArticulationCache->jointPosition[dofIndex] = states[i].pos;
        }
    }

    if (flags & kDcStateVel)
    {
        pxFlags |= PxArticulationCacheFlag::eVELOCITY;
        for (int i = 0; i < numDofs; i++)
        {
            art->pxArticulationCache->jointVelocity[art->dofs[i]->cacheIdx] = states[i].vel;
        }
    }
    else
    {
        // ZeroArray(art->pxArticulationCache->jointVelocity, art->pxArticulation->getDofs());
    }

    ZeroArray(art->pxArticulationCache->jointForce, art->pxArticulation->getDofs());
    ZeroArray(art->pxArticulationCache->jointAcceleration, art->pxArticulation->getDofs());

    ZeroArray(art->pxArticulationCache->linkVelocity, art->pxArticulation->getNbLinks());
    ZeroArray(art->pxArticulationCache->linkAcceleration, art->pxArticulation->getNbLinks());

    // art->pxArticulation->applyCache(*art->pxArticulationCache, pxFlags);
    art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eALL); // hmmm

    /*
    auto result = DcGetArticulationDofStates(art, kDcStatePos);
    printf("Result:");
    for (int i = 0; i < numDofs; i++)
    {
        printf(" %f", result[i].pos);
    }
    printf("\n");
    printf("\n");
    */

    return true;
}

bool CARB_ABI DcSetArticulationDofPositionTargets(DcHandle artHandle, const float* targets)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !targets)
    {
        return false;
    }

    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        DcSetDofPositionTarget(art->dofs[i]->handle, targets[i]);
    }

    return true;
}

bool CARB_ABI DcSetArticulationDofVelocityTargets(DcHandle artHandle, const float* targets)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !targets)
    {
        return false;
    }

    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        DcSetDofVelocityTarget(art->dofs[i]->handle, targets[i]);
    }

    return true;
}

bool CARB_ABI DcApplyArticulationDofEfforts(DcHandle artHandle, const float* efforts)
{
    (void)DC_CHECK_SIMULATING();

    DcArticulation* art = DC_LOOKUP_ARTICULATION(artHandle);
    if (!art || !efforts)
    {
        return false;
    }

    if (!art->refreshCache())
    {
        return false;
    }

    // clear forces
    memset(art->pxArticulationCache->jointForce, 0,
           art->pxArticulation->getDofs() * sizeof(*art->pxArticulationCache->jointForce));

    int numDofs = art->numDofs();
    for (int i = 0; i < numDofs; i++)
    {
        auto dof = art->dofs[i];
        // if (dof->driveMode == DcDriveMode::eEffort)
        {
            art->pxArticulationCache->jointForce[dof->cacheIdx] = efforts[i];
        }
    }

    // apply forces
    art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eFORCE);

    return true;
}


// rigid bodies

const char* CARB_ABI DcGetRigidBodyName(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body)
    {
        return body->name.c_str();
    }
    return nullptr;
}

const char* CARB_ABI DcGetRigidBodyPath(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body)
    {
        return body->path.GetString().c_str();
    }
    return nullptr;
}

DcHandle CARB_ABI DcGetRigidBodyParentJoint(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body)
    {
        return body->parentJoint;
    }
    return kDcInvalidHandle;
}

int CARB_ABI DcGetRigidBodyChildJointCount(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body)
    {
        return int(body->childJoints.size());
    }
    return 0;
}

DcHandle CARB_ABI DcGetRigidBodyChildJoint(DcHandle bodyHandle, int jointIdx)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && jointIdx >= 0 && jointIdx < int(body->childJoints.size()))
    {
        return body->childJoints[jointIdx];
    }
    return kDcInvalidHandle;
}

DcTransform CARB_ABI DcGetRigidBodyPose(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        DcTransform pose = asDcTransform(body->pxRigidBody->getGlobalPose());

        // apply offset
        carb::Float3& origin = body->origin;
        pose.p.x -= origin.x;
        pose.p.y -= origin.y;
        pose.p.z -= origin.z;

        return pose;
    }
    return kTransformIdentity;
}

carb::Float3 CARB_ABI DcGetRigidBodyLinearVelocity(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        return asFloat3(body->pxRigidBody->getLinearVelocity());
    }
    return kFloat3Zero;
}

carb::Float3 CARB_ABI DcGetRigidBodyLocalLinearVelocity(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        PxTransform pose = body->pxRigidBody->getGlobalPose();
        PxVec3 vel = body->pxRigidBody->getLinearVelocity();

        return carb::Float3{ vel.dot(pose.q.rotate(PxVec3(1, 0, 0))), vel.dot(pose.q.rotate(PxVec3(0, 1, 0))),
                             vel.dot(pose.q.rotate(PxVec3(0, 0, 1))) };
    }
    return kFloat3Zero;
}

carb::Float3 CARB_ABI DcGetRigidBodyAngularVelocity(DcHandle bodyHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        return asFloat3(body->pxRigidBody->getAngularVelocity());
    }
    return kFloat3Zero;
}

void CARB_ABI DcSetRigidBodyPose(DcHandle bodyHandle, const DcTransform& pose)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        PxTransform tx = asPxTransform(pose);

        // apply offset
        carb::Float3& origin = body->origin;
        tx.p.x += origin.x;
        tx.p.y += origin.y;
        tx.p.z += origin.z;

        if (body->art)
        {
            if (body->art->rigidBodies[0]->handle != bodyHandle)
            {
                CARB_LOG_ERROR("Cannot set pose on non-root articulation link");
                return;
            }
            else
            {
                // its a root link
                body->art->pxArticulation->copyInternalStateToCache(
                    *body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);

                body->art->pxArticulationCache->rootLinkData->transform = tx;
                body->art->pxArticulation->applyCache(*body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);

                return;
            }
        }
        body->pxRigidBody->setGlobalPose(tx);
    }
}

void CARB_ABI DcSetRigidBodyDisableGravity(DcHandle bodyHandle, const bool disableGravity)
{

    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        body->pxRigidBody->setActorFlag(PxActorFlag::eDISABLE_GRAVITY, disableGravity);
    }
}

void CARB_ABI DcSetRigidBodyDisableSimulation(DcHandle bodyHandle, const bool disableSimualation)
{

    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        body->pxRigidBody->setActorFlag(PxActorFlag::eDISABLE_SIMULATION, disableSimualation);
    }
}


void CARB_ABI DcSetRigidBodyLinearVelocity(DcHandle bodyHandle, const carb::Float3& linvel)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        // This is a link but not the root link
        if (body->art)
        {
            if (body->art->rigidBodies[0]->handle != bodyHandle)
            {
                CARB_LOG_ERROR("Cannot set linear velocity on non-root articulation link");
                return;
            }
            else
            {
                // its a root link
                body->art->pxArticulation->copyInternalStateToCache(
                    *body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);

                body->art->pxArticulationCache->rootLinkData->worldLinVel = asPxVec3(linvel);
                body->art->pxArticulation->applyCache(*body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);
                return;
            }
        }
        PxRigidDynamic* dynamicBody = static_cast<PxRigidDynamic*>(body->pxRigidBody);
        if (dynamicBody)
        {
            dynamicBody->setLinearVelocity(asPxVec3(linvel));
        }
        else
        {
            CARB_LOG_ERROR("Not a dynamic rigid body or a root articulation link");
        }
    }
}

void CARB_ABI DcSetRigidBodyAngularVelocity(DcHandle bodyHandle, const carb::Float3& angvel)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body && body->pxRigidBody)
    {
        if (body->art)
        {
            if (body->art->rigidBodies[0]->handle != bodyHandle)
            {
                CARB_LOG_ERROR("Cannot set angular velocity on non-root articulation link");
                return;
            }
            else
            {
                // its a root link
                body->art->pxArticulation->copyInternalStateToCache(
                    *body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);

                body->art->pxArticulationCache->rootLinkData->worldAngVel = asPxVec3(angvel);
                body->art->pxArticulation->applyCache(*body->art->pxArticulationCache, PxArticulationCacheFlag::eALL);
                return;
            }
        }
        PxRigidDynamic* dynamicBody = static_cast<PxRigidDynamic*>(body->pxRigidBody);

        if (dynamicBody)
        {
            dynamicBody->setAngularVelocity(asPxVec3(angvel));
        }
        else
        {
            CARB_LOG_ERROR("Not a dynamic rigid body or a root articulation link");
        }
    }
}

void CARB_ABI DcApplyBodyForce(DcHandle bodyHandle, const carb::Float3& force, const carb::Float3& pos)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (!body || !body->pxRigidBody)
    {
        CARB_LOG_ERROR("Invalid body");
        return;
    }

    if (!body->pxRigidBody->getScene())
    {
        CARB_LOG_ERROR("Body not in simulation scene");
        return;
    }

    // FIXME
    body->pxRigidBody->addForce((const PxVec3&)force);
}

void CARB_ABI DcGetRelativeBodyPoses(DcHandle parentHandle,
                                     const size_t numBodies,
                                     const DcHandle* bodyHandles,
                                     DcTransform* bodyTransforms)
{
    (void)DC_CHECK_SIMULATING();
    DcRigidBody* parent = DC_LOOKUP_RIGID_BODY(parentHandle);
    if (parent && parent->pxRigidBody)
    {
        PxTransform P = parent->pxRigidBody->getGlobalPose();
        for (size_t i = 0; i < numBodies; i++)
        {
            if (bodyHandles[i] == kDcInvalidHandle)
            {
                bodyTransforms[i] = DcTransform();
                continue;
            }
            DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandles[i]);
            if (body && body->pxRigidBody)
            {
                bodyTransforms[i] = asDcTransform(P.transformInv(body->pxRigidBody->getGlobalPose()));
            }
            else
            {
                bodyTransforms[i] = DcTransform();
            }
        }
    }
}

bool CARB_ABI DcGetRigidBodyProperties(DcHandle bodyHandle, DcRigidBodyProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(bodyHandle);
    if (body)
    {
        PxRigidBody* pxBody = body->pxRigidBody;

        props->mass = pxBody->getMass();
        props->moment = asFloat3(pxBody->getMassSpaceInertiaTensor());
        return true;
    }
    return false;
}

//
// joints
//

const char* CARB_ABI DcGetJointName(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return joint->name.c_str();
    }
    return nullptr;
}

const char* CARB_ABI DcGetJointPath(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return joint->path.GetString().c_str();
    }
    return nullptr;
}

DcJointType CARB_ABI DcGetJointType(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return joint->type;
    }
    return DcJointType::eNone;
}

int CARB_ABI DcGetJointDofCount(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return int(joint->dofs.size());
    }
    return 0;
}

DcHandle CARB_ABI DcGetJointDof(DcHandle jointHandle, int dofIdx)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint && dofIdx >= 0 && dofIdx < int(joint->dofs.size()))
    {
        return joint->dofs[dofIdx];
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcGetJointParentBody(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return joint->parentBody;
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcGetJointChildBody(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcJoint* joint = DC_LOOKUP_JOINT(jointHandle);
    if (joint)
    {
        return joint->childBody;
    }
    return kDcInvalidHandle;
}


//
// dofs
//

const char* CARB_ABI DcGetDofName(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        return dof->name.c_str();
    }
    return nullptr;
}

const char* CARB_ABI DcGetDofPath(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        return dof->path.GetString().c_str();
    }
    return nullptr;
}

DcDofType CARB_ABI DcGetDofType(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        return dof->type;
    }
    return DcDofType::eNone;
}

DcHandle CARB_ABI DcGetDofJoint(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        return dof->joint;
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcGetDofParentBody(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        DcJoint* joint = DC_LOOKUP_JOINT(dof->joint);
        if (joint)
        {
            return joint->parentBody;
        }
    }
    return kDcInvalidHandle;
}

DcHandle CARB_ABI DcGetDofChildBody(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof)
    {
        DcJoint* joint = DC_LOOKUP_JOINT(dof->joint);
        if (joint)
        {
            return joint->childBody;
        }
    }
    return kDcInvalidHandle;
}

DcDofState CARB_ABI DcGetDofState(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDofState state{};

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art)
    {
        if (dof->art->refreshCache())
        {
            state.pos = dof->art->pxArticulationCache->jointPosition[dof->cacheIdx];
            state.vel = dof->art->pxArticulationCache->jointVelocity[dof->cacheIdx];
        }
    }

    return state;
}

bool CARB_ABI DcSetDofState(DcHandle dofHandle, const DcDofState* state)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art && state)
    {
        DcArticulation* art = dof->art;
        if (art->refreshCache())
        {
            art->pxArticulationCache->jointPosition[dof->cacheIdx] = state->pos;
            art->pxArticulationCache->jointVelocity[dof->cacheIdx] = state->vel;
#if 0
            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::ePOSITION | PxArticulationCacheFlag::eVELOCITY);
#else
            ZeroArray(art->pxArticulationCache->jointForce, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->jointAcceleration, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->linkVelocity, art->pxArticulation->getNbLinks());
            ZeroArray(art->pxArticulationCache->linkAcceleration, art->pxArticulation->getNbLinks());

            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eALL);
#endif
            return true;
        }
    }
    return false;
}

float CARB_ABI DcGetDofPosition(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art)
    {
        if (dof->art->refreshCache())
        {
            return dof->art->pxArticulationCache->jointPosition[dof->cacheIdx];
        }
    }
    return 0.0f;
}

bool CARB_ABI DcSetDofPosition(DcHandle dofHandle, float pos)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art)
    {
        DcArticulation* art = dof->art;
        if (art->refreshCache())
        {
            art->pxArticulationCache->jointPosition[dof->cacheIdx] = pos;
#if 0
            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::ePOSITION);
#else
            ZeroArray(art->pxArticulationCache->jointForce, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->jointAcceleration, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->linkVelocity, art->pxArticulation->getNbLinks());
            ZeroArray(art->pxArticulationCache->linkAcceleration, art->pxArticulation->getNbLinks());

            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eALL);
#endif
            return true;
        }
    }
    return false;
}

float CARB_ABI DcGetDofVelocity(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art)
    {
        if (dof->art->refreshCache())
        {
            return dof->art->pxArticulationCache->jointVelocity[dof->cacheIdx];
        }
    }
    return 0.0f;
}

bool CARB_ABI DcSetDofVelocity(DcHandle dofHandle, float vel)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (dof && dof->art)
    {
        DcArticulation* art = dof->art;
        if (art->refreshCache())
        {
            art->pxArticulationCache->jointVelocity[dof->cacheIdx] = vel;
#if 0
            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eVELOCITY);
#else
            ZeroArray(art->pxArticulationCache->jointForce, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->jointAcceleration, art->pxArticulation->getDofs());
            ZeroArray(art->pxArticulationCache->linkVelocity, art->pxArticulation->getNbLinks());
            ZeroArray(art->pxArticulationCache->linkAcceleration, art->pxArticulation->getNbLinks());

            art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eALL);
#endif
            return true;
        }
    }
    return false;
}

bool CARB_ABI DcGetDofProperties(DcHandle dofHandle, DcDofProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !props)
    {
        return false;
    }

    auto pxJoint = dof->pxArticulationJoint;
    if (!pxJoint)
    {
        return false;
    }

    // dof type
    props->type = dof->type;

    // get limits
    PxArticulationMotion::Enum motion = pxJoint->getMotion(dof->pxAxis);
    if (motion == PxArticulationMotion::eLIMITED)
    {
        props->hasLimits = true;
        pxJoint->getLimit(dof->pxAxis, props->lower, props->upper);
    }

    // get stiffness, damping, and maxEffort
    PxArticulationDriveType::Enum driveType;
    pxJoint->getDrive(dof->pxAxis, props->stiffness, props->damping, props->maxEffort, driveType);

    // get the max joint velocity.
    props->maxVelocity = pxJoint->getMaxJointVelocity();

    // cached drive mode
    // HMMM... should we take the actual driveType into account?
    props->driveMode = dof->driveMode;

    return true;
}

bool CARB_ABI DcSetDofProperties(DcHandle dofHandle, const DcDofProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !props)
    {
        return false;
    }

    auto pxJoint = dof->pxArticulationJoint;
    if (!pxJoint)
    {
        return false;
    }

    // if (dof->art->pxArticulation->getScene())
    // {
    //     dof->art->pxArticulation->wakeUp();
    // }

    // Remove articulation from scene
    ::physx::PxScene* scene = dof->art->pxArticulation->getScene();
    if (scene)
    {
        scene->removeArticulation(*dof->art->pxArticulation);
    }

    // set limits
    if (props->hasLimits)
    {
        pxJoint->setMotion(dof->pxAxis, PxArticulationMotion::eLIMITED);
        pxJoint->setLimit(dof->pxAxis, props->lower, props->upper);
    }
    else
    {
        pxJoint->setMotion(dof->pxAxis, PxArticulationMotion::eFREE);
    }

    float stiffness = props->stiffness;
    float damping = props->damping;

    // save drive mode
    dof->driveMode = props->driveMode;

    PxArticulationDriveType::Enum driveType;
    switch (props->driveMode)
    {
    case DcDriveMode::ePositionTarget:
        // driveType = PxArticulationDriveType::eTARGET;
        driveType = PxArticulationDriveType::eFORCE;
        break;
    case DcDriveMode::eVelocityTarget:
        // driveType = PxArticulationDriveType::eVELOCITY;
        driveType = PxArticulationDriveType::eFORCE;
        stiffness = 0.0f;
        break;
        // case DcDriveMode::eEffort:
    case DcDriveMode::eNone:
    default:
        driveType = PxArticulationDriveType::eNONE;
        break;
    }

    // set drive properties
    pxJoint->setDrive(dof->pxAxis, stiffness, damping, props->maxEffort, driveType);


    // Add articulation back to scene
    if (scene)
    {
        scene->addArticulation(*dof->art->pxArticulation);
    }

    // if (dof->art->pxArticulation->getScene())
    // {
    //     // Cache becomes invalid, clear it
    //     dof->art->pxArticulation->releaseCache(*dof->art->pxArticulationCache);
    //     dof->art->pxArticulationCache = dof->art->pxArticulation->createCache();
    // }
    return true;
}

bool CARB_ABI DcSetDofPositionTarget(DcHandle dofHandle, float target)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !dof->pxArticulationJoint)
    {
        return false;
    }

    if (dof->driveMode == DcDriveMode::ePositionTarget)
    {
        dof->pxArticulationJoint->setDriveTarget(dof->pxAxis, target);
    }

    return true;
}

bool CARB_ABI DcSetDofVelocityTarget(DcHandle dofHandle, float target)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !dof->pxArticulationJoint)
    {
        return false;
    }

    if (dof->driveMode == DcDriveMode::eVelocityTarget)
    {
        dof->pxArticulationJoint->setDriveVelocity(dof->pxAxis, target);
    }

    return true;
}

float CARB_ABI DcGetDofPositionTarget(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !dof->pxArticulationJoint)
    {
        return false;
    }

    if (dof->driveMode == DcDriveMode::ePositionTarget)
    {
        return dof->pxArticulationJoint->getDriveTarget(dof->pxAxis);
    }

    return 0;
}

float CARB_ABI DcGetDofVelocityTarget(DcHandle dofHandle)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !dof->pxArticulationJoint)
    {
        return false;
    }

    if (dof->driveMode == DcDriveMode::eVelocityTarget)
    {
        return dof->pxArticulationJoint->getDriveVelocity(dof->pxAxis);
    }

    return 0;
}

bool CARB_ABI DcApplyDofEffort(DcHandle dofHandle, float effort)
{
    (void)DC_CHECK_SIMULATING();

    DcDof* dof = DC_LOOKUP_DOF(dofHandle);
    if (!dof || !dof->art)
    {
        return false;
    }

    DcArticulation* art = dof->art;
    if (!art->refreshCache())
    {
        return false;
    }

    // Calling this method for individual dofs is not very efficient,
    // since it uses the full parent articulation cache each time.
    // Prefer DcApplyArticulationDofEfforts for multiple DOF efforts.

    // clear forces
    memset(art->pxArticulationCache->jointForce, 0,
           art->pxArticulation->getDofs() * sizeof(*art->pxArticulationCache->jointForce));

    art->pxArticulationCache->jointForce[dof->cacheIdx] = effort;

    // apply forces
    art->pxArticulation->applyCache(*art->pxArticulationCache, PxArticulationCacheFlag::eFORCE);

    return true;
}

//
// attractors
//

bool setAttractorProperties(DcAttractor* attractor, const DcAttractorProperties* props);

DcHandle CARB_ABI DcCreateRigidBodyAttractor(const DcAttractorProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return kDcInvalidHandle;
    }

    if (!props)
    {
        return kDcInvalidHandle;
    }

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(props->rigidBody);
    if (!body || !body->pxRigidBody)
    {
        return kDcInvalidHandle;
    }

    PxRigidBody* pxBody = body->pxRigidBody;

    if (!pxBody->getScene())
    {
        CARB_LOG_ERROR("Failed to create attractor: body not in scene");
        return kDcInvalidHandle;
    }

    SdfPath attractorPath("/attractor" + std::to_string(ctx->numAttractors()));

#if 0
    // this won't work, because PxGetFoundation returns nullptr
    PxTransform targetTransform = asPxTransform(props->target);
    PxTransform offsetTransform = asPxTransform(props->offset);
    PxPhysics& physics = body->getScene()->getPhysics();
    PxD6Joint* joint = PxD6JointCreate(physics, nullptr, targetTransform, body, offsetTransform);
#else
    size_t targetId = (size_t)pxBody->userData;
    SdfPath targetPath = ctx->physx->getPhysXObjectUsdPath(targetId);
    PxD6Joint* joint = (PxD6Joint*)ctx->physx->createD6JointAtPath(attractorPath, SdfPath(), targetPath);
#endif
    if (!joint)
    {
        CARB_LOG_ERROR("Failed to create attractor joint");
        return kDcInvalidHandle;
    }

    std::unique_ptr<DcAttractor> attractor = std::make_unique<DcAttractor>();
    attractor->path = attractorPath;
    attractor->pxJoint = joint;

    if (!setAttractorProperties(attractor.get(), props))
    {
        CARB_LOG_ERROR("Failed to set attractor properties");
        joint->release();
        return kDcInvalidHandle;
    }

    DcAttractor* attPtr = attractor.get();
    DcHandle attHandle = ctx->addAttractor(std::move(attractor), attractorPath);
    attPtr->handle = attHandle;

    return attHandle;
}

bool CARB_ABI DcSetAttractorProperties(DcHandle attHandle, const DcAttractorProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    return setAttractorProperties(DC_LOOKUP_ATTRACTOR(attHandle), props);
}

bool setAttractorProperties(DcAttractor* attractor, const DcAttractorProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    if (!attractor || !props)
    {
        return false;
    }

    // motion and drive

    // Either both swing axes are set, or neither are
    if (((props->axes & kDcAxisSwing1) ^ (props->axes & kDcAxisSwing1)))
    {
        CARB_LOG_ERROR("Invalid attractor swing axes configuration");
        return false;
    }

    DcRigidBody* body = DC_LOOKUP_RIGID_BODY(props->rigidBody);
    if (!body || !body->pxRigidBody)
    {
        CARB_LOG_ERROR("Invalid rigid body for attractor");
        return false;
    }

    PxD6Joint* joint = attractor->pxJoint;
    if (!joint)
    {
        CARB_LOG_ERROR("Attractor is missing physics joint");
        return false;
    }

    DcWakeUpRigidBody(props->rigidBody);

    /*
    PxRigidBody* body = props->rigidBody->pxRigidBody;
    if (props->rigidBody->art)
    {
    props->rigidBody->art->pxArticulation->wakeUp();
    }
    */

    PxTransform targetTransform = asPxTransform(props->target);
    PxTransform offsetTransform = asPxTransform(props->offset);

    // auto& t = targetTransform;
    // auto& o = offsetTransform;
    // printf("Setting target (%f, %f, %f) (%f, %f, %f, %f)\n", t.p.x, t.p.y, t.p.z, t.q.x, t.q.y, t.q.z, t.q.w);
    // printf("Setting offset (%f, %f, %f) (%f, %f, %f, %f)\n", o.p.x, o.p.y, o.p.z, o.q.x, o.q.y, o.q.z, o.q.w);

    joint->setActors(nullptr, body->pxRigidBody);

    joint->setLocalPose(PxJointActorIndex::eACTOR0, targetTransform);
    joint->setLocalPose(PxJointActorIndex::eACTOR1, offsetTransform);

    PxD6JointDrive drive(props->stiffness, props->damping, props->forceLimit, false);
    PxD6JointDrive defaultDrive;

    // Make all axes free
    for (int i = 0; i < 6; ++i)
    {
        joint->setMotion(g_dcToPxAxis[i], PxD6Motion::eFREE);
    }

    // Set linear drive
    for (int i = 0; i < 3; ++i)
    {
        if ((props->axes >> i) & 1)
        {
            joint->setDrive((PxD6Drive::Enum)i, drive);
        }
        else
        {
            joint->setDrive((PxD6Drive::Enum)i, defaultDrive);
        }
    }

    // All rotation axes are set
    if ((props->axes & kDcAxisAllRotation) == kDcAxisAllRotation)
    {
        joint->setDrive(PxD6Drive::eSWING, defaultDrive);
        joint->setDrive(PxD6Drive::eTWIST, defaultDrive);
        joint->setDrive(PxD6Drive::eSLERP, drive);
    }

    // Only swing axes are set
    else if ((props->axes & kDcAxisSwing1) && (props->axes & kDcAxisSwing2))
    {
        joint->setDrive(PxD6Drive::eTWIST, defaultDrive);
        joint->setDrive(PxD6Drive::eSLERP, defaultDrive);
        joint->setDrive(PxD6Drive::eSWING, drive);
    }

    // Only twist is set
    else if (props->axes & kDcAxisTwist)
    {
        joint->setDrive(PxD6Drive::eSWING, defaultDrive);
        joint->setDrive(PxD6Drive::eSLERP, defaultDrive);
        joint->setDrive(PxD6Drive::eTWIST, drive);
    }

    joint->setDrivePosition(PxTransform(PxIDENTITY()));

    // save props
    attractor->props = *props;

    return true;
}

bool CARB_ABI DcSetAttractorTarget(DcHandle attHandle, const DcTransform& target)
{
    (void)DC_CHECK_SIMULATING();

    DcAttractor* attractor = DC_LOOKUP_ATTRACTOR(attHandle);
    if (!attractor)
    {
        return false;
    }

    PxD6Joint* joint = attractor->pxJoint;
    if (!joint)
    {
        CARB_LOG_ERROR("Attractor is missing physics joint");
        return false;
    }

    DcWakeUpRigidBody(attractor->props.rigidBody);

    PxTransform targetTransform = asPxTransform(target);

    joint->setLocalPose(PxJointActorIndex::eACTOR0, targetTransform);

    // save target
    attractor->props.target = target;

    return true;
}

bool CARB_ABI DcGetAttractorProperties(DcHandle attHandle, DcAttractorProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcAttractor* attractor = DC_LOOKUP_ATTRACTOR(attHandle);
    if (!attractor || !props)
    {
        return false;
    }

    *props = attractor->props;

    return true;
}

void CARB_ABI DcDestroyRigidBodyAttractor(DcHandle attHandle)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return;
    }

    DcAttractor* attractor = DC_LOOKUP_ATTRACTOR(attHandle);
    if (!attractor || !attractor->pxJoint)
    {
        return;
    }

    ctx->physx->releaseD6Joint(attractor->pxJoint);

    ctx->removeAttractor(attHandle);
}


//
// D6 Joints
//

bool setD6JointProperties(DcD6Joint* dcJoint, const DcD6JointProperties* props);
bool getD6JointConstraintIsBroken(DcD6Joint* dcJoint);


DcHandle CARB_ABI DcCreateD6Joint(const DcD6JointProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return kDcInvalidHandle;
    }

    if (!props)
    {
        return kDcInvalidHandle;
    }

    PxRigidBody* pxBody0 = nullptr;
    PxRigidBody* pxBody1 = nullptr;
    if (props->body0 != kDcInvalidHandle)
    {
        DcRigidBody* body0 = DC_LOOKUP_RIGID_BODY(props->body0);
        if (!body0 || !body0->pxRigidBody)
        {
            CARB_LOG_ERROR("Failed to create Joint: body 0 handle is invalid");
            return kDcInvalidHandle;
        }
        pxBody0 = body0->pxRigidBody;
        if (!pxBody0->getScene())
        {
            CARB_LOG_ERROR("Failed to create Joint: body 0 not in scene");
            return kDcInvalidHandle;
        }
        DcWakeUpRigidBody(props->body0);
    }
    if (props->body1 != kDcInvalidHandle)
    {
        DcRigidBody* body1 = DC_LOOKUP_RIGID_BODY(props->body1);
        if (!body1 || !body1->pxRigidBody)
        {
            CARB_LOG_ERROR("Failed to create Joint: body 1 handle is invalid");
            return kDcInvalidHandle;
        }
        pxBody1 = body1->pxRigidBody;
        if (!pxBody1->getScene())
        {
            CARB_LOG_ERROR("Failed to create Joint: body 1 not in scene");
            return kDcInvalidHandle;
        }
        DcWakeUpRigidBody(props->body1);
    }
    std::string jointName = "/joint_" + std::to_string(ctx->numD6Joints());
    SdfPath jointPath;
    if (props->name != nullptr)
    {
        jointName = std::string(props->name);
    }
    jointPath = SdfPath(jointName);


    size_t originId = (size_t)pxBody0->userData;
    SdfPath originPath(ctx->physx->getPhysXObjectUsdPath(originId));
    SdfPath targetPath;
    if (pxBody1)
        targetPath = ctx->physx->getPhysXObjectUsdPath((size_t)pxBody1->userData);


    PxD6Joint* joint = (PxD6Joint*)ctx->physx->createD6JointAtPath(jointPath, originPath, targetPath);
    if (!joint)
    {
        CARB_LOG_ERROR("Failed to create D6 joint");
        return kDcInvalidHandle;
    }

    std::unique_ptr<DcD6Joint> dcJoint = std::make_unique<DcD6Joint>();
    dcJoint->path = jointPath;
    dcJoint->pxJoint = joint;

    if (!setD6JointProperties(dcJoint.get(), props))
    {
        CARB_LOG_ERROR("Failed to set Joint properties");
        joint->release();
        return kDcInvalidHandle;
    }

    DcD6Joint* j_Ptr = dcJoint.get();
    DcHandle j_handle = ctx->addD6Joint(std::move(dcJoint), jointPath);
    j_Ptr->handle = j_handle;
    return j_handle;
}

void CARB_ABI DcDestroyD6Joint(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return;
    }

    DcD6Joint* joint = DC_LOOKUP_D6JOINT(jointHandle);
    if (!joint || !joint->pxJoint)
    {
        return;
    }

    ctx->physx->releaseD6Joint(joint->pxJoint);

    ctx->removeD6Joint(jointHandle);
}

bool CARB_ABI DcGetD6JointProperties(DcHandle jointHandle, DcD6JointProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    DcD6Joint* joint = DC_LOOKUP_D6JOINT(jointHandle);
    if (!joint || !props)
    {
        return false;
    }

    *props = joint->props;

    return true;
}

bool CARB_ABI DcGetD6JointConstraintIsBroken(DcHandle jointHandle)
{
    (void)DC_CHECK_SIMULATING();

    return getD6JointConstraintIsBroken(DC_LOOKUP_D6JOINT(jointHandle));
}

bool CARB_ABI DcSetD6JointProperties(DcHandle jointHandle, const DcD6JointProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    return setD6JointProperties(DC_LOOKUP_D6JOINT(jointHandle), props);
}

bool CARB_ABI DcSetOriginOffset(DcHandle handle, const carb::Float3& origin)
{
    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return false;
    }

    DcArticulation* art = ctx->getArticulation(handle);
    if (art)
    {
        for (int i = 0; i < art->numRigidBodies(); i++)
        {
            art->rigidBodies[i]->origin = origin;
        }
        return true;
    }

    DcRigidBody* body = ctx->getRigidBody(handle);
    if (body)
    {
        body->origin = origin;
        return true;
    }

    // TODO: attractors

    return false;
}

bool setD6JointProperties(DcD6Joint* dcJoint, const DcD6JointProperties* props)
{
    (void)DC_CHECK_SIMULATING();

    if (!dcJoint || !props)
    {
        return false;
    }

    // motion and drive

    // Either both swing axes are set, or neither are
    if (((props->axes & kDcAxisSwing1) ^ (props->axes & kDcAxisSwing1)))
    {
        CARB_LOG_ERROR("Invalid D6 joint swing axes configuration");
        return false;
    }

    PxD6Joint* joint = dcJoint->pxJoint;
    if (!joint)
    {
        auto& ctx = g_dcCtx;
        if (!ctx)
        {
            return false;
        }
        printf("Refreshing joint %s\n", dcJoint->path.GetString().c_str());
        // Joint was created through DC so it doesn't exist after sim is stopped, re-create
        PxRigidBody* pxBody0 = nullptr;
        PxRigidBody* pxBody1 = nullptr;
        if (dcJoint->props.body0 != kDcInvalidHandle)
        {
            DcRigidBody* body0 = DC_LOOKUP_RIGID_BODY(dcJoint->props.body0);
            if (!body0 || !body0->pxRigidBody)
            {

                CARB_LOG_ERROR("Failed to refresh Joint: body 0 %s at %s handle is invalid", body0->name.c_str(),
                               body0->path.GetString().c_str());

                return kDcInvalidHandle;
            }
            pxBody0 = body0->pxRigidBody;
            if (!pxBody0->getScene())
            {

                CARB_LOG_ERROR("Failed to refresh Joint: body 0 %s at %s not in scene", body0->name.c_str(),
                               body0->path.GetString().c_str());

                return kDcInvalidHandle;
            }
            DcWakeUpRigidBody(dcJoint->props.body0);
        }
        if (dcJoint->props.body1 != kDcInvalidHandle)
        {
            DcRigidBody* body1 = DC_LOOKUP_RIGID_BODY(dcJoint->props.body1);
            if (!body1 || !body1->pxRigidBody)
            {

                CARB_LOG_ERROR("Failed to refresh Joint: body 1 %s at %s handle is invalid", body1->name.c_str(),
                               body1->path.GetString().c_str());

                return kDcInvalidHandle;
            }
            pxBody1 = body1->pxRigidBody;
            if (!pxBody1->getScene())
            {

                CARB_LOG_ERROR("Failed to refresh Joint: body 1 %s at %s not in scene", body1->name.c_str(),
                               body1->path.GetString().c_str());

                return kDcInvalidHandle;
            }
            DcWakeUpRigidBody(dcJoint->props.body1);
        }
        std::string jointName = "/joint_" + std::to_string(ctx->numD6Joints());
        SdfPath jointPath;
        if (dcJoint->props.name != nullptr)
        {
            jointName = std::string(dcJoint->props.name);
        }
        jointPath = SdfPath(jointName);


        size_t originId = (size_t)pxBody0->userData;
        SdfPath originPath(ctx->physx->getPhysXObjectUsdPath(originId));
        SdfPath targetPath;
        if (pxBody1)
            targetPath = ctx->physx->getPhysXObjectUsdPath((size_t)pxBody1->userData);


        dcJoint->pxJoint = (PxD6Joint*)ctx->physx->createD6JointAtPath(jointPath, originPath, targetPath);
        joint = dcJoint->pxJoint;
        printf("Refreshed joint %s\n", dcJoint->path.GetString().c_str());
    }
    PxRigidBody* pxBody0 = nullptr;
    PxRigidBody* pxBody1 = nullptr;
    if (props->body0 != kDcInvalidHandle)
    {
        DcRigidBody* body0 = DC_LOOKUP_RIGID_BODY(props->body0);
        if (!body0 || !body0->pxRigidBody)
        {
            CARB_LOG_ERROR("Failed to create Joint: body 0 handle is invalid");
            return kDcInvalidHandle;
        }
        pxBody0 = body0->pxRigidBody;
        if (!pxBody0->getScene())
        {
            CARB_LOG_ERROR("Failed to create Joint: body 0 not in scene");
            return kDcInvalidHandle;
        }
        DcWakeUpRigidBody(props->body0);
    }
    if (props->body1 != kDcInvalidHandle)
    {
        DcRigidBody* body1 = DC_LOOKUP_RIGID_BODY(props->body1);
        if (!body1 || !body1->pxRigidBody)
        {
            CARB_LOG_ERROR("Failed to create Joint: body 1 handle is invalid");
            return kDcInvalidHandle;
        }
        pxBody1 = body1->pxRigidBody;
        if (!pxBody1->getScene())
        {
            CARB_LOG_ERROR("Failed to create Joint: body 1 not in scene");
            return kDcInvalidHandle;
        }
        DcWakeUpRigidBody(props->body1);
    }


    PxTransform pose0 = asPxTransform(props->pose0);
    PxTransform pose1 = asPxTransform(props->pose1);

    joint->setActors(pxBody0, pxBody1);


    joint->setLocalPose(PxJointActorIndex::eACTOR0, pose0);
    joint->setLocalPose(PxJointActorIndex::eACTOR1, pose1);

    joint->setBreakForce(props->forceLimit, props->torqueLimit);

    PxD6JointDrive drive(props->stiffness, props->damping, props->forceLimit, false);
    PxD6JointDrive defaultDrive;

    bool anyLimit = false;
    // Set axis motion
    for (int i = 0; i < 6; ++i)
    {
        if ((props->axes >> i) & 1)
        {
            if (props->hasLimits[i])
            {
                joint->setMotion(g_dcToPxAxis[i], PxD6Motion::eLIMITED);
                anyLimit = true;
            }
            else
            {
                joint->setMotion(g_dcToPxAxis[i], PxD6Motion::eLOCKED);
            }
        }
        else
        {
            joint->setMotion(g_dcToPxAxis[i], PxD6Motion::eFREE);
        }
    }

    if (anyLimit)
    {
        PxSpring spring(props->limitStiffness, props->limitDamping);
        switch (props->jointType)
        {
        case DcJointType::eSpherical:
        {
            if (props->softLimit)
            {
                joint->setSwingLimit(PxJointLimitCone(props->lowerLimit, props->upperLimit, spring));
            }
            else
            {
                joint->setSwingLimit(PxJointLimitCone(props->lowerLimit, props->upperLimit, 0.01f));
            }
            break;
        }
        case DcJointType::ePrismatic:
        {
            for (int i = 0; i < 3; ++i)
            {
                if (((props->axes >> i) & 1) && props->hasLimits[i])
                {
                    if (props->softLimit)
                    {
                        joint->setLinearLimit(
                            g_dcToPxAxis[i], PxJointLinearLimitPair(props->lowerLimit, props->upperLimit, spring));
                    }
                    else
                    {
                        joint->setLinearLimit(
                            g_dcToPxAxis[i],
                            PxJointLinearLimitPair(props->lowerLimit, props->upperLimit, PxSpring(1e6, 0)));
                    }
                }
            }
            break;
        }
        case DcJointType::eRevolute:
        {
            if (((props->axes >> 3) & 1) && props->hasLimits[3])
            {
                if (props->softLimit)
                {
                    joint->setTwistLimit(PxJointAngularLimitPair(props->lowerLimit, props->upperLimit, spring));
                }
                else
                {
                    joint->setTwistLimit(PxJointAngularLimitPair(props->lowerLimit, props->upperLimit, 0.01f));
                }
            }
            if ((((props->axes >> 4) & 1) && props->hasLimits[4]) || (((props->axes >> 5) & 1) && props->hasLimits[5]))
            {
                if (props->softLimit)
                {
                    joint->setSwingLimit(PxJointLimitCone(props->lowerLimit, props->upperLimit, spring));
                }
                else
                {
                    joint->setSwingLimit(PxJointLimitCone(props->lowerLimit, props->upperLimit, 0.01f));
                }
            }
        }
        case DcJointType::eNone:
        case DcJointType::eFixed:
        default:
        {
            CARB_LOG_ERROR("Attempting to set limits to fixed D6 joint");
            break;
        }
        }
    }

    // Set linear drive
    for (int i = 0; i < 3; ++i)
    {
        if ((props->axes >> i) & 1)
        {
            joint->setDrive((PxD6Drive::Enum)i, drive);
        }
        else
        {
            joint->setDrive((PxD6Drive::Enum)i, defaultDrive);
        }
    }

    // All rotation axes are set
    if ((props->axes & kDcAxisAllRotation) == kDcAxisAllRotation)
    {
        joint->setDrive(PxD6Drive::eSWING, drive);
        joint->setDrive(PxD6Drive::eTWIST, drive);
        joint->setDrive(PxD6Drive::eSLERP, drive);
    }

    // Only swing axes are set
    else if ((props->axes & kDcAxisSwing1) && (props->axes & kDcAxisSwing2))
    {
        joint->setDrive(PxD6Drive::eTWIST, defaultDrive);
        joint->setDrive(PxD6Drive::eSLERP, defaultDrive);
        joint->setDrive(PxD6Drive::eSWING, drive);
    }

    // Only twist is set
    else if (props->axes & kDcAxisTwist)
    {
        joint->setDrive(PxD6Drive::eSWING, defaultDrive);
        joint->setDrive(PxD6Drive::eSLERP, defaultDrive);
        joint->setDrive(PxD6Drive::eTWIST, drive);
    }

    joint->setDrivePosition(PxTransform(PxIDENTITY()));

    // save props
    dcJoint->props = *props;

    return true;
}

bool getD6JointConstraintIsBroken(DcD6Joint* dcJoint)
{
    (void)DC_CHECK_SIMULATING();

    if (!dcJoint)
    {
        return false;
    }

    PxD6Joint* joint = dcJoint->pxJoint;
    if (joint)
    {
        return joint->getConstraintFlags() & PxConstraintFlag::eBROKEN;
    }
    else
    {
        return true;
    }
}

//
// RayCast
//

DcRayCastResult CARB_ABI DcRayCast(const carb::Float3& origin, const carb::Float3& direction, float max_distance)
{

    (void)DC_CHECK_SIMULATING();
    DcRayCastResult out;
    out.hit = false;

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return out;
    }

    omni::physx::RaycastHit result;
    out.hit = ctx->physxSceneQuery->raycastClosest(origin, direction, max_distance, result, false);

    if (out.hit)
    {
        out.rigidBody = ctx->registerRigidBody(intToPath(result.rigidBody));
        out.distance = result.distance;
    }
    return out;
}

//
// stage update callbacks
//

void SuAttach(long stageId, double metersPerUnit, void* data)
{
    // printf("++ DynamicControl: Stage Attach: stageId %ld\n", stageId);

    // HMMM: only allow a single "current" context
    if (g_dcCtx)
    {
        destroyContext(g_dcCtx);
    }

    g_dcCtx = createContext();
}

void SuDetach(void* data)
{
    // printf("++ DynamicControl: Stage Detach\n");

    if (g_dcCtx)
    {
        destroyContext(g_dcCtx);
        g_dcCtx = nullptr;
    }
}

void SuPause(void* data)
{
    printf("++ DC: Stage Pause\n");
    if (g_dcCtx)
    {
        g_dcCtx->wasPaused = true;
    }
}

void SuResume(float currentTime, void* data)
{
    // printf("++ DC: Stage Resume\n");

    if (g_dcCtx)
    {
        // printf("Refreshing context\n");
        // if pause is pressed there is no need to refresh pointers on the next play
        if (!g_dcCtx->wasPaused)
        {
            g_dcCtx->refreshPhysicsPointers(true);
        }
        g_dcCtx->isSimulating = true;
        g_dcCtx->wasPaused = false;
    }
}

void SuStop(void* data)
{
    // printf("++ DC: Stage Stop\n");

    if (g_dcCtx)
    {
        // destroyContext(g_dcCtx);
        // g_dcCtx = nullptr;
        printf("Refreshing context\n");
        g_dcCtx->refreshPhysicsPointers(false);
        g_dcCtx->isSimulating = false;
        g_dcCtx->wasPaused = false;
    }
}

void SuUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    // printf("++ DC: Stage Update\n");
    // Skip if not simulating
    if (!settings->isPlaying)
    {
        return;
    }
    // FIXME: should we do this automatically?
    // FIXME: should this be done per physics step instead of stage update?
    if (g_dcCtx)
    {
        //++g_dcCtx->frameno;
        // updateContext(g_dcCtx);
        // if this extension is acquired with play happening, make sure that simulating is set to true
        g_dcCtx->isSimulating = true;
    }
}


void CARB_ABI onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    // printf("++ DC: Prim Remove: %s\n", primPath);

    auto& ctx = g_dcCtx;
    if (!ctx)
    {
        return;
    }

    ctx->removeUsdPath(primPath);
}
}
}
}

CARB_EXPORT void carbOnPluginStartup()
{
    using namespace omni::isaac::dynamic_control;

    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    g_su = framework->acquireInterface<omni::kit::IStageUpdate>();
    if (!g_su)
    {
        CARB_LOG_ERROR("Failed to acquire stage update interface");
        return;
    }

    omni::kit::StageUpdateNodeDesc suDesc = { 0 };
    suDesc.displayName = "Dynamic Control";
    suDesc.order = 20; // should run after omni.physx!!
    suDesc.onAttach = SuAttach;
    suDesc.onDetach = SuDetach;
    suDesc.onUpdate = SuUpdate;
    suDesc.onResume = SuResume;
    suDesc.onPause = SuPause;
    suDesc.onStop = SuStop;

    suDesc.onPrimRemove = onPrimRemove;

    g_suNode = g_su->createStageUpdateNode(suDesc);
    if (!g_suNode)
    {
        CARB_LOG_ERROR("Failed to create stage update node");
        return;
    }
}

CARB_EXPORT void carbOnPluginShutdown()
{
    using namespace omni::isaac::dynamic_control;

    if (g_suNode)
    {
        g_su->destroyStageUpdateNode(g_suNode);
        g_suNode = nullptr;
    }
}

void fillInterface(omni::isaac::dynamic_control::DynamicControl& iface)
{
    using namespace omni::isaac::dynamic_control;

    memset(&iface, 0, sizeof(iface));

    iface.hello = DcHello;

    // iface.createContext = DcCreateContext;
    // iface.destroyContext = DcDestroyContext;
    // iface.updateContext = DcUpdateContext;
    iface.isSimulating = DcIsSimulating;
    iface.getRigidBody = DcGetRigidBody;
    iface.getJoint = DcGetJoint;
    iface.getDof = DcGetDof;
    iface.getArticulation = DcGetArticulation;
    iface.getD6Joint = DcGetD6Joint;

    iface.getObject = DcGetObject;
    iface.peekObjectType = DcPeekObjectType;
    iface.getObjectType = DcGetObjectType;
    iface.getObjectTypeName = DcGetObjectTypeName;

    iface.wakeUpRigidBody = DcWakeUpRigidBody;
    iface.wakeUpArticulation = DcWakeUpArticulation;

    iface.getArticulationName = DcGetArticulationName;
    iface.getArticulationPath = DcGetArticulationPath;

    iface.getArticulationBodyCount = DcGetArticulationBodyCount;
    iface.getArticulationBody = DcGetArticulationBody;
    iface.findArticulationBody = DcFindArticulationBody;
    iface.findArticulationBodyIndex = DcFindArticulationBodyIndex;
    iface.getArticulationRootBody = DcGetArticulationRootBody;
    iface.getArticulationBodyStates = DcGetArticulationBodyStates;
    // iface.setArticulationBodyStates = DcSetArticulationBodyStates;

    iface.getArticulationJointCount = DcGetArticulationJointCount;
    iface.getArticulationJoint = DcGetArticulationJoint;
    iface.findArticulationJoint = DcFindArticulationJoint;

    iface.getArticulationDofCount = DcGetArticulationDofCount;
    iface.getArticulationDof = DcGetArticulationDof;
    iface.findArticulationDof = DcFindArticulationDof;
    iface.findArticulationDofIndex = DcFindArticulationDofIndex;
    iface.getArticulationDofProperties = DcGetArticulationDofProperties;
    iface.setArticulationDofProperties = DcSetArticulationDofProperties;
    iface.getArticulationDofStates = DcGetArticulationDofStates;
    iface.setArticulationDofStates = DcSetArticulationDofStates;
    iface.getArticulationDofStateDerivatives = DcGetArticulationDofStateDerivatives;
    iface.setArticulationDofPositionTargets = DcSetArticulationDofPositionTargets;
    iface.setArticulationDofVelocityTargets = DcSetArticulationDofVelocityTargets;
    iface.applyArticulationDofEfforts = DcApplyArticulationDofEfforts;

    iface.getRigidBodyName = DcGetRigidBodyName;
    iface.getRigidBodyPath = DcGetRigidBodyPath;
    iface.getRigidBodyParentJoint = DcGetRigidBodyParentJoint;
    iface.getRigidBodyChildJointCount = DcGetRigidBodyChildJointCount;
    iface.getRigidBodyChildJoint = DcGetRigidBodyChildJoint;
    iface.getRigidBodyPose = DcGetRigidBodyPose;
    iface.getRigidBodyLinearVelocity = DcGetRigidBodyLinearVelocity;
    iface.getRigidBodyLocalLinearVelocity = DcGetRigidBodyLocalLinearVelocity;
    iface.getRigidBodyAngularVelocity = DcGetRigidBodyAngularVelocity;
    iface.setRigidBodyDisableGravity = DcSetRigidBodyDisableGravity;
    iface.setRigidBodyDisableSimulation = DcSetRigidBodyDisableSimulation;
    iface.setRigidBodyPose = DcSetRigidBodyPose;
    iface.setRigidBodyLinearVelocity = DcSetRigidBodyLinearVelocity;
    iface.setRigidBodyAngularVelocity = DcSetRigidBodyAngularVelocity;
    iface.applyBodyForce = DcApplyBodyForce;
    iface.getRelativeBodyPoses = DcGetRelativeBodyPoses;
    iface.getRigidBodyProperties = DcGetRigidBodyProperties;

    iface.getJointName = DcGetJointName;
    iface.getJointPath = DcGetJointPath;
    iface.getJointType = DcGetJointType;
    iface.getJointDofCount = DcGetJointDofCount;
    iface.getJointDof = DcGetJointDof;
    iface.getJointParentBody = DcGetJointParentBody;
    iface.getJointChildBody = DcGetJointChildBody;

    iface.getDofName = DcGetDofName;
    iface.getDofPath = DcGetDofPath;
    iface.getDofType = DcGetDofType;
    iface.getDofJoint = DcGetDofJoint;
    iface.getDofParentBody = DcGetDofParentBody;
    iface.getDofChildBody = DcGetDofChildBody;
    iface.getDofState = DcGetDofState;
    iface.setDofState = DcSetDofState;
    iface.getDofPosition = DcGetDofPosition;
    iface.setDofPosition = DcSetDofPosition;
    iface.getDofVelocity = DcGetDofVelocity;
    iface.setDofVelocity = DcSetDofVelocity;
    iface.getDofProperties = DcGetDofProperties;
    iface.setDofProperties = DcSetDofProperties;
    iface.setDofPositionTarget = DcSetDofPositionTarget;
    iface.setDofVelocityTarget = DcSetDofVelocityTarget;
    iface.getDofPositionTarget = DcGetDofPositionTarget;
    iface.getDofVelocityTarget = DcGetDofVelocityTarget;
    iface.applyDofEffort = DcApplyDofEffort;

    iface.createRigidBodyAttractor = DcCreateRigidBodyAttractor;
    iface.destroyRigidBodyAttractor = DcDestroyRigidBodyAttractor;
    iface.getAttractorProperties = DcGetAttractorProperties;
    iface.setAttractorProperties = DcSetAttractorProperties;
    iface.setAttractorTarget = DcSetAttractorTarget;

    iface.createD6Joint = DcCreateD6Joint;
    iface.destroyD6Joint = DcDestroyD6Joint;
    iface.getD6JointProperties = DcGetD6JointProperties;
    iface.setD6JointProperties = DcSetD6JointProperties;
    iface.getD6JointConstraintIsBroken = DcGetD6JointConstraintIsBroken;

    iface.setOriginOffset = DcSetOriginOffset;

    iface.rayCast = DcRayCast;
}
