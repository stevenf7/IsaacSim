// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>


namespace omni
{
namespace kit
{

/**
 * @brief Interface for controlling the run loop execution
 * @details Provides functionality to control the simulation loop's execution mode
 *          and timing, allowing for manual stepping and mode control
 */
struct IRunLoopRunnerImpl
{
    CARB_PLUGIN_INTERFACE("omni::kit::IRunLoopRunnerImpl", 1, 1);

    /**
     * @brief Sets the time step size for manual stepping
     * @param[in] dt Time step size in seconds
     * @param[in] name Identifier for the run loop instance
     */
    void(CARB_ABI* setManualStepSize)(const double dt, const std::string& name);

    /**
     * @brief Enables or disables manual stepping mode
     * @param[in] enabled True to enable manual stepping, false for automatic
     * @param[in] name Identifier for the run loop instance
     */
    void(CARB_ABI* setManualMode)(const bool enabled, const std::string& name);

    /**
     * @brief Gets the manual mode for the run loop
     * @param[in] name Identifier for the run loop instance
     * @return True if manual mode is enabled, false otherwise
     */
    bool(CARB_ABI* getManualMode)(const std::string& name);
};
}
}
