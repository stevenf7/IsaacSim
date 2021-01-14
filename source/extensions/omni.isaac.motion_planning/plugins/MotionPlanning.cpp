// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "MotionPlanningPCH.h"
// clang-format on

#include <omni/isaac/motion_planning/MotionPlanning.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Math.h>

#include <omni/kit/IStageUpdate.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tasking/ITasking.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include "MotionPolicy.h"

#include <lula/util/logging.h>
#include <glog/logging.h>

#include <physicsSchemaTools/UsdTools.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>

#include <map>
#include <string>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.motion_planning.plugin", "Isaac Motion Planning",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::motion_planning::MotionPlanning)
CARB_PLUGIN_IMPL_DEPS(omni::isaac::dynamic_control::DynamicControl, omni::kit::IStageUpdate, carb::tasking::ITasking)

// private stuff
namespace
{
pxr::UsdStageWeakPtr gStage = nullptr;
carb::Framework* gFramework = nullptr;
carb::tasking::ITasking* gTasking;
carb::tasking::Counter* gTaskCounter;
omni::kit::IStageUpdate* gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
omni::isaac::dynamic_control::DynamicControl* gDynamicControl = nullptr;
static bool gInitLogging = false;
static float gTime = 0;

static omni::physx::IPhysx* gPhysXInterface = nullptr;
omni::physx::SubscriptionId gStepSubscription;
omni::physx::SubscriptionId gEventSubscription;

std::unordered_map<size_t, std::shared_ptr<MotionPolicy>> gMotionPolicies;
}
size_t CARB_ABI MpRegisterRmp(std::string robotURDFPath,
                              std::string robotDescriptorPath,
                              std::string rmpFlowCommonPath,
                              std::string primPath,
                              std::string controlFrame,
                              bool verbose)
{
    auto SDFPrimPath = pxr::SdfPath(primPath);
    auto SDFHash = SDFPrimPath.GetHash();
    pxr::UsdPrim childPrim = gStage->GetPrimAtPath(pxr::SdfPath(primPath));
    if (childPrim)
    {
        omni::isaac::dynamic_control::DcObjectType primType =
            gDynamicControl->peekObjectType(childPrim.GetPath().GetString().c_str());

        if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            std::shared_ptr<MotionPolicy> policy = std::make_shared<MotionPolicy>(gStage, gDynamicControl);

            if (policy->setRobotPrim(childPrim))
            {
                CARB_LOG_INFO("Register Articulation at %s", childPrim.GetPath().GetString().c_str());
                policy->initialize(robotURDFPath, robotDescriptorPath, rmpFlowCommonPath, controlFrame);

                gMotionPolicies[SDFHash] = std::move(policy);
                return SDFHash;
            }
            else
            {
                CARB_LOG_ERROR("getArticulation or getArticulationRootBody handle not valid");
            }
        }
        else
        {
            CARB_LOG_ERROR("No valid articulation at %s", primPath.c_str());
        }
    }
    else
    {
        CARB_LOG_ERROR("Could not find %s", primPath.c_str());
    }
    return 0;
}
void CARB_ABI MpUnregisterRmp(size_t handle)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle].reset();
        gMotionPolicies.erase(handle);
    }
}


// Converts the global pose to local
void CARB_ABI MpSetTargetGlobal(size_t handle, carb::Float3 position, carb::Float4 rotation)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        // convert the position and rotation into local coordinates
        // M_loc = M_parent_inv * M
        gMotionPolicies[handle]->setTargetGlobal(position, rotation);
    }
}

void CARB_ABI MpSetFrequency(size_t handle, const float Frequency)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->setFrequency(Frequency);
    }
}

// Assumes that the pose is given in local coordinates
void CARB_ABI MpSetTargetLocal(size_t handle, carb::Float3 position, carb::Float4 rotation)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {

        gMotionPolicies[handle]->setTargetLocal(position, rotation);
    }
}
void CARB_ABI MpGoLocal(size_t handle, omni::isaac::motion_planning::PartialPoseCommand command)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->goLocal(command);
    }
}

std::vector<double> CARB_ABI MpGetError(size_t handle)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        return gMotionPolicies[handle]->getError();
    }
    return std::vector<double>({ DBL_MAX, DBL_MAX, DBL_MAX, DBL_MAX });
}

std::vector<carb::Float3> CARB_ABI MpGetRMPState(size_t handle)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        return gMotionPolicies[handle]->getRmpState();
    }
    return std::vector<carb::Float3>();
}

