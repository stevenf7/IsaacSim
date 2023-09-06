// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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


#define RCL_ERROR_MSG(caller, called)                                                                                  \
    do                                                                                                                 \
    {                                                                                                                  \
        CARB_LOG_ERROR("[" #caller "] error in " #called ": %s", rcutils_get_error_string().str);                      \
        rcl_reset_error();                                                                                             \
    } while (0)


#define RCL_WARN_MSG(caller, called)                                                                                   \
    do                                                                                                                 \
    {                                                                                                                  \
        CARB_LOG_WARN("[" #caller "] warning in " #called ": %s", rcutils_get_error_string().str);                     \
        rcl_reset_error();                                                                                             \
    } while (0)
