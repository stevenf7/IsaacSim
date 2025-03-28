// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.


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

    m.doc() = R"pbdoc(
        Internal interface that is automatically called when the extension is loaded so that Omnigraph nodes are registered.

        Example:

            # import  isaacsim.sensors.rtx.bindings._isaacsim_sensors_rtx as _isaacsim_sensors_rtx

            # Acquire the interface
            interface = _isaacsim_sensors_rtx.acquire_interface()

            # Use the interface
            # ...

            # Release the interface
            _isaacsim_sensors_rtx.release_interface(interface)
    )pbdoc";

    defineInterfaceClass<isaacsim::sensors::rtx::IIsaacSimSensorsRtx>(m, "IIsaacSimSensorsRtx", "acquire_interface", "release_interface");
}
}