std::vector<carb::Float3> CARB_ABI MpGetRMPTarget(size_t handle)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        return gMotionPolicies[handle]->getRmpTarget();
    }
    return std::vector<carb::Float3>();
}

void CARB_ABI MpAddObstacle(size_t handle, std::string primPath, int type, carb::Float3 scale)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->addObstacle(primPath, type, scale);
    }
}
void CARB_ABI MpUpdateObstacle(size_t handle, std::string primPath)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->updateObstacle(primPath);
    }
}
void CARB_ABI MpRemoveObstacle(size_t handle, std::string primPath)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->removeObstacle(primPath);
    }
}
void CARB_ABI MpEnableObstacle(size_t handle, std::string primPath)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->enableObstacle(primPath);
    }
}
void CARB_ABI MpDisableObstacle(size_t handle, std::string primPath)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->disableObstacle(primPath);
    }
}
void CARB_ABI MpSetDefaultConfig(size_t handle, const std::vector<double>& config)
{
    if (handle != 0 && gMotionPolicies.find(handle) != gMotionPolicies.end())
    {
        gMotionPolicies[handle]->setDefaultConfig(config);
    }
}

// This function should return new poses in meters
// Update obstacles in meters as well

std::vector<omni::isaac::dynamic_control::DcTransform> CARB_ABI MpUpdateGetRelativePoses(
    size_t rmp_handle, std::vector<std::pair<omni::isaac::dynamic_control::DcHandle, std::string>> handles)
{
    double unitScale = UsdGeomGetStageMetersPerUnit(gStage);
    std::vector<omni::isaac::dynamic_control::DcTransform> result;
    if (rmp_handle != 0 && gMotionPolicies.find(rmp_handle) != gMotionPolicies.end())
    {
        omni::isaac::dynamic_control::DcTransform parentTransform =
            gDynamicControl->getRigidBodyPose(gMotionPolicies[rmp_handle]->getRobotRootHandle());

        std::vector<omni::isaac::dynamic_control::DcHandle> DcHandles;
        for (size_t i = 0; i < handles.size(); i++)
        {
            DcHandles.push_back(handles[i].first);
        }
        result.resize(DcHandles.size());
        gDynamicControl->getRelativeBodyPoses(
            gMotionPolicies[rmp_handle]->getRobotRootHandle(), DcHandles.size(), DcHandles.data(), result.data());
        for (size_t i = 0; i < handles.size(); i++)
        {
            std::string primPath = handles[i].second;
            if (gDynamicControl->getObjectType(handles[i].first) == omni::isaac::dynamic_control::eDcObjectRigidBody &&
                handles[i].first != omni::isaac::dynamic_control::kDcInvalidHandle)
            {
                result[i].p.x *= unitScale;
                result[i].p.y *= unitScale;
                result[i].p.z *= unitScale;
            }
            else // eDcObjectNone
            {
                pxr::UsdPrim prim = gStage->GetPrimAtPath(pxr::SdfPath(primPath));
                const pxr::GfTransform bodyToWorld(omni::usd::UsdUtils::getWorldTransformMatrix(prim));
                const pxr::GfQuatd q = bodyToWorld.GetRotation().GetQuat();
                omni::isaac::dynamic_control::DcTransform T;
                T.p = carb::Float3({ bodyToWorld.GetTranslation()[0] * unitScale,
                                     bodyToWorld.GetTranslation()[1] * unitScale,
                                     bodyToWorld.GetTranslation()[2] * unitScale });
                T.r = carb::Float4({ q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2], q.GetReal() });

                result[i] = omni::isaac::utils::math::transformInv(parentTransform, T);
            }
            gMotionPolicies[rmp_handle]->updateObstacle(primPath, result[i]);
        }
    }
    else
    {
        CARB_LOG_WARN("RMP Handle not valid");
    }
    return result;
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    // try and find USD stage from Id
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

    if (!stage)
    {
        CARB_LOG_ERROR("Isaac MotionPlanning could not find USD stage");
        return;
    }

    gStage = stage;
    gTime = 0;
}

void onDetach(void* userData)
{
    CARB_LOG_INFO("onDetach MotionPlanning");
    gTime = 0;
    gMotionPolicies.clear();
}
struct TaskData
{
    double time;
    double dt;
    size_t handle;
};
auto loadTaskFn = [](carb::tasking::ITasking* tasking, void* taskArg) {
    TaskData* taskArgs = reinterpret_cast<TaskData*>(taskArg);
    gMotionPolicies[taskArgs->handle]->step(taskArgs->time, taskArgs->dt);
};


