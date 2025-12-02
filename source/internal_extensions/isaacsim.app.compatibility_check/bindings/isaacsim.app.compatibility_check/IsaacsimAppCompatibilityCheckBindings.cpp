// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/app/compatibility_check/ICompatibilityCheck.h>

CARB_BINDINGS("isaacsim.app.compatibility_check")


namespace py = pybind11;

PYBIND11_MODULE(_compatibility_check, m)
{
    using namespace isaacsim::app::compatibility_check;

    m.doc() = R"doc(
    Isaac Sim compatibility check bindings

    This module provides bindings for the compatibility check interface.
    )doc";

    py::class_<RtxGpuInfo>(m, "RtxGpuInfo", "RTX GPU Info")
        .def(py::init<>())
        .def_readonly("device_uuid", &RtxGpuInfo::deviceUUID, "Unique device identifier (:obj:`str`)")
        .def_readonly("pci_bus_id", &RtxGpuInfo::pciBusId, "PCI bus identifier (:obj:`str`)")
        .def_readonly("device_id", &RtxGpuInfo::deviceId, "Unique identifier for the physical device (:obj:`str`)")
        .def_readonly("vendor_id", &RtxGpuInfo::vendorId, "Unique vendor identifier. NVIDIA 0x10DE (:obj:`str`)")
        .def_readonly("sub_sys_id", &RtxGpuInfo::subSysId, "PCI ID of the sub system, or zero if unavailable (:obj:`str`)")
        .def_readonly(
            "raytracing_supported", &RtxGpuInfo::raytracingSupported, "Whether ray tracing is supported (:obj:`bool`)")
        .def_readonly("raytracing_shader_feature", &RtxGpuInfo::raytracingShaderFeature,
                      "Whether non-vendor specific ray tracing is supported (:obj:`bool`)");

    carb::defineInterfaceClass<ICompatibilityCheckInterface>(m, "ICompatibilityCheckInterface",
                                                             "acquire_compatibility_check_interface",
                                                             "release_compatibility_check_interface")
        .def(
            "get_rtx_gpu_info",
            [](ICompatibilityCheckInterface& m, bool createGpuFoundation)
            {
                std::vector<RtxGpuInfo> rtxGpuInfos;
                bool returnValue = m.getRtxGpuInfo(rtxGpuInfos, createGpuFoundation);
                return std::make_tuple(returnValue, rtxGpuInfos);
            },
            R"doc(
                Get information about an RTX GPU.

                This method retrieves information about an RTX GPU, including its UUID, PCI bus ID, device ID, vendor ID,
                sub-system ID, ray tracing support, and ray tracing shader feature support.
            )doc");
}
