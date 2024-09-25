// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

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
 * Print `rcl` current error string as ERROR.
 *
 * @param caller Class, method, function, etc. from which the code is called.
 * @param called Called code (method, function, etc.).
 */
#define RCL_ERROR_MSG(caller, called)                                                                                  \
    do                                                                                                                 \
    {                                                                                                                  \
        printf("[" #caller "] error in " #called ": %s\n", rcutils_get_error_string().str);                            \
        rcl_reset_error();                                                                                             \
    } while (0)

/**
 * Print `rcl` current error string as WARNING.
 *
 * @param caller Class, method, function, etc. from which the code is called.
 * @param called Called code (method, function, etc.).
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
