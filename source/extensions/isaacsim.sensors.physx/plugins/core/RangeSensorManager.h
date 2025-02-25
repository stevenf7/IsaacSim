// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
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
#include "../lightbeam_sensor/LightBeamSensor.h"
#include "RangeSensorComponent.h"
#include "isaacsim/core/utils/ScopedTimer.h"
#include "omni/isaac/bridge/BridgeApplication.h"

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

namespace isaacsim
{
namespace sensors
{
namespace physx
{

/**
 * @class RangeSensorManager
 * @brief Manager class for handling multiple range sensor components in the simulation
 * @details This class manages the lifecycle and updates of various range sensor types including
 *          Lidar sensors, generic range sensors, and light beam sensors. It handles sensor
 *          initialization, updates, and cleanup while providing thread-safe access to sensor data.
 *          The manager supports parallel processing of multiple sensors and ensures proper
 *          synchronization with the physics simulation timeline.
 */
class RangeSensorManager : public isaacsim::core::utils::BridgeApplicationBase<RangeSensorComponent>
{
public:
    /**
     * @brief Constructs a new Sensor Manager object
     * @param[in] physxPtr Pointer to the PhysX interface for physics simulation
     * @param[in] syntheticDataPtr Pointer to the synthetic data interface for additional sensor data
     * @param[in] taskingPtr Pointer to the tasking interface for parallel processing
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
     * @brief Virtual destructor for proper cleanup
     */
    ~RangeSensorManager() = default;

    /**
     * @brief Updates all sensor components after each physics simulation step
     * @details Processes each enabled sensor component, updating their timestamps and
     *          triggering their physics step handlers. Also manages the initialization
     *          of components that haven't started yet.
     * @param[in] dt The time step duration in seconds
     */
    void onPhysicsStep(const double& dt)
    {
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
                component.second.get()->updateTimestamp(this->mTimeSeconds, dt, this->mTimeNanoSeconds);
                component.second->onPhysicsStep();
            }
        }
        this->mTimeSeconds += dt;
        this->mTimeNanoSeconds = static_cast<int64_t>(mTimeSeconds * 1e9);

        // update timestep
    }

    /**
     * @brief Updates all sensor components during the simulation tick
     * @details Processes each enabled sensor component in parallel if multiple sensors exist.
     *          Handles component initialization, pre-tick operations, main tick updates,
     *          and visualization drawing.
     * @param[in] dt The time step duration in seconds
     */
    void tick(double dt)
    {
        std::unique_lock<std::mutex> lck(mComponentMtx);
        CARB_PROFILE_ZONE(0, "Isaac Range Sensor Tick");
        if (mComponents.empty())
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
     * @brief Handles cleanup when the simulation scene is stopped
     * @details Resets all components to ensure proper reinitialization on next start
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
     * @brief Creates a new sensor component based on the USD prim type
     * @param[in] prim The USD prim representing the sensor to create
     * @details Instantiates the appropriate sensor type (Lidar, Generic, or LightBeam)
     *          based on the prim type and initializes it with the provided parameters
     */
    void onComponentAdd(const pxr::UsdPrim& prim)
    {
        std::unique_ptr<RangeSensorComponent> component;

        if (prim.IsA<pxr::RangeSensorLidar>())
        {
            component = std::make_unique<LidarSensor>(mPhysxPtr, mSyntheticDataPtr);
        }
        else if (prim.IsA<pxr::RangeSensorGeneric>())
        {
            component = std::make_unique<GenericSensor>(mPhysxPtr);
        }
        else if (prim.IsA<pxr::IsaacSensorIsaacLightBeamSensor>())
        {
            component = std::make_unique<LightBeamSensor>(mPhysxPtr);
        }

        if (component)
        {
            component->initialize(pxr::RangeSensorRangeSensor(prim), mStage);
            CARB_LOG_INFO("Create: Range Sensor %s with type: %s", prim.GetPath().GetString().c_str(),
                          component->getPrim().GetPrim().GetTypeName().GetString().c_str());
            mComponents[prim.GetPath().GetString()] = std::move(component);
        }
    }

    /**
     * @brief Gets the list of supported sensor component types
     * @return Vector of strings containing the supported sensor type names
     */
    virtual std::vector<std::string> getComponentIsAVector() const
    {
        return { "RangeSensorLidar", "RangeSensorGeneric", "IsaacSensorIsaacLightBeamSensor" };
    }

    /**
     * @brief Handles property changes for a sensor component
     * @param[in] prim The USD prim whose properties have changed
     * @details Updates the corresponding sensor component with the new property values
     */
    virtual void onComponentChange(const pxr::UsdPrim& prim)
    {
        isaacsim::core::utils::BridgeApplicationBase<RangeSensorComponent>::onComponentChange(prim);
        // update properties of this prim (onComponentChange)
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            mComponents[prim.GetPath().GetString()]->onComponentChange();
        }
    }

    /**
     * @brief Retrieves a Lidar sensor component associated with the given USD prim
     * @param[in] prim The USD prim associated with the desired Lidar sensor
     * @return Pointer to the LidarSensor component if found, nullptr otherwise
     */
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

    /**
     * @brief Retrieves a generic range sensor component associated with the given USD prim
     * @param[in] prim The USD prim associated with the desired generic sensor
     * @return Pointer to the GenericSensor component if found, nullptr otherwise
     */
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

    /**
     * @brief Retrieves a light beam sensor component associated with the given USD prim
     * @param[in] prim The USD prim associated with the desired light beam sensor
     * @return Pointer to the LightBeamSensor component if found, nullptr otherwise
     */
    LightBeamSensor* getLightBeamSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<LightBeamSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }

private:
    /**
     * @brief Pointer to the PhysX interface for physics simulation
     */
    omni::physx::IPhysx* mPhysxPtr = nullptr;

    /**
     * @brief Pointer to the synthetic data interface for additional sensor data
     */
    omni::syntheticdata::SyntheticData* mSyntheticDataPtr = nullptr;

    /**
     * @brief Pointer to the tasking interface for parallel processing
     */
    carb::tasking::ITasking* mTasking = nullptr;
};
}
}
}