void onPhysicsUpdate(omni::physx::SimulationStatusEvent eventStatus, void* userData)
{

    // if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationStarting)
    // {
    //     CARB_LOG_INFO("Simulation starting");
    // }
    // if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationEnded)
    // {
    //     CARB_LOG_INFO("Simulation Ended");
    // }
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    CARB_LOG_INFO("Physics Step");

    CARB_PROFILE_ZONE(0, "MpOnUpdate");
#if 0
    for (const auto& policy : gMotionPolicies)
    {
        policy.second->Step(gTime, elapsedSecs);
    }
#else
    TaskData* td = new TaskData[gMotionPolicies.size()];
    int index = 0;
    for (const auto& policy : gMotionPolicies)
    {
        td[index].time = gTime;
        td[index].dt = timeElapsed;
        td[index].handle = policy.first;

        carb::tasking::TaskDesc bigTask{};
        bigTask.priority = carb::tasking::Priority::eHigh;
        bigTask.task = loadTaskFn;
        bigTask.taskArg = (void*)(td + index);
        gTasking->addTask(bigTask, gTaskCounter);
        index++;
    }
    gTasking->yieldUntilCounter(gTaskCounter);
    delete[] td;
#endif
    gTime += timeElapsed;
}

void onStop(void* userData)
{
    gTime = 0;
    gTasking->yieldUntilCounter(gTaskCounter);
    for (const auto& policy : gMotionPolicies)
    {
        policy.second->reset();
    }
}

CARB_EXPORT void carbOnPluginStartup()
{
    gFramework = carb::getFramework();
    gStageUpdate = gFramework->acquireInterface<omni::kit::IStageUpdate>();
    gDynamicControl = gFramework->acquireInterface<omni::isaac::dynamic_control::DynamicControl>();
    gTasking = gFramework->acquireInterface<carb::tasking::ITasking>();

    gTaskCounter = gTasking->createCounter();

    if (!gDynamicControl)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }
    gPhysXInterface = gFramework->acquireInterface<omni::physx::IPhysx>();
    if (!gPhysXInterface)
    {
        CARB_LOG_ERROR("Failed to acquire PhysX` interface");
        return;
    }


    gStepSubscription = gPhysXInterface->subscribePhysicsStepEvents(onPhysicsStep, nullptr);
    // gEventSubscription = gPhysXInterface->subscribePhysicsSimulationEvents(onPhysicsUpdate, nullptr);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "MotionPlanning";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    // desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    // Create the stage update node and make sure it runs first
    size_t index = gStageUpdate->getStageUpdateNodeCount();
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
    // gStageUpdate->setStageUpdateNodeOrder(index, -100);
    if (!gInitLogging)
    {
        google::InitGoogleLogging("Lula");
        lula::util::SetStderrLoggingLevel(lula::util::LoggingLevel::ERROR);
        gInitLogging = true;
    }
}

CARB_EXPORT void carbOnPluginShutdown()
{
    gPhysXInterface->unsubscribePhysicsStepEvents(gStepSubscription);
    // gPhysXInterface->unsubscribePhysicsSimulationEvents(gEventSubscription)
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
    gTasking->destroyCounter(gTaskCounter);
}

void fillInterface(omni::isaac::motion_planning::MotionPlanning& iface)
{
    using namespace omni::isaac::motion_planning;

    memset(&iface, 0, sizeof(iface));

    iface.registerRmp = MpRegisterRmp;
    iface.unregisterRmp = MpUnregisterRmp;
    iface.setFrequency = MpSetFrequency;
    iface.setTargetGlobal = MpSetTargetGlobal;
    iface.setTargetLocal = MpSetTargetLocal;
    iface.goLocal = MpGoLocal;
    iface.getError = MpGetError;
    iface.getRMPState = MpGetRMPState;
    iface.getRMPTarget = MpGetRMPTarget;
    iface.addObstacle = MpAddObstacle;
    iface.updateObstacle = MpUpdateObstacle;
    iface.removeObstacle = MpRemoveObstacle;
    iface.enableObstacle = MpEnableObstacle;
    iface.disableObstacle = MpDisableObstacle;
    iface.updateGetRelativePoses = MpUpdateGetRelativePoses;
    iface.setDefaultConfig = MpSetDefaultConfig;
}
