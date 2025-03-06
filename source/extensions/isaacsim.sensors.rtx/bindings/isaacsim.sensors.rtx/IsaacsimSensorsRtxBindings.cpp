// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <isaacsim/sensors/rtx/IIsaacSimSensorsRtx.h>

CARB_BINDINGS("isaacsim.sensors.rtx.python")

namespace
{

PYBIND11_MODULE(_isaacsim_sensors_rtx, m)
{
    // clang-format off
    using namespace carb;

    m.doc() = "pybind11 isaacsim.sensors.rtx bindings";

    defineInterfaceClass<isaacsim::sensors::rtx::IIsaacSimSensorsRtx>(m, "IIsaacSimSensorsRtx", "acquire_interface", "release_interface");
}
}
