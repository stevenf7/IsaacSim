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
#include <carb/settings/ISettings.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IEditor.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/KitUtils.h>
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
     * @param dynamicControlPtr
     */
    LidarSensorManager(omni::kit::IEditor* editor,
                       carb::physics::PhysX* physxPtr,
                       omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                       carb::fastcache::FastCache* fastCachePtr,
                       carb::tasking::ITasking* taskingPtr)
    {
        mEditor = editor;
        mPhysxPtr = physxPtr;
        mDynamicControlPtr = dynamicControlPtr;
        mFastCachePtr = fastCachePtr;
        mTasking = taskingPtr;
        mTaskCounter = mTasking->createCounter();


        mViewportUiEventSub = carb::events::createSubscriptionToPop(
            carb::getCachedInterface<omni::kit::IViewport>()->getViewportWindow(nullptr)->getUiDrawEventStream().get(),
            [this](carb::events::IEvent* e) { onUIDraw(e, omni::kit::getImGui()); }, 0, "Lidar viewport ui update");
    }

    /**
     * @brief Destroy the Sensor Manager object
     *
     */
    ~LidarSensorManager()
    {
        mTasking->yieldUntilCounter(mTaskCounter);
        releaseDebugLineList();
        mTasking->destroyCounter(mTaskCounter);
    }
    /**
     * @brief Tick the application and all components
     *
     * @param dt
     */
    void tick(double dt)
    {
        // omni::isaac::utils::ScopedTimer T("LIDAR");

        if (mDoOnce == false)
        {
            for (auto& component : mComponents)
            {
                component.second->onStart();
            }
            mDoOnce = true;
            releaseDebugLineList();
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
            return mComponents[prim.GetPath().GetString()].get();
        }
        else
        {
            return nullptr;
        }
    }


private:
    void createDebugLineList()
    {
        if (!mDebugLineList)
        {
            carb::renderer::SceneId id = omni::usd::UsdContext::getContext()->getRendererScene();
            carb::renderer::LineSettings lineSettings;
            lineSettings.enableDepthTest = true;
            lineSettings.width =
                0.01f / (float)UsdGeomGetStageMetersPerUnit(omni::usd::UsdContext::getContext()->getStage());
            mDebugLineList = mEditor->getRenderer()->createLineList(mEditor->getRenderContext(), id, lineSettings);

            mDebugLineVector.reserve(65535);
        }
    }

    void releaseDebugLineList()
    {
        if (mDebugLineList)
        {
            mEditor->getRenderer()->destroyLineList(mEditor->getRenderContext(), mDebugLineList);
            mDebugLineList = nullptr;

            mDebugLineVector.resize(0);
            mDebugLineVector.shrink_to_fit();
        }
    }


    void onUIDraw(carb::events::IEvent* e, carb::imgui::ImGui* imGui)
    {
        mTasking->yieldUntilCounter(mTaskCounter);
        mDebugLineVector.clear();

        for (auto& component : mComponents)
        {
            if (component.second.get()->getDrawLidarPoints())
            {
                auto& debugLines = component.second.get()->getDebugLines();
                for (const auto& line : debugLines)
                {
                    mDebugLineVector.push_back(line);
                }
            }
        }

        if (!mDebugLineVector.empty())
        {
            createDebugLineList();

            mEditor->getRenderer()->updateLineList(mEditor->getRenderContext(), mDebugLineList, mDebugLineVector.data(),
                                                   mDebugLineVector.size(), nullptr, 0);
        }
    }

    carb::physics::PhysX* mPhysxPtr = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::kit::IEditor* mEditor = nullptr;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;

    carb::renderer::LineList* mDebugLineList = nullptr;
    std::vector<carb::renderer::Line> mDebugLineVector;
    carb::events::ISubscriptionPtr mViewportUiEventSub;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;
};
}
}
}
