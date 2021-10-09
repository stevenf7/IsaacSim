// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <optional>

namespace omni
{
namespace isaac
{
namespace motion_planning
{

enum FrameElement
{
    ORIG = 0,
    AXIS_X,
    AXIS_Y,
    AXIS_Z,
    NUM_FRAME_ELEMENTS
};


struct Approach
{
    carb::Float3 direction;
    double standoff;
    double std_dev;

    Approach(const carb::Float3& direction, double standoff, double std_dev)
        : direction(direction), standoff(standoff), std_dev(std_dev)
    {
    }
};

struct Command
{
    carb::Float3 target;
    std::optional<Approach> approach;
    std::optional<double> user_weight;

    Command()
    {
    } // Default constructor doesn't initialize.
    explicit Command(const carb::Float3& target) : target(target)
    {
    }
    Command(const carb::Float3& target, const Approach& approach) : target(target), approach(approach)
    {
    }
};


struct PartialPoseCommand
{
    std::vector<std::optional<Command>> commands;

    PartialPoseCommand() : commands(FrameElement::NUM_FRAME_ELEMENTS)
    {
    }
};

struct MotionPlanning
{
    CARB_PLUGIN_INTERFACE("omni::isaac::motion_planning::MotionPlanning", 0, 1);

    size_t(CARB_ABI* registerRmp)(std::string robotUrdfPath,
                                  std::string robotDescriptorPath,
                                  std::string rmpFlowCommonPath,
                                  std::string primPath,
                                  std::string controlFrame,
                                  bool verbose);
    void(CARB_ABI* unregisterRmp)(size_t handle);
    void(CARB_ABI* setTargetGlobal)(size_t handle, carb::Float3 position, carb::Float4 rotation);
    void(CARB_ABI* setTargetLocal)(size_t handle, carb::Float3 position, carb::Float4 rotation);
    void(CARB_ABI* goLocal)(size_t handle, PartialPoseCommand p);
    std::vector<dynamic_control::DcTransform>(CARB_ABI* updateGetRelativePoses)(
        size_t handle, std::vector<std::pair<dynamic_control::DcHandle, std::string>> handles);
    std::vector<double>(CARB_ABI* getError)(size_t handle);
    std::vector<carb::Float3>(CARB_ABI* getRMPState)(size_t handle);
    std::vector<carb::Float3>(CARB_ABI* getRMPTarget)(size_t handle);
    void(CARB_ABI* setDefaultConfig)(size_t handle, const std::vector<double>& config);
    void(CARB_ABI* setFrequency)(size_t handle, const float frequency);
    void(CARB_ABI* addObstacle)(size_t handle, std::string primPath, int type, carb::Float3 scale);
    void(CARB_ABI* updateObstacle)(size_t handle, std::string primPath);
    void(CARB_ABI* removeObstacle)(size_t handle, std::string primPath);
    void(CARB_ABI* enableObstacle)(size_t handle, std::string primPath);
    void(CARB_ABI* disableObstacle)(size_t handle, std::string primPath);
};
}
}
}
