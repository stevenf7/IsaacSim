// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

/** @file
 * @brief ROS 2 error handling macros
 * @details
 * This file provides utility macros for handling and reporting ROS Client Library (rcl)
 * errors in a consistent manner throughout the Isaac Sim ROS 2 bridge. The macros
 * facilitate error reporting with contextual information about where the error occurred.
 */
#pragma once

#include <carb/logging/Log.h>

#include <rcl/error_handling.h>
#include <rcl/rcl.h>
#include <rcutils/logging_macros.h>

#include <stdarg.h>
#include <stdio.h>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

/**
 * @def RCL_ERROR_MSG
 * @brief Macro for printing RCL errors with context
 * @details
 * Prints the current RCL error string as an ERROR level message, including
 * information about where the error occurred. After printing, it resets
 * the RCL error state to prevent error propagation.
 *
 * Usage example:
 * ```cpp
 * if (rcl_operation_failed) {
 *     RCL_ERROR_MSG(MyClass::MyMethod, rcl_operation);
 *     return false;
 * }
 * ```
 *
 * @param caller The context where the error occurred (e.g., class, method, function)
 * @param called The RCL operation that failed
 */
#define RCL_ERROR_MSG(caller, called)                                                                                  \
    do                                                                                                                 \
    {                                                                                                                  \
        printf("[" #caller "] error in " #called ": %s\n", rcutils_get_error_string().str);                            \
        rcl_reset_error();                                                                                             \
    } while (0)

/**
 * @def RCL_WARN_MSG
 * @brief Macro for printing RCL warnings with context
 * @details
 * Prints the current RCL error string as a WARNING level message, including
 * information about where the warning occurred. After printing, it resets
 * the RCL error state to prevent warning propagation.
 *
 * Usage example:
 * ```cpp
 * if (rcl_operation_suspicious) {
 *     RCL_WARN_MSG(MyClass::MyMethod, rcl_operation);
 *     // continue execution
 * }
 * ```
 *
 * @param caller The context where the warning occurred (e.g., class, method, function)
 * @param called The RCL operation that triggered the warning
 */
#define RCL_WARN_MSG(caller, called)                                                                                   \
    do                                                                                                                 \
    {                                                                                                                  \
        printf("[" #caller "] warning in " #called ": %s\n", rcutils_get_error_string().str);                          \
        rcl_reset_error();                                                                                             \
    } while (0)

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
