// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <isaacsim/xr/input_devices/IsaacSimHandTrackerCAPI.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>

using Clock = std::chrono::steady_clock;

static std::atomic<bool> g_initialized{ false };
static Clock::time_point g_startTime;

extern "C"
{

#if !defined(_MSC_VER)
#    define ISAACSIM_USED __attribute__((used))
#else
#    define ISAACSIM_USED
#endif

    ISAACSIM_HANDTRACKER_API ISAACSIM_USED bool IsaacSimHandTracker_Initialize(void)
    {
        g_startTime = Clock::now();
        g_initialized.store(true, std::memory_order_release);
        return true;
    }

    // NOLINTNEXTLINE(readability-identifier-naming)
    ISAACSIM_HANDTRACKER_API ISAACSIM_USED bool IsaacSimHandTracker_GetData(IsaacSimHandJointPose* out_joint_poses,
                                                                            int outJointPoseCount)
    {
        if (!g_initialized.load(std::memory_order_acquire))
        {
            return false;
        }
        if (out_joint_poses == nullptr || outJointPoseCount <= 0)
        {
            return false;
        }

        const int totalRequired = ISAACSIM_HAND_COUNT * ISAACSIM_HAND_JOINT_COUNT;
        const int count = (outJointPoseCount < totalRequired) ? outJointPoseCount : totalRequired;

        const double t = std::chrono::duration<double>(Clock::now() - g_startTime).count();


        // Fill left hand then right hand with slightly offset trajectories
        for (int hand = 0; hand < ISAACSIM_HAND_COUNT; ++hand)
        {
            const int handBase = hand * ISAACSIM_HAND_JOINT_COUNT;
            for (int j = 0; j < ISAACSIM_HAND_JOINT_COUNT; ++j)
            {
                const int idx = handBase + j;
                if (idx >= count)
                {
                    break;
                }
                IsaacSimHandJointPose& p = out_joint_poses[idx];

                // Simple animated circle per joint with slight phase offset; different radius per hand
                const double phase = 0.2 * j + 0.5 * hand;
                const float radius = hand == 0 ? 0.10f : 0.12f;
                const float x = static_cast<float>(radius * std::cos(t + phase));
                const float y = static_cast<float>(radius * std::sin(t + phase));
                const float z = static_cast<float>(0.02 * j + 0.01f * hand);
                p.position[0] = x;
                p.position[1] = y;
                p.position[2] = z;

                // Orientation as a unit quaternion rotating slowly around Z
                const float angle = static_cast<float>(0.5 * t + 0.1 * j + 0.05f * hand);
                const float half = 0.5f * angle;
                const float s = std::sin(half);
                const float c = std::cos(half);
                // quaternion (w, x, y, z)
                p.orientation[0] = c;
                p.orientation[1] = 0.0f;
                p.orientation[2] = 0.0f;
                p.orientation[3] = s;

                p.radius = 0.01234f + 0.001f * hand;
                p.locationFlags = ISAACSIM_HAND_JOINT_LOCATION_FLAGS_POSITION_VALID |
                                  ISAACSIM_HAND_JOINT_LOCATION_FLAGS_ORIENTATION_VALID |
                                  ISAACSIM_HAND_JOINT_LOCATION_FLAGS_POSITION_TRACKED |
                                  ISAACSIM_HAND_JOINT_LOCATION_FLAGS_ORIENTATION_TRACKED;
            }
        }

        return true;
    }

    ISAACSIM_HANDTRACKER_API ISAACSIM_USED void IsaacSimHandTracker_Shutdown(void)
    {
        g_initialized.store(false, std::memory_order_release);
    }

} // extern "C"
