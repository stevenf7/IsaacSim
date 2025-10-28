// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

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
