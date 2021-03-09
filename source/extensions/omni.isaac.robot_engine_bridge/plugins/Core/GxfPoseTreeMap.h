
// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "gems/pose_tree/pose_tree.hpp"

#include <mutex>
#include <shared_mutex>
#include <string>
#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{

class GxfPoseTreeMap
{
public:
    void clear();

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findOrCreateNamedFrame(
        const std::string& path, nvidia::isaac::PoseTree& poseTree);

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findOrCreateUnnamedFrame(
        const std::string& path, nvidia::isaac::PoseTree& poseTree);

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findFrame(const std::string& path);

private:
    mutable std::shared_timed_mutex mMutex;
    std::unordered_map<std::string, nvidia::isaac::PoseTree::frame_t> mPoseUidMap;
};

}
}
}
}
