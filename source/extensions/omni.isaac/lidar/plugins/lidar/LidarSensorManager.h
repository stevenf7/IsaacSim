#pragma once

#include "../core/SensorComponent.h"
#include "LidarSensor.h"
#include "plugins/bridge/BridgeApplication.h"
#include "plugins/core/ScopedTimer.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/fastcache/FastCache.h>
#include <carb/imgui/ImGui.h>
#include <carb/logging/Log.h>
#include <carb/physx/physx.h>
#include <carb/renderer/Renderer.h>
#include <carb/settings/ISettings.h>

#include <omni/kit/IEditor.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/KitUtils.h>
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
namespace lidar
{

/**
 * @brief Data used by a lidar task thread
 *
 */
struct LidarTaskData
{
    double timeSeconds;
    double timeNanoSeconds;
    double dt;
    LidarSensor* lidar;
};

/**
 * @brief Function called by each lidar task thread
 *
 */
auto lidarTaskFunction = [](carb::tasking::ITasking* tasking, void* taskArg) {
    LidarTaskData* taskData = reinterpret_cast<LidarTaskData*>(taskArg);
    taskData->lidar->updateTimestamp(taskData->timeSeconds, taskData->dt, taskData->timeNanoSeconds);
    taskData->lidar->tick();
};

class LidarSensorManager : public utils::BridgeApplicationBase<LidarSensor>
{
public:
    /**
     * @brief Construct a new Sensor Manager object
     *
     * @param physxPtr
     */
    LidarSensorManager(omni::renderer::IDebugDraw* debugDrawPtr,
                       carb::physics::PhysX* physxPtr,
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

        // mViewportUiEventSub = carb::events::createSubscriptionToPop(
        //     carb::getCachedInterface<omni::kit::IViewport>()->getViewportWindow(nullptr)->getUiDrawEventStream().get(),
        //     [this](carb::events::IEvent* e) { onUIDraw(e, omni::kit::getImGui()); }, 0, "Lidar viewport ui update");
    }

    /**
     * @brief Destroy the Sensor Manager object
     *
     */
    ~LidarSensorManager()
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
        // omni::isaac::utils::ScopedTimer T("LIDAR");

        if (mDoOnce == false)
        {
            for (auto& component : mComponents)
            {
                component.second->onStart();
            }
            mDoOnce = true;
        }
        else
        {
#if 1
            LidarTaskData* taskArray = new LidarTaskData[mComponents.size()];
            int index = 0;
            for (auto& component : mComponents)
            {
                taskArray[index].timeSeconds = this->mTimeSeconds;
                taskArray[index].timeNanoSeconds = this->mTimeNanoSeconds;
                taskArray[index].dt = dt;
                taskArray[index].lidar = component.second.get();

                carb::tasking::TaskDesc bigTask{};
                bigTask.priority = carb::tasking::Priority::eHigh;
                bigTask.task = lidarTaskFunction;
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
        }

        size_t mShapeDebugIndex = 0;
        bool shouldDraw = false;
        size_t count = 0;
        for (auto& component : mComponents)
        {
            if (component.second.get()->getDrawLidarPoints() || component.second.get()->getDrawLidarLines())
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
                if (component.second.get()->getDrawLidarPoints() || component.second.get()->getDrawLidarLines())
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
        this->mTimeNanoSeconds = mTimeSeconds * 1e9;
    }
    /**
     * @brief Run once the scene is stopped
     *
     */
    void stop()
    {
        // PxScene can change after stop is pressed so reset DoOnce bool to force OnStart to run
        mDoOnce = false;
        releaseDebugLineList();
    }
    /**
     * @brief Create a supported component in this manager
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim)
    {
        for (auto&& child : prim.GetAllDescendants())
        {
            if (child.IsA<pxr::LidarSchemaLidar>())
            {
                std::unique_ptr<LidarSensor> component = std::make_unique<LidarSensor>();
                CARB_LOG_INFO("Create Lidar at %s", child.GetPath().GetString().c_str());
                component->initialize(mPhysxPtr, mFastCachePtr, pxr::LidarSchemaLidar(child), mStage);
                mComponents[child.GetPath().GetString()] = std::move(component);
                mDoOnce = false;
            }
        }

        if (prim.IsA<pxr::LidarSchemaLidar>())
        {
            std::unique_ptr<LidarSensor> component = std::make_unique<LidarSensor>();
            CARB_LOG_INFO("Create Lidar at %s", prim.GetPath().GetString().c_str());
            component->initialize(mPhysxPtr, mFastCachePtr, pxr::LidarSchemaLidar(prim), mStage);
            mComponents[prim.GetPath().GetString()] = std::move(component);
            mDoOnce = false;
        }
    }
    LidarSensor* getSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return mComponents[prim.GetPath().GetString()].get();
            }
            else
            {
                return nullptr;
            }
        }
        else
        {
            return nullptr;
        }
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

    carb::physics::PhysX* mPhysxPtr = nullptr;
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
