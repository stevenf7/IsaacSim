// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "Component.h"

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @class ComponentManager
 * @brief Base class for managing USD-based components in an application
 * @details
 * ComponentManager provides the core interface for managing components within a USD stage.
 * It handles component lifecycle (creation, updates, deletion), stage management,
 * and application-level events. This class serves as the foundation for building
 * component-based applications that interact with USD stages.
 *
 * @note All pure virtual functions must be implemented by derived classes
 * @warning This class is not thread-safe by default; derived classes must implement
 *          their own thread safety mechanisms if needed
 */
class ComponentManager
{
public:
    /**
     * @brief Constructs a new ComponentManager instance
     */
    ComponentManager() = default;

    /**
     * @brief Virtual destructor for proper cleanup of derived classes
     */
    ~ComponentManager() = default;

    /**
     * @brief Initializes the manager with a USD stage
     * @details Sets up the stage reference for component management
     *
     * @param[in] stage Weak pointer to the USD stage to be managed
     * @post The manager is initialized with the provided stage
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage)
    {
        mStage = stage;
    }

    /**
     * @brief Updates the manager and all managed components
     * @details Pure virtual function that must be implemented by derived classes
     *          to define the update behavior of components
     *
     * @param[in] dt Time step in seconds since the last tick
     */
    virtual void tick(double dt) = 0;

    /**
     * @brief Initializes components from the current stage
     * @details Pure virtual function that must be implemented by derived classes
     *          to define how components are discovered and initialized from the stage
     */
    virtual void initComponents() = 0;

    /**
     * @brief Handles application start event
     * @details Optional callback that runs when the application starts
     *          Override this to implement custom start behavior
     */
    virtual void onStart()
    {
    }

    /**
     * @brief Handles application stop event
     * @details Optional callback that runs when the application stops
     *          Override this to implement custom stop behavior
     */
    virtual void onStop()
    {
    }

    /**
     * @brief Creates a new component for the given prim
     * @details Pure virtual function that must be implemented by derived classes
     *          to define component creation behavior
     *
     * @param[in] prim The USD prim to create a component for
     */
    virtual void onComponentAdd(const pxr::UsdPrim& prim) = 0;

    /**
     * @brief Updates a component when its corresponding prim changes
     * @details Pure virtual function that must be implemented by derived classes
     *          to define how components react to prim changes
     *
     * @param[in] prim The USD prim that changed
     */
    virtual void onComponentChange(const pxr::UsdPrim& prim) = 0;

    /**
     * @brief Removes a component and its associated resources
     * @details Pure virtual function that must be implemented by derived classes
     *          to define component cleanup behavior
     *
     * @param[in] primPath Path to the prim whose component should be removed
     */
    virtual void onComponentRemove(const pxr::SdfPath& primPath) = 0;

    /**
     * @brief Removes all components and performs cleanup
     * @details Pure virtual function that must be implemented by derived classes
     *          to define complete cleanup behavior
     */
    virtual void deleteAllComponents() = 0;

    /**
     * @brief Retrieves the managed USD stage
     * @return Weak pointer to the current USD stage
     */
    pxr::UsdStageWeakPtr getStage()
    {
        return mStage;
    }

protected:
    /** @brief Weak pointer to the managed USD stage */
    pxr::UsdStageWeakPtr mStage = nullptr;

    /** @brief Current simulation time in seconds */
    double mTimeSeconds = 0;

    /** @brief Current simulation time in nanoseconds */
    int64_t mTimeNanoSeconds = 0;

    /** @brief Time delta for current tick in seconds */
    double mTimeDelta = 0;
};
}
}
}
