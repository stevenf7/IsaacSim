// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#pragma once
#if defined(_WIN32)
#    include <usdrt/scenegraph/usd/usd/stage.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wunused-variable"
#    include <usdrt/scenegraph/usd/usd/stage.h>
#    pragma GCC diagnostic pop
#endif

#include <string>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @class ComponentBase
 * @brief Base class template for USD prim-attached components in an Application
 * @details
 * ComponentBase provides the foundational structure for components that are attached to USD prims
 * within an Application. It manages the lifecycle, timing, and state of components while providing
 * virtual interfaces for key operations like initialization, updates, and event handling.
 *
 * @tparam PrimType The USD prim type that this component will be attached to
 *
 * @note All derived components must implement the pure virtual functions
 * @warning Components must be properly initialized with a valid USD prim and stage before use
 */
template <class PrimType>
class ComponentBase
{
public:
    /**
     * @brief Virtual destructor ensuring proper cleanup of derived classes
     */
    virtual ~ComponentBase() = default;

    /**
     * @brief Initializes the component with USD prim and stage references
     * @details Sets up the component's USD context and prepares it for execution
     *
     * @param[in] prim The USD prim to attach this component to
     * @param[in] stage The USD stage containing the prim
     *
     * @post Component is initialized with valid USD prim and stage references
     * @post mDoStart is set to true, indicating the component is ready to start
     */
    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        mPrim = prim;
        mStage = stage;
        mDoStart = true;

        omni::fabric::IStageReaderWriter* iStageReaderWriter =
            carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
        uint64_t stageId = static_cast<uint64_t>(pxr::UsdUtilsStageCache::Get().GetId(stage).ToLongInt());
        omni::fabric::StageReaderWriterId stageInProgress = iStageReaderWriter->get(stageId);
        mUsdrtStage = usdrt::UsdStage::Attach(stageId, stageInProgress);
    }

    /**
     * @brief Pure virtual function called after simulation start
     * @details Implement this to define component behavior at simulation start
     */
    virtual void onStart() = 0;

    /**
     * @brief Called when simulation is stopped
     * @details Override this to implement cleanup or state reset behavior
     */
    virtual void onStop()
    {
    }

    /**
     * @brief Called during each physics simulation step
     * @details Override this to implement physics-based behavior
     *
     * @param[in] dt Time step size in seconds
     */
    virtual void onPhysicsStep(float dt)
    {
    }

    /**
     * @brief Called for each rendered frame
     * @details Override this to implement render-specific behavior or visual updates
     */
    virtual void onRenderEvent()
    {
    }

    /**
     * @brief Pure virtual function called every frame
     * @details Implement this to define the component's per-frame behavior
     */
    virtual void tick() = 0;

    /**
     * @brief Pure virtual function called when the component's prim changes
     * @details Implement this to handle USD prim attribute or relationship changes
     */
    virtual void onComponentChange() = 0;

    /**
     * @brief Updates the component's internal timing information
     * @details Maintains synchronized timing state across the component
     *
     * @param[in] timeSeconds Current simulation time in seconds
     * @param[in] dt Time step size in seconds
     * @param[in] timeNano Current simulation time in nanoseconds
     */
    virtual void updateTimestamp(double timeSeconds, double dt, int64_t timeNano)
    {
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
        this->mTimeNanoSeconds = timeNano;
    }

    /**
     * @brief Retrieves the component's USD prim
     * @return Reference to the component's USD prim
     */
    PrimType& getPrim()
    {
        return mPrim;
    }

    /**
     * @brief Checks if the component is enabled
     * @return true if the component is enabled, false otherwise
     */
    bool getEnabled()
    {
        return mEnabled;
    }

    /**
     * @brief Gets the component's sequence number
     * @return The component's sequence number
     */
    uint64_t getSequenceNumber()
    {
        return mSequenceNumber;
    }

    /** @brief Flag indicating whether onStart should be called */
    bool mDoStart = true;

protected:
    /** @brief USD prim reference storing component settings */
    PrimType mPrim;

    /** @brief Weak pointer to the USD stage containing the prim */
    pxr::UsdStageWeakPtr mStage = nullptr;

    /** @brief Runtime USD stage reference */
    usdrt::UsdStageRefPtr mUsdrtStage = nullptr;

    /** @brief Current simulation time in seconds */
    double mTimeSeconds = 0;

    /** @brief Current simulation time in nanoseconds */
    int64_t mTimeNanoSeconds = 0;

    /** @brief Time delta for current tick in seconds */
    double mTimeDelta = 0;

    /** @brief Component sequence number for ordering/identification */
    uint64_t mSequenceNumber = 0;

    /** @brief Component enabled state flag */
    bool mEnabled = true;
};

/**
 * @typedef Component
 * @brief Convenience typedef for ComponentBase specialized with pxr::UsdPrim
 */
typedef ComponentBase<pxr::UsdPrim> Component;

}
}
}
