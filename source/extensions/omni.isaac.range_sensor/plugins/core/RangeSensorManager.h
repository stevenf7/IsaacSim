// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../lidar/LidarSensor.h"
#include "../radar/RadarSensor.h"
#include "../ultrasonic/UltrasonicSensor.h"
#include "RangeSensorComponent.h"
#include "plugins/bridge/BridgeApplication.h"
#include "plugins/core/ScopedTimer.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/fastcache/FastCache.h>
#include <carb/imgui/ImGui.h>
#include <carb/logging/Log.h>
#include <carb/renderer/Renderer.h>
#include <carb/settings/ISettings.h>

#include <omni/kit/IViewport.h>
#include <omni/kit/KitUtils.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

/**
 * @brief Data used by a lidar task thread
 *
 */
struct RangeSensorTaskData
{
    double timeSeconds;
    int64_t timeNanoSeconds;
    double dt;
    RangeSensorComponent* sensor;
};

/**
 * @brief Function called by each lidar task thread
 *
 */
auto rangeSensorTaskFunction = [](carb::tasking::ITasking* tasking, void* taskArg) {
    RangeSensorTaskData* taskData = reinterpret_cast<RangeSensorTaskData*>(taskArg);
    taskData->sensor->updateTimestamp(taskData->timeSeconds, taskData->dt, taskData->timeNanoSeconds);
    taskData->sensor->tick();
};

class RangeSensorManager : public utils::BridgeApplicationBase<RangeSensorComponent>
{
public:
    /**
     * @brief Construct a new Sensor Manager object
     *
     * @param physxPtr
     */
    RangeSensorManager(omni::renderer::IDebugDraw* debugDrawPtr,
                       omni::physx::IPhysx* physxPtr,
                       carb::fastcache::FastCache* fastCachePtr,
                       carb::tasking::ITasking* taskingPtr)
    {
        mDebugDrawPtr = debugDrawPtr;
        mPhysxPtr = physxPtr;
        mFastCachePtr = fastCachePtr;
        mTasking = taskingPtr;
        mTaskCounter = mTasking->createCounter();
        mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    }

    /**
     * @brief Destroy the Sensor Manager object
     *
     */
    ~RangeSensorManager()
    {
        mViewportUiEventSub = nullptr;
        mTasking->yieldUntilCounter(mTaskCounter);
        releaseDebugLineList();
        mTasking->destroyCounter(mTaskCounter);
        mComponents.clear();
    }
    /**
     * @brief Tick the application and all components
     *
     * @param dt
     */
    void tick(double dt)
    {
        if (mComponents.size() == 0)
        {
            return;
        }

        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                component.second->onStart();
                component.second->mDoStart = false;
            }
        }

#if 1
        RangeSensorTaskData* taskArray = new RangeSensorTaskData[mComponents.size()];
        int index = 0;
        for (auto& component : mComponents)
        {
            taskArray[index].timeSeconds = this->mTimeSeconds;
            taskArray[index].timeNanoSeconds = this->mTimeNanoSeconds;
            taskArray[index].dt = dt;
            taskArray[index].sensor = component.second.get();

            carb::tasking::TaskDesc bigTask{};
            bigTask.priority = carb::tasking::Priority::eHigh;
            bigTask.task = rangeSensorTaskFunction;
            bigTask.taskArg = (void*)(taskArray + index);
            mTasking->addTask(bigTask, mTaskCounter);
            index++;
        }
        mTasking->yieldUntilCounter(mTaskCounter);
        delete[] taskArray;

#else
        for (auto& component : mComponents)
        {
            component.second.get()->updateTimestamp(this->mTimeSeconds, dt, this->mTimeNanoSeconds);
            component.second->tick();
        }
