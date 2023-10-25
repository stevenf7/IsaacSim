// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

namespace omni
{
namespace kit
{

class IRendererRunLoopGate;
class SlidingMaximum;

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

    void setTargetFPS(double fps);

    bool isActive() const;
    void setActive(bool active);

private:
    /**
     * @brief Create or delete present thread subscription
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
