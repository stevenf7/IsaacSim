
// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "GxfContext.h"

#include "../Gxf/CameraComponent.h"
#include "../Gxf/CommandComponent.h"
#include "../Gxf/LidarComponent.h"
#include "../Gxf/PoseTreeComponent.h"
#include "../Gxf/UltrasonicComponent.h"
#include "../Gxf/VehicleSimulator.h"
#include "GxfComponent.h"

#include <gxf/std/unbounded_allocator.hpp>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

GxfContext::GxfContext(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
{
    mDynamicControlPtr = dynamicControlPtr;
    mViewportInterface = carb::getCachedInterface<omni::kit::IViewport>();
    mViewportManager = std::make_unique<utils::ViewportManager>(mViewportInterface);
}

GxfContext::~GxfContext()
{
}
gxf_result_t GxfContext::create(const std::string& basePath,
                                const std::string& manifestFile,
                                const std::vector<std::string>& graphFiles)
{
    if (mContext == 0)
    {
        CARB_LOG_WARN("Loading: %s %s", basePath.c_str(), manifestFile.c_str());
        const char* manifest_filename = manifestFile.c_str();
        const char* base_path = basePath.c_str();
        const GxfLoadExtensionsInfo load_ext_info{ nullptr, 0, &manifest_filename, 1, base_path };
        gxf_result_t result;

        if ((result = GxfContextCreate(&mContext)))
        {
            CARB_LOG_ERROR("GxfContextCreate failed");
            return result;
        }
        if ((result = GxfLoadExtensions(mContext, &load_ext_info)))
        {
            CARB_LOG_ERROR("GxfLoadExtensions failed");
            return result;
        }
        for (auto& graph : graphFiles)
        {
            CARB_LOG_WARN("Loading Graph: %s", graph.c_str());
            if ((result = GxfGraphLoadFile(mContext, graph.c_str())))
            {
                CARB_LOG_ERROR("GxfLoadGraph failed");
                return result;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Context already exists");
    }
    return GXF_SUCCESS;
}
gxf_result_t GxfContext::start()
{
    gxf_result_t result;
    if (mRunning == false)
    {
        // // Create a host memory allocator
        // gxf_uid_t eid;
        // if ((result = GxfEntityCreate(mContext, &eid)))
        // {
        //     CARB_LOG_ERROR("GxfEntityCreate failed");
        // }
        // gxf_tid_t tid;
        // if ((result = GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::UnboundedAllocator>(),
        // &tid)))
        // {
        //     CARB_LOG_ERROR("GxfComponentTypeId");
        //     return result;
        // }
        // gxf_uid_t cid;
        // if ((result = GxfComponentAdd(mContext, eid, tid, "allocator", &cid)))
        // {
        //     CARB_LOG_ERROR("GxfComponentAdd");
        //     return result;
        // }
        // if ((result = GxfParameterSetInt32(mContext, cid, "storage_type", 0)))
        // {
        //     CARB_LOG_ERROR("GxfParameterSetInt32");
        //     return result;
        // }
        // if ((result = GxfParameterSetBool(mContext, cid, "do_not_use_cuda_malloc_host", true)))
        // {
        //     CARB_LOG_ERROR("GxfParameterSetBool");
        //     return result;
        // }
        // auto allocator = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(mContext, cid);
        // if (!allocator)
        // {
        //     CARB_LOG_ERROR("mAllocator Not Valid %d", allocator.error());
        //     return allocator.error();
        // }
        // else
        // {
        //     mAllocator =allocator.value();
        //     if ((result = mAllocator.get()->initialize()))
        //     {
        //         CARB_LOG_ERROR("mAllocator Not initialized %d", result);
        //         return result;
        //     }
        // }
        // if (mAllocator.get())
        // {
        //     CARB_LOG_ERROR("CAN ALLOCATE A: %d", mAllocator.get()->is_available(100));
        // }
        // GxfEntityActivate(mContext, eid);

        if ((result = GxfGraphActivate(mContext)))
        {
            CARB_LOG_ERROR("GxfGraphActivate");
            return result;
        }
        if ((result = GxfGraphRunAsync(mContext)))
        {
            CARB_LOG_ERROR("GxfGraphRunAsync");
            return result;
        }
        {
            gxf_uid_t eid;
            GxfEntityFind(mContext, "isaac_sim_allocator", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::UnboundedAllocator>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(mContext, eid, tid, "allocator", nullptr, &cid);
            auto allocator = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(mContext, cid);
            if (!allocator)
            {
                CARB_LOG_ERROR("Allocator not found");
                return nvidia::gxf::ToResultCode(allocator);
            }
            mAllocator = std::move(allocator.value());
        }
        {
            gxf_uid_t eid;
            GxfEntityFind(mContext, "clock", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::Clock>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(mContext, eid, tid, "default", nullptr, &cid);
            auto clock = nvidia::gxf::Handle<nvidia::gxf::Clock>::Create(mContext, cid);
            if (!clock)
            {
                CARB_LOG_ERROR("Clock not found");
                return nvidia::gxf::ToResultCode(clock);
            }
            mClock = std::move(clock.value());
        }

        // if (mAllocator.get())
        // {
        //     CARB_LOG_ERROR("CAN ALLOCATE B: %d", mAllocator.get()->is_available(100));
        // }
        mPoseTreeMap.clear();
        mRunning = true;

        // This GXF app just started, set context and allocator for existing components
        for (auto& component : mComponents)
        {
            component.second.get()->setGxfContext(mContext);
            component.second.get()->setGxfAllocator(mAllocator);
            component.second.get()->setPoseTreeMap(&mPoseTreeMap);
            component.second->mDoStart = true;
        }
    }
    else
    {
        CARB_LOG_WARN("Context already running");
    }

    return GXF_SUCCESS;
}
void GxfContext::tick(double dt)
{
    CARB_PROFILE_ZONE(0, "REB GxfContext Tick");
    if (!mContext)
    {
        return;
    }

    // omni::isaac::utils::ScopedTimer TimerApp("IsaacApplication");
    // only update time difference to bridge app if the step size is greater than zero
    // if (dt > 0)
    // {
    //     mError =
    //         (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds,
    //         &mTimeDifferenceNanoSeconds);
    // }
    if (mRunning)
    {

        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                component.second->GxfComponent::onComponentChange();
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
        }

        mTimeSeconds = mClock->time();
        mTimeNanoSeconds = mTimeSeconds * 1e9;
        for (auto& component : mComponents)
        {
            component.second.get()->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
        }

#if 0
        // omni::isaac::utils::ScopedTimer TimerApp("  Publish");
        TaskData* taskArray = new TaskData[mComponents.size()];
        int index = 0;
        for (auto& component : mComponents)
        {
            taskArray[index].component = component.second.get();

            mTasking->addTask(carb::tasking::Priority::eHigh, mTaskCounter, TaskFunction, (void*)(taskArray + index));
            index++;
        }

        for (auto& component : mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second->tick();
            }
        }

        mTasking->wait(mTaskCounter);
        delete[] taskArray;

#else

        for (auto& component : mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second->publishAllMessages();
                component.second->tick();
            }
        }
#endif


        // mSceneLoaderComponent->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
        // mSceneLoaderComponent->tick();
    }
    // TODO: do this before or after tick?
    //    mTimeSeconds += dt;
    //    mTimeNanoSeconds = mTimeSeconds * 1e9;
    // gxf_result_t result;
    // if ((result = GxfGraphWait(mContext)))
    // {
    //     CARB_LOG_ERROR("GxfGraphWait");
    //     // return result;
    // }
}
gxf_result_t GxfContext::stop()
{
    gxf_result_t result;
    if (mRunning == true)
    {
        mRunning = false;
        mPoseTreeMap.clear();
        if ((result = GxfGraphInterrupt(mContext)))
        {
            CARB_LOG_ERROR("GxfGraphInterrupt %s", GxfResultStr(result));
            return result;
        }
        if ((result = GxfGraphWait(mContext)))
        {
            CARB_LOG_ERROR("GxfGraphWait %s", GxfResultStr(result));
            return result;
        }
        if ((result = GxfGraphDeactivate(mContext)))
        {
            CARB_LOG_ERROR("GxfGraphDeactivate %s", GxfResultStr(result));
            return result;
        }
    }
    else
    {
        CARB_LOG_WARN("Context already stopped");
        return GXF_FAILURE;
    }
    return GXF_SUCCESS;
}
gxf_result_t GxfContext::destroy()
{
    gxf_result_t result = GXF_SUCCESS;
    if ((result = GxfContextDestroy(mContext)))
    {
        CARB_LOG_ERROR("GxfContextDestroy %s", GxfResultStr(result));
    }
    mContext = 0;
    return result;
}

void GxfContext::onStop()
{
    for (auto& component : mComponents)
    {
        component.second->onStop();
        component.second->mDoStart = true;
    }
}
void GxfContext::onComponentAdd(const pxr::UsdPrim& prim)
{
    std::unique_ptr<GxfComponent> component;

    // if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink>())
    // {
    //     component = std::make_unique<robot_engine_bridge_gxf::RigidBodiesSink>(mDynamicControlPtr);
    //     component->initialize(mContext, pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink(prim), mStage);
    // }
    // else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineTeleport>())
    // {
    //     component = std::make_unique<Teleport>(mDynamicControlPtr);
    //     component->initialize(mIsaacCApiPtr, mAppHandle, pxr::RobotEngineBridgeSchemaRobotEngineTeleport(prim),
    //     mStage);
    // }
    if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic>())
    {
        component = std::make_unique<UltrasonicComponent>();
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineLidar>())
    {
        component = std::make_unique<LidarComponent>();
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEngineLidar(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineCamera>())
    {
        component = std::make_unique<CameraComponent>(mViewportManager.get());
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEngineCamera(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEnginePoseTree>())
    {
        component = std::make_unique<PoseTreeComponent>(mDynamicControlPtr);
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEnginePoseTree(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineCommand>())
    {
        component = std::make_unique<CommandComponent>();
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEngineCommand(prim), mStage);
    }
    else if (prim.IsA<pxr::RobotEngineBridgeSchemaRobotEngineVehicle>())
    {
        component = std::make_unique<VehicleSimulator>();
        component->initialize(mContext, mAllocator, pxr::RobotEngineBridgeSchemaRobotEngineVehicle(prim), mStage);
    }
    if (component)
    {
        CARB_LOG_INFO("Create: Prim %s with type: %s", prim.GetPath().GetString().c_str(),
                      component->getPrim().GetPrim().GetTypeName().GetString().c_str());
        component->setPoseTreeMap(&mPoseTreeMap);
        mComponents[prim.GetPath().GetString()] = std::move(component);
    }
}
bool GxfContext::tickComponent(const pxr::UsdPrim& prim)
{
    if (!mContext)
    {
        return false;
    }
    if (prim)
    {
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            auto* component = mComponents[prim.GetPath().GetString()].get();


            if (component->mDoStart == true)
            {
                component->onStart();
                component->mDoStart = false;
            }

            component->publishAllMessages();
            component->tick();
            return true;
        }
    }
    return false;
}
}
}
}
