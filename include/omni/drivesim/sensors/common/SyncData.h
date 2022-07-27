// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <condition_variable>

namespace carb
{
namespace tasking
{
struct ITasking;
class Counter;
} // namespace tasking
} // namespace carb

struct SyncData
{
    bool connected{ false };
    std::mutex mutex;
    bool ready{ true };
    std::condition_variable cv;
    carb::tasking::Counter* taskingCounter{ nullptr };
};

inline void procFinished(SyncData* syncData, const bool checkConnection = false)
{
    if (syncData)
    {
        std::lock_guard<std::mutex> lk(syncData->mutex);
        if (!(checkConnection && syncData->connected))
        {
            syncData->ready = true;
            syncData->cv.notify_all();
        }
    }
}

inline void nodeConnected(SyncData* syncData)
{
    if (syncData)
    {
        std::lock_guard<std::mutex> lk(syncData->mutex);
        syncData->connected = true;
    }
}

inline void syncWait(SyncData* syncData)
{
    if (syncData)
    {
        std::unique_lock<std::mutex> lk(syncData->mutex);
        while (!syncData->ready)
        {
            syncData->cv.wait(lk);
        }
        syncData->ready = false;
    }
}
