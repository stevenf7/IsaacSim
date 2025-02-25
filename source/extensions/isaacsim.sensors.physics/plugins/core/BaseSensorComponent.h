// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "isaacsim/core/utils/UsdUtilities.h"
#include "omni/isaac/bridge/Component.h"

#include <isaacSensorSchema/isaacBaseSensor.h>

#include <string>
#include <vector>

/**
 * @namespace isaacsim
 * @brief Root namespace for Isaac Sim functionality.
 */
namespace isaacsim
{
/**
 * @namespace sensors
 * @brief Namespace containing sensor-related functionality.
 */
namespace sensors
{
/**
 * @namespace physics
 * @brief Namespace containing physics-based sensor implementations.
 */
namespace physics
{
/**
 * @brief Linear interpolation between two values.
 * @details Performs linear interpolation between start and end values based on the interpolation factor t.
 * The interpolation is calculated as: start + ((end - start) * t).
 *
 * @param[in] start Starting value for interpolation.
 * @param[in] end Ending value for interpolation.
 * @param[in] t Interpolation factor between 0.0 and 1.0.
 * @return The interpolated value.
 *
 * @note The interpolation factor t should be between 0.0 and 1.0 for expected results.
 */
inline float lerp(const float& start, const float& end, const float t)
{
    return start + ((end - start) * t);
}

/**
 * @class IsaacSensorComponentBase
 * @brief Base class template for non-RTX Isaac sensors.
 * @details
 * This class serves as the foundation for implementing non-RTX sensors in Isaac Sim.
 * It provides the basic structure and lifecycle methods that all sensors should implement.
 *
 * @tparam PrimType The USD prim type representing the sensor. This type parameter allows
 *                  different sensor implementations to use their specific USD prim types.
 *
 * @note This class inherits from ComponentBase to integrate with the Isaac Sim component system.
 */
template <class PrimType>
class IsaacSensorComponentBase : public isaacsim::core::utils::ComponentBase<PrimType>
{
public:
    /**
     * @brief Default constructor.
     * @details Constructs a new instance of the sensor component.
     */
    IsaacSensorComponentBase() = default;

    /**
     * @brief Virtual destructor.
     * @details Ensures proper cleanup of derived sensor classes.
     */
    ~IsaacSensorComponentBase() = default;

    /**
     * @brief Initializes the sensor component.
     * @details Sets up the sensor component with its USD prim and stage references.
     *
     * @param[in] prim USD prim representing the sensor.
     * @param[in] stage USD stage containing the prim.
     */
    virtual void initialize(const PrimType& prim, const pxr::UsdStageWeakPtr stage)
    {
        isaacsim::core::utils::ComponentBase<PrimType>::initialize(prim, stage);
    }

    /**
     * @brief Called when the sensor starts.
     * @details Handles sensor initialization when the component is started.
     *          Triggers onComponentChange to ensure proper initial state.
     */
    virtual void onStart()
    {
        onComponentChange();
    }

    /**
     * @brief Called when sensor component properties change.
     * @details Updates the sensor's enabled state when component properties are modified.
     */
    virtual void onComponentChange()
    {
        // base sensor on component change
        isaacsim::core::utils::safeGetAttribute(this->mPrim.GetEnabledAttr(), this->mEnabled);
    }

    /**
     * @brief Called before each tick to prepare sensor state.
     * @details Provides an opportunity to prepare the sensor state before the main tick update.
     *          Default implementation does nothing.
     */
    virtual void preTick()
    {
        return;
    }

    /**
     * @brief Pure virtual function called each tick to update sensor state.
     * @details This method must be implemented by derived classes to define the
     *          sensor's behavior during each simulation tick.
     */
    virtual void tick() = 0;

    /**
     * @brief Called each physics step to update sensor state.
     * @details Allows sensors to update their state based on physics simulation steps.
     *          Default implementation does nothing.
     */
    virtual void onPhysicsStep(){};

    /**
     * @brief Called when the sensor stops.
     * @details Handles cleanup when the sensor component is stopped.
     *          Default implementation does nothing.
     */
    virtual void onStop()
    {
    }

    /**
     * @brief Gets the parent prim of the sensor.
     * @details Retrieves the USD prim that is the parent of this sensor.
     *
     * @return USD prim that is the parent of this sensor.
     */
    pxr::UsdPrim getParentPrim()
    {
        return mParentPrim;
    }

protected:
    /**
     * @brief USD prim that is the parent of this sensor.
     * @details Stores a reference to the parent USD prim that contains this sensor.
     */
    pxr::UsdPrim mParentPrim;
};

/**
 * @typedef IsaacBaseSensorComponent
 * @brief Convenience typedef for IsaacSensorComponentBase with IsaacBaseSensor prim type.
 * @details Defines a commonly used specialization of IsaacSensorComponentBase using
 *          the IsaacBaseSensor prim type for basic sensor functionality.
 */
typedef IsaacSensorComponentBase<pxr::IsaacSensorIsaacBaseSensor> IsaacBaseSensorComponent;

}
}
}