#endif


        size_t mShapeDebugIndex = 0;
        bool shouldDraw = false;
        size_t count = 0;
        for (auto& component : mComponents)
        {
            if (component.second.get()->getDrawPoints() || component.second.get()->getDrawLines())
            {
                auto& debugLines = component.second.get()->getDebugLines();
                if (debugLines.size() > 0)
                {
                    shouldDraw = true;
                    count += debugLines.size();
                }
            }
        }
        if (shouldDraw)
        {
            releaseDebugLineList();
            createDebugLineList(count);
            for (auto& component : mComponents)
            {
                if (component.second.get()->getDrawPoints() || component.second.get()->getDrawLines())
                {
                    auto& debugLines = component.second.get()->getDebugLines();
                    for (const auto& line : debugLines)
                    {
                        // mDebugLineVector.push_back(line);
                        mDebugDrawPtr->setLine(mShapeDebugLineBuffer, mShapeDebugIndex++, line.startPos, line.color,
                                               line.endPos, line.color);
                    }
                }
            }
        }
        this->mTimeSeconds += dt;
        this->mTimeNanoSeconds = static_cast<int64_t>(mTimeSeconds * 1e9);
    }
    /**
     * @brief Run once the scene is stopped
     *
     */
    void onStop()
    {
        // PxScene can change after stop is pressed so reset mDoStart bool to force OnStart to run
        for (auto& component : mComponents)
        {
            component.second->mDoStart = true;
        }
        releaseDebugLineList();
    }
    /**
     * @brief Create a supported component in this manager
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim)
    {
        std::unique_ptr<RangeSensorComponent> component;

        if (prim.IsA<pxr::RangeSensorSchemaLidar>())
        {
            component = std::make_unique<LidarSensor>(mPhysxPtr, mFastCachePtr);
            component->initialize(pxr::RangeSensorSchemaLidar(prim), mStage);
        }
        else if (prim.IsA<pxr::RangeSensorSchemaUltrasonicArray>())
        {
            component = std::make_unique<UltrasonicSensor>(mPhysxPtr, mFastCachePtr);
            component->initialize(pxr::RangeSensorSchemaUltrasonicArray(prim), mStage);
        }
        else if (prim.IsA<pxr::RangeSensorSchemaRadar>())
        {
            component = std::make_unique<RadarSensor>(mPhysxPtr, mFastCachePtr);
            component->initialize(pxr::RangeSensorSchemaRadar(prim), mStage);
        }

        if (component)
        {
            CARB_LOG_INFO("Create: Range Sensor %s with type: %s", prim.GetPath().GetString().c_str(),
                          component->getPrim().GetPrim().GetTypeName().GetString().c_str());
            mComponents[prim.GetPath().GetString()] = std::move(component);
        }
    }

    virtual void onComponentChange(const pxr::UsdPrim& prim)
    {
        utils::BridgeApplicationBase<RangeSensorComponent>::onComponentChange(prim);
        // update properties of this prim (onComponentChange)
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            mComponents[prim.GetPath().GetString()]->onComponentChange();
        }
        // Also need to make sure all emitters get their functions called
        for (auto& component : mComponents)
        {
            UltrasonicSensor* uss = dynamic_cast<UltrasonicSensor*>(component.second.get());
            if (uss)
            {
                uss->onEmitterChange(prim);
                uss->onFiringGroupChange(prim);
            }
        }
    }

    LidarSensor* getLidarSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<LidarSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }

    UltrasonicSensor* getUltrasonicSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<UltrasonicSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }
    RadarSensor* getRadarSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<RadarSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }

private:
    void createDebugLineList(size_t size)
    {
        if (mShapeDebugLineBuffer == omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mShapeDebugLineBuffer = mDebugDrawPtr->allocateLineBuffer(size);
            mShapeDebugRenderInstanceBuffer = mDebugDrawPtr->allocateRenderInstanceBuffer(mShapeDebugLineBuffer, 1);
            float transform[16] = {};
            transform[0] = 1.f;
            transform[1 + 4] = 1.f;
            transform[2 + 8] = 1.f;
            transform[3 + 12] = 1.f;

            mDebugDrawPtr->setRenderInstance(mShapeDebugRenderInstanceBuffer, 0, &transform[0], 0);
        }
    }

    void releaseDebugLineList()
    {
        if (mShapeDebugLineBuffer != omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mDebugDrawPtr->deallocateLineBuffer(mShapeDebugLineBuffer);
            mDebugDrawPtr->deallocateRenderInstanceBuffer(mShapeDebugRenderInstanceBuffer);
            mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
            mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        }
    }

    omni::physx::IPhysx* mPhysxPtr = nullptr;
    omni::renderer::IDebugDraw* mDebugDrawPtr = nullptr;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;

    omni::renderer::LineBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    carb::events::ISubscriptionPtr mViewportUiEventSub;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;
};
}
}
}
