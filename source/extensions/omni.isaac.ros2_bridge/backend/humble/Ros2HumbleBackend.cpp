// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Humble.h"
#include "rosidl_runtime_c/string_functions.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>

Ros2BackendHumble::Ros2BackendHumble(std::string pkgName, std::string msgSubfolder, std::string msgName)
    : Ros2Backend(pkgName, msgSubfolder, msgName)
{
}


void Ros2BackendHumble::set_timestamp(const int64_t nanoseconds, builtin_interfaces__msg__Time& time)
{
    // publish the input string to topic
    constexpr rcl_time_point_value_t kRemainder = RCL_S_TO_NS(1);
    const auto result = std::div(nanoseconds, kRemainder);
    if (result.rem >= 0)
    {
        time.sec = static_cast<std::int32_t>(result.quot);
        time.nanosec = static_cast<std::uint32_t>(result.rem);
    }
    else
    {
        time.sec = static_cast<std::int32_t>(result.quot - 1);
        time.nanosec = static_cast<std::uint32_t>(kRemainder + result.rem);
    }
}

void Ros2BackendHumble::set_string(const std::string& input, rosidl_runtime_c__String& output)
{
    rosidl_runtime_c__String__assign(&output, input.c_str());
}

void Ros2BackendHumble::set_header(const std::string& frame_id, const int64_t nanoseconds, std_msgs__msg__Header& header)
{
    set_string(frame_id.c_str(), header.frame_id);

    if (nanoseconds > 0)
    {
        set_timestamp(nanoseconds, header.stamp);
    }
    else
    {
        fprintf(
            stdout,
            "[Warning] Timestamp is invalid. Timestamp will be neglected for all published ROS CameraInfo messages\n");
    }
}
