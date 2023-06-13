// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/ros2_bridge/Ros2BridgeHumble.h>
#include <pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.ros2_humble_bridge.python")

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
}
}
}

namespace
{

PYBIND11_MODULE(_ros2_humble_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::ros2_bridge;

    m.doc() = "Isaac ROS2 bridge bindings";

    {
        defineInterfaceClass<Ros2BridgeHumble>(
            m, "Ros2BridgeHumble", "acquire_ros2_bridge_interface", "release_ros2_bridge_interface");
    }
}
}
