
// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "GxfPoseTreeMap.h"

#include "gems/pose_tree/pose_tree.hpp"

#include <carb/logging/Log.h>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{


void GxfPoseTreeMap::clear()
{
    std::unique_lock<std::shared_timed_mutex> lock(mMutex);
    // CARB_LOG_ERROR("Cleared");
    mPoseUidMap.clear();
}

nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> GxfPoseTreeMap::findOrCreateNamedFrame(
    const std::string& path)
{
    std::unique_lock<std::shared_timed_mutex> lock(mMutex);

    auto cacheEntry = mPoseUidMap.find(path);
    if (cacheEntry == mPoseUidMap.end())
    {
        // Check path name length
        if (static_cast<int32_t>(path.size()) > nvidia::isaac::PoseTree::kFrameNameMaximumLength)
        {
            CARB_LOG_ERROR("Prim %s path size %zu exceeds pose tree name limit %d", path.c_str(), path.size(),
                           nvidia::isaac::PoseTree::kFrameNameMaximumLength);
            return nvidia::isaac::PoseTree::unexpected_t(nvidia::isaac::PoseTree::Error::kInvalidArgument);
        }

        const auto maybeUid = mAtlas->pose_tree().findOrCreateFrame(path.c_str());
        if (maybeUid)
        {
            // CARB_LOG_WARN("Created named frame Prim %s", path.c_str());
            mPoseUidMap.emplace(path, maybeUid.value());
        }
        return maybeUid;
    }

    // CARB_LOG_WARN("Found named frame Prim %s, %zu", path.c_str(), cacheEntry->second);
    return cacheEntry->second;
}

nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> GxfPoseTreeMap::findOrCreateUnnamedFrame(
    const std::string& path)
{
    std::unique_lock<std::shared_timed_mutex> lock(mMutex);

    auto cacheEntry = mPoseUidMap.find(path);
    if (cacheEntry == mPoseUidMap.end())
    {
        const auto maybeUid = mAtlas->pose_tree().createFrame();
        if (maybeUid)
        {
            // CARB_LOG_WARN("Created unnamed frame Prim %s", path.c_str());
            mPoseUidMap.emplace(path, maybeUid.value());
        }
        return maybeUid;
    }

    // CARB_LOG_WARN("Found unnamed frame Prim %s, %zu", path.c_str(), cacheEntry->second);
    return cacheEntry->second;
}

nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> GxfPoseTreeMap::findFrame(const std::string& path)
{
    std::shared_lock<std::shared_timed_mutex> lock(mMutex);

    auto cacheEntry = mPoseUidMap.find(path);
    if (cacheEntry != mPoseUidMap.end())
    {
        return cacheEntry->second;
    }
    return nvidia::isaac::PoseTree::unexpected_t(nvidia::isaac::PoseTree::Error::kFrameNotFound);
}

}
}
}
