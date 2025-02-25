// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/dictionary/IDictionary.h>
#include <carb/events/EventsUtils.h>
#include <carb/tasking/TaskingUtils.h>

#include <chrono>
#include <cstddef>
#include <memory>

namespace omni
{
namespace kit
{

class IRendererRunLoopGate;
class SlidingMaximum;

/**
 * @brief Class for synchronizing multiple run loops
 * @details Provides functionality to synchronize multiple threads or run loops
 *          to a common timing source, typically the present/render thread.
 *          Supports frame rate control and timing adjustments.
 */
class RunLoopSynchronizer
{
public:
    RunLoopSynchronizer();

    ~RunLoopSynchronizer();

    /**
     * @brief Saves the present time and duration.
     */
    void presentPreNotify();

    /**
     * @brief Notifies the condition variable in `wait` that it has to wake up.
     * Saves the syncronization point.
     */
    void presentPostNotify();

    /**
     * @brief Waits for the present thread and syncs the calling thread to the
     * present thread.
     *
     * This function calculates how long it needs to wait using a Sliding
     * Maximum of the already passed time. It uses a high resolution clock to
     * wait until the desired frame duration is met. It starts by obtaining the
     * current time, and calculates the sliding maximum of the already passed
     * time, ignoring a specified number of outliers. The function then
     * determines if waiting is necessary by comparing the current time with the
     * computed time point it should wake up at.
     *
     * @param alreadyPassedNs The duration in nanoseconds that has already
     *                        passed.
     * @param slidingMaximumCount The number of recent durations to consider
     *                            when finding the sliding maximum.
     * @param slidingMaximumOutlierCount The number of outlier durations to
     *                                   ignore when finding the sliding
     *                                   maximum.
     * @param slidingMaximumToleranceFactor A multiplier for the average
     *                                      duration. Durations exceeding this
     *                                      are considered outliers.
     */
    void wait(float alreadyPassedNs,
              size_t slidingMaximumCount,
              size_t slidingMaximumOutlierCount,
              float slidingMaximumToleranceFactor);

    /**
     * @brief Sets the target frames per second
     * @param[in] fps Desired frame rate in frames per second
     */
    void setTargetFPS(double fps);

    /**
     * @brief Checks if the synchronizer is active
     * @return True if synchronization is active, false otherwise
     */
    bool isActive() const;

    /**
     * @brief Enables or disables synchronization
     * @param[in] active True to enable synchronization, false to disable
     */
    void setActive(bool active);

private:
    /**
     * @brief Sets up or tears down the present thread subscription
     * @details Creates or deletes subscriptions for present thread notifications
     *          based on current synchronization state
     */
    void _setupPresentThread();

    using Clock = std::chrono::high_resolution_clock;
    using Duration = Clock::duration;
    using TimePoint = Clock::time_point;

    carb::tasking::MutexWrapper m_presentMutex;
    Duration m_presentDuration;
    TimePoint m_presentStartTime;
    // All the threads will be synced to this time point.
    TimePoint m_presentCheckpointTime;

    carb::tasking::MutexWrapper m_targetMutex;
    Duration m_targetDuration;

    std::unique_ptr<IRendererRunLoopGate> m_gate;
    std::unique_ptr<SlidingMaximum> m_sliding;

    // Present thread
    carb::events::ISubscriptionPtr m_presentPreSubscription;
    carb::events::ISubscriptionPtr m_presentPostSubscription;
    // Present thread setting watch
    carb::dictionary::SubscriptionId* m_presentThreadEnabledSubscription = nullptr;

    bool m_isActive = false;
    double m_fps = -1.0f;
};
}
}
