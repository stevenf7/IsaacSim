// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../generic/GenericSensor.h"
#include "../lidar/LidarSensor.h"
#include "../ultrasonic/UltrasonicSensor.h"
#include "RangeSensorComponent.h"
#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/utils/ScopedTimer.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/imgui/ImGui.h>
#include <carb/logging/Log.h>
#include <carb/renderer/Renderer.h>
#include <carb/settings/ISettings.h>

#include <isaacSensorSchema/isaacBaseSensor.h>
#include <omni/kit/KitUtils.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <PrimitiveDrawingHelper.h>
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

class RangeSensorManager : public utils::BridgeApplicationBase<RangeSensorComponent>
{
public:
    /**
     * @brief Construct a new Sensor Manager object
     *
     * @param physxPtr
     */
    RangeSensorManager(omni::physx::IPhysx* physxPtr,
                       omni::syntheticdata::SyntheticData* syntheticDataPtr,
                       carb::tasking::ITasking* taskingPtr)
    {
        mPhysxPtr = physxPtr;
        mSyntheticDataPtr = syntheticDataPtr;
        mTasking = taskingPtr;
    }

    /**
     * @brief Destroy the Sensor Manager object
     *
     */
    ~RangeSensorManager()
    {
    }
    /**
     * @brief Tick the application and all components
     *
     * @param dt
     */
    void tick(double dt)
    {
        std::unique_lock<std::mutex> lck(mComponentMtx);
        CARB_PROFILE_ZONE(0, "Isaac Range Sensor Tick");
        if (mComponents.size() == 0)
        {
            return;
        }

        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
            if (component.second->getEnabled())
            {
                component.second->preTick();
            }
        }
        // No need to make threads if there is only one sensor.
        if (mComponents.size() > 1)
        {
            mTasking->applyRange(mComponents.size(),
                                 [&](size_t index)
                                 {
                                     auto it = mComponents.begin();
                                     std::advance(it, index);

                                     if (it->second.get()->getEnabled())
                                     {
                                         it->second.get()->updateTimestamp(
                                             this->mTimeSeconds, dt, this->mTimeNanoSeconds);
                                         it->second.get()->tick();
                                     }
                                 });
        }
        else
        {
            for (auto& component : mComponents)
            {
                if (component.second->getEnabled())
                {
                    component.second.get()->updateTimestamp(this->mTimeSeconds, dt, this->mTimeNanoSeconds);
                    component.second->tick();
                }
            }
        }


        for (auto& component : mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second.get()->draw();
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
            component.second->onStop();
        }
    }
    /**
     * @brief Create a supported component in this manager
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim)
    {
        std::unique_ptr<RangeSensorComponent> component;

        if (prim.IsA<pxr::RangeSensorLidar>())
        {
            component = std::make_unique<LidarSensor>(mPhysxPtr, mSyntheticDataPtr);
        }
        else if (prim.IsA<pxr::RangeSensorUltrasonicArray>())
        {
            component = std::make_unique<UltrasonicSensor>(mPhysxPtr, mTasking);
        }
        else if (prim.IsA<pxr::RangeSensorGeneric>())
        {
            component = std::make_unique<GenericSensor>(mPhysxPtr);
        }

        if (component)
        {
            component->initialize(pxr::RangeSensorRangeSensor(prim), mStage);
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
    GenericSensor* getGenericSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<GenericSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }


private:
    omni::physx::IPhysx* mPhysxPtr = nullptr;
    omni::syntheticdata::SyntheticData* mSyntheticDataPtr = nullptr;

    carb::tasking::ITasking* mTasking = nullptr;
};
}
}
}
