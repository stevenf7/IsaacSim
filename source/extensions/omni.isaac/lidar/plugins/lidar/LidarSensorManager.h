#pragma once

#include "../core/SensorComponent.h"
#include "LidarSensor.h"
#include "plugins/bridge/BridgeApplication.h"

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
                       carb::fastcache::FastCache* fastCache)
    {
        mEditor = editor;
        mPhysxPtr = physxPtr;
        mDynamicControlPtr = dynamicControlPtr;
        mFastCachePtr = fastCache;

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
        releaseDebugLineList();
    }
    /**
     * @brief Tick the application and all components
     *
     * @param dt
     */
    void tick(double dt)
    {
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
            for (auto& component : mComponents)
            {
                component.second.get()->updateTimestamp(this->mTimeSeconds, dt, this->mTimeNanoSeconds);
                component.second->tick();
            }
        }
        this->mTimeSeconds += dt;
        this->mTimeNanoSeconds = mTimeSeconds * 1e9;
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
                CARB_LOG_WARN("Create: Prim %s", child.GetPath().GetString().c_str());
                component->initialize(mPhysxPtr, mDynamicControlPtr, mFastCachePtr, pxr::LidarSchemaLidar(child), mStage);
                mComponents[child.GetPath().GetString()] = std::move(component);
            }
        }

        if (prim.IsA<pxr::LidarSchemaLidar>())
        {
            std::unique_ptr<LidarSensor> component = std::make_unique<LidarSensor>();
            CARB_LOG_WARN("Create: Prim %s", prim.GetPath().GetString().c_str());
            component->initialize(mPhysxPtr, mDynamicControlPtr, mFastCachePtr, pxr::LidarSchemaLidar(prim), mStage);
            mComponents[prim.GetPath().GetString()] = std::move(component);
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
        else
        {
            releaseDebugLineList();
        }
    }

    carb::physics::PhysX* mPhysxPtr = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::kit::IEditor* mEditor = nullptr;
    carb::fastcache::FastCache* mFastCachePtr = nullptr;

    carb::renderer::LineList* mDebugLineList = nullptr;
    std::vector<carb::renderer::Line> mDebugLineVector;
    carb::events::ISubscriptionPtr mViewportUiEventSub;
};
}
}
}
