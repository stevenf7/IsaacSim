// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <DynamicControlTypes.h>
#include <memory>
#include <unordered_map>

namespace std
{
// hash function for SdfPath
template <>
struct hash<pxr::SdfPath>
{
    size_t operator()(const pxr::SdfPath& path) const
    {
        return path.GetHash();
    }
};
}

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
constexpr uint64_t kHandleContextMask = 0xffffff0000000000;
constexpr uint64_t kHandleTypeMask = 0x000000ff00000000;
constexpr uint64_t kHandleObjectMask = 0x00000000ffffffff;

constexpr DcHandle makeHandle(uint64_t objectId, uint64_t typeId, uint64_t contextId)
{
    return objectId | (typeId << 32) | (contextId << 40);
}

constexpr uint32_t getHandleObjectId(DcHandle h)
{
    return static_cast<uint32_t>(h & kHandleObjectMask);
}

constexpr uint32_t getHandleTypeId(DcHandle h)
{
    return static_cast<uint32_t>((h & kHandleTypeMask) >> 32);
}

constexpr uint32_t getHandleContextId(DcHandle h)
{
    return static_cast<uint32_t>(h >> 40);
}

template <class T>
class Bucket
{
public:
    // bucket takes ownership
    uint32_t add(std::unique_ptr<T>&& obj)
    {
        uint32_t id = ++mNextId;
        mDict[id] = std::move(obj);
        return id;
    }

    T* get(uint32_t id) const
    {
        auto it = mDict.find(id);
        if (it != mDict.end())
        {
            return it->second.get();
        }
        else
        {
            return nullptr;
        }
    }

    void remove(uint32_t id)
    {
        auto it = mDict.find(id);
        if (it != mDict.end())
        {
            mDict.erase(it);
        }
    }

    void clear()
    {
        mDict.clear();
    }

private:
    // can convert this to a generational index if needed
    std::unordered_map<uint32_t, std::unique_ptr<T>> mDict;

    uint32_t mNextId = 0;
};

}
}
}
