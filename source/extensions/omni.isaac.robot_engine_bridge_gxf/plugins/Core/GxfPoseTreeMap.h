
// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "extensions/atlas/atlas_frontend.hpp"
#include "gxf/core/gxf.h"

#include <mutex>
#include <shared_mutex>
#include <string>
#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{


class GxfPoseTreeMap
{
public:
    void setAtlas(const nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend>& atlas)
    {
        mAtlas = atlas;
    }

    void clear();

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findOrCreateNamedFrame(const std::string& path);

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findOrCreateUnnamedFrame(const std::string& path);

    nvidia::isaac::PoseTree::expected_t<nvidia::isaac::PoseTree::frame_t> findFrame(const std::string& path);

private:
    mutable std::shared_timed_mutex mMutex;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;
    std::unordered_map<std::string, nvidia::isaac::PoseTree::frame_t> mPoseUidMap;
};

}
}
}
