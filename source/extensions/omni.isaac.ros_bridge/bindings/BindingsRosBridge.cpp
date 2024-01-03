// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <pybind11/numpy.h>

#include <RosBridge.h>

CARB_BINDINGS("omni.isaac.ros_bridge.python")

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
}
}
}

namespace
{

PYBIND11_MODULE(_ros_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::ros_bridge;

    m.doc() = "Isaac ROS bridge bindings";

    {
        defineInterfaceClass<RosBridge>(m, "RosBridge", "acquire_ros_bridge_interface", "release_ros_bridge_interface");
    }
}
}
