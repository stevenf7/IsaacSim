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

#pragma once

#include <carb/Interface.h>

namespace isaacsim
{
namespace app
{
namespace compatibility_check
{

/**
 * @struct RtxGpuInfo
 * @brief Information about an RTX GPU.
 * @details
 * This struct contains information about an RTX GPU, including its UUID, PCI bus ID, device ID, vendor ID, sub-system
 * ID, ray tracing support, and ray tracing shader feature support.
 */
struct RtxGpuInfo
{
    /** @brief Unique device identifier. */
    std::string deviceUUID;
    /** @brief PCI bus identifier. */
    std::string pciBusId;
    /** @brief Unique identifier for the physical device. */
    std::string deviceId;
    /** @brief Unique vendor identifier. NVIDIA: 0x10DE. */
    std::string vendorId;
    /** @brief PCI ID of the sub system, or zero if unavailable. */
    std::string subSysId;
    /** @brief Whether ray tracing is supported. */
    bool raytracingSupported;
    /** @brief Whether non-vendor specific ray tracing is supported. */
    bool raytracingShaderFeature;
};

/**
 * @class ICompatibilityCheckInterface
 * @brief Compatibility check interface.
 * @details
 * Interface for a compatibility check that checks the compatibility of the system with Isaac Sim.
 */
class ICompatibilityCheckInterface
{
public:
    CARB_PLUGIN_INTERFACE("isaacsim::app::compatibility_check::ICompatibilityCheckInterface", 1, 0);

    /**
     * @brief Get information about an RTX GPU.
     * @param[out] rtxGpuInfos Vector of RTX GPU information.
     * @param[in] createGpuFoundation Whether to create a GPU foundation instance.
     * @return Whether the RTX GPU information was retrieved successfully.
     */
    virtual bool getRtxGpuInfo(std::vector<RtxGpuInfo>& rtxGpuInfos, const bool& createGpuFoundation) = 0;
};

} // namespace compatibility_check
} // namespace app
} // namespace isaacsim
