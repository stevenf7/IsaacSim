// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
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
    CARB_PLUGIN_INTERFACE("omni::kit::IRunLoopRunnerImpl", 1, 0);

    /**
     * @brief Sets the time step size for manual stepping
     * @param[in] dt Time step size in seconds
     * @param[in] name Identifier for the run loop instance
     */
    void(CARB_ABI* setManualStepSize)(double dt, std::string name);

    /**
     * @brief Enables or disables manual stepping mode
     * @param[in] enabled True to enable manual stepping, false for automatic
     * @param[in] name Identifier for the run loop instance
     */
    void(CARB_ABI* setManualMode)(bool enabled, std::string name);
};
}
}
