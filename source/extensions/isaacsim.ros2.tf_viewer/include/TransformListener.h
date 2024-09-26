// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once
#include <carb/Interface.h>

namespace omni
{
namespace isaac
{
namespace transform_listener
{

class ITransformListener
{
public:
    /// @private
    CARB_PLUGIN_INTERFACE("omni::isaac::transform_listener::ITransformListener", 1, 0);
    virtual bool initialize(const std::string& rosDistro) = 0;
    virtual void finalize() = 0;
    virtual bool spin() = 0;
    virtual void reset() = 0;
    virtual void getTransformations(const std::string& rootFrame) = 0;

    virtual const std::vector<std::string>& getFrames() = 0;
    virtual const std::vector<std::tuple<std::string, std::string>>& getRelations() = 0;
    virtual const std::unordered_map<std::string,
                                     std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>&
    getTransforms() = 0;
};

} // namespace transform_listener
} // namespace isaac
} // namespace omni
