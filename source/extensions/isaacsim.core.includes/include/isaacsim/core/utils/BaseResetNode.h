// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/timeline/ITimeline.h>
#include <omni/timeline/TimelineTypes.h>
#include <omni/usd/UsdContext.h>

/**
 * @class BaseResetNode
 * @brief Base class for nodes that automatically reset their state when simulation is stopped.
 * @details
 * This class provides automatic reset functionality for nodes in the simulation graph.
 * It subscribes to the timeline event stream and triggers a reset when a stop event is received.
 * Derived classes must implement the reset() function to define their specific reset behavior.
 *
 * The class handles:
 * - Timeline event subscription management
 * - Automatic cleanup of subscriptions
 * - Reset triggering on simulation stop
 *
 * @note This class uses RAII principles to manage timeline event subscriptions
 * @warning Derived classes must implement reset() or a compilation error will occur
 */
class BaseResetNode
{
public:
    /**
     * @brief Constructs a new BaseResetNode instance.
     * @details
     * Sets up the timeline event subscription to automatically trigger reset on simulation stop.
     * The subscription is created with the following characteristics:
     * - Listens for eStop events from the timeline
     * - Automatically triggers reset() when stop occurs
     * - Uses a unique handler name for identification
     *
     * @post Timeline event subscription is created and active
     * @post Timeline interface is cached and ready for use
     */
    BaseResetNode()
    {
        // When the node is created, we create a stage event subscription
        // The idea is that node is reset whenever stop is pressed
        mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
        mTimelineEventSub = carb::events::createSubscriptionToPopByType(
            mTimeline->getTimelineEventStream(),
            static_cast<carb::events::EventType>(omni::timeline::TimelineEventType::eStop),
            [this](carb::events::IEvent* e) { reset(); }, 0, "IsaacSimOGNTimelineEventHandler");
    }

    /**
     * @brief Virtual destructor to ensure proper cleanup of derived classes.
     * @details
     * Cleans up the timeline event subscription using RAII principles.
     * The subscription is automatically released when the object is destroyed.
     *
     * @note The timeline interface pointer is not explicitly cleaned up as it's managed by carb
     */
    virtual ~BaseResetNode()
    {
        mTimelineEventSub = nullptr;
    }

    /**
     * @brief Pure virtual function to reset the node's state.
     * @details
     * This function is called automatically when the simulation is stopped.
     * Derived classes must implement this function to define their specific reset behavior.
     *
     * @note This function is called from the timeline event handler thread
     * @warning Implementation must be thread-safe as it may be called asynchronously
     */
    virtual void reset() = 0;

private:
    /** @brief Subscription handle for timeline stop events */
    carb::events::ISubscriptionPtr mTimelineEventSub;

    /** @brief Cached pointer to the timeline interface */
    omni::timeline::ITimeline* mTimeline = nullptr;
};
