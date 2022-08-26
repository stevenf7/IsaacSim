// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/logging/Log.h>

#include <packages/engine_c_api/isaac_c_api.h>

#include <dlfcn.h>
#include <functional>

namespace
{
#define DEFINEBINDING(ExFunc) std::function<ExFunc##_binding> ExFunc;
#define CREATEBINDING(ExFunc) typedef __typeof__(ExFunc) ExFunc##_binding;
#define BINDFUNCTION(ExFunc, handle) ExFunc = reinterpret_cast<ExFunc##_binding*>(dlsym(handle, #ExFunc));
#define INVOKE(ExFunc) omni::isaac::robot_engine_bridge::ExFunc
};


namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief Returns true if the error code is set to success.
 *
 * @param code
 * @return true
 * @return false
 */
inline bool checkErrorCode(const isaac_error_t& code)
{
    return code == isaac_error_t::isaac_error_success;
}


CREATEBINDING(isaac_create_application);
CREATEBINDING(isaac_destroy_application);
CREATEBINDING(isaac_start_application);
CREATEBINDING(isaac_stop_application);
CREATEBINDING(isaac_create_message);
CREATEBINDING(isaac_destroy_message);
CREATEBINDING(isaac_publish_message);
CREATEBINDING(isaac_receive_latest_new_message);
CREATEBINDING(isaac_release_message);
CREATEBINDING(isaac_get_time);
CREATEBINDING(isaac_get_pose);
CREATEBINDING(isaac_set_pose);
CREATEBINDING(isaac_get_parameter);
CREATEBINDING(isaac_set_parameter);
CREATEBINDING(isaac_set_parameter_from_string);
CREATEBINDING(isaac_get_message_json);
CREATEBINDING(isaac_read_message_json);
CREATEBINDING(isaac_write_message_json);
CREATEBINDING(isaac_set_message_auto_convert);
CREATEBINDING(isaac_get_message_acqtime);
CREATEBINDING(isaac_set_message_acqtime);
CREATEBINDING(isaac_get_message_pubtime);
CREATEBINDING(isaac_get_message_proto_id);
CREATEBINDING(isaac_set_message_proto_id);
CREATEBINDING(isaac_read_message_proto_segments);
CREATEBINDING(isaac_set_message_proto_segments);
CREATEBINDING(isaac_message_get_buffers);
CREATEBINDING(isaac_message_append_buffer);
CREATEBINDING(isaac_get_external_time_difference);
CREATEBINDING(isaac_create_null_json);
CREATEBINDING(isaac_create_null_const_json);
CREATEBINDING(isaac_get_error_message);

/**
 * @brief Manages the pointers to Isaac C Api functions
 *
 */
class IsaacCApi
{
public:
    /**
     * @brief Construct a new Isaac C Api object
     *
     */
    IsaacCApi()
    {
        g_c_api_handle = dlopen("libisaac_c_api.so", RTLD_LAZY | RTLD_DEEPBIND);
        if (!g_c_api_handle)
        {
            CARB_LOG_ERROR("libisaac_c_api.so dlopen failed");
        }
        BINDFUNCTION(isaac_create_application, g_c_api_handle);
        BINDFUNCTION(isaac_destroy_application, g_c_api_handle);
        BINDFUNCTION(isaac_start_application, g_c_api_handle);
        BINDFUNCTION(isaac_stop_application, g_c_api_handle);
        BINDFUNCTION(isaac_create_message, g_c_api_handle);
        BINDFUNCTION(isaac_destroy_message, g_c_api_handle);
        BINDFUNCTION(isaac_publish_message, g_c_api_handle);
        BINDFUNCTION(isaac_receive_latest_new_message, g_c_api_handle);
        BINDFUNCTION(isaac_release_message, g_c_api_handle);
        BINDFUNCTION(isaac_get_time, g_c_api_handle);
        BINDFUNCTION(isaac_get_pose, g_c_api_handle);
        BINDFUNCTION(isaac_set_pose, g_c_api_handle);
        BINDFUNCTION(isaac_get_parameter, g_c_api_handle);
        BINDFUNCTION(isaac_set_parameter, g_c_api_handle);
        BINDFUNCTION(isaac_set_parameter_from_string, g_c_api_handle);
        BINDFUNCTION(isaac_get_message_json, g_c_api_handle);
        BINDFUNCTION(isaac_read_message_json, g_c_api_handle);
        BINDFUNCTION(isaac_write_message_json, g_c_api_handle);
        BINDFUNCTION(isaac_set_message_auto_convert, g_c_api_handle);
        BINDFUNCTION(isaac_get_message_acqtime, g_c_api_handle);
        BINDFUNCTION(isaac_set_message_acqtime, g_c_api_handle);
        BINDFUNCTION(isaac_get_message_pubtime, g_c_api_handle);
        BINDFUNCTION(isaac_get_message_proto_id, g_c_api_handle);
        BINDFUNCTION(isaac_set_message_proto_id, g_c_api_handle);
        BINDFUNCTION(isaac_read_message_proto_segments, g_c_api_handle);
        BINDFUNCTION(isaac_set_message_proto_segments, g_c_api_handle);
        BINDFUNCTION(isaac_message_get_buffers, g_c_api_handle);
        BINDFUNCTION(isaac_message_append_buffer, g_c_api_handle);
        BINDFUNCTION(isaac_get_external_time_difference, g_c_api_handle);
        BINDFUNCTION(isaac_create_null_json, g_c_api_handle);
        BINDFUNCTION(isaac_create_null_const_json, g_c_api_handle);
        BINDFUNCTION(isaac_get_error_message, g_c_api_handle);
    }
    /**
     * @brief Destroy the Isaac C Api object
     *
     */
    ~IsaacCApi()
    {
        if (g_c_api_handle)
        {
            dlclose(g_c_api_handle);
        }
        g_c_api_handle = nullptr;
    }
    DEFINEBINDING(isaac_create_application);
    DEFINEBINDING(isaac_destroy_application);
    DEFINEBINDING(isaac_start_application);
    DEFINEBINDING(isaac_stop_application);
    DEFINEBINDING(isaac_create_message);
    DEFINEBINDING(isaac_destroy_message);
    DEFINEBINDING(isaac_publish_message);
    DEFINEBINDING(isaac_receive_latest_new_message);
    DEFINEBINDING(isaac_release_message);
    DEFINEBINDING(isaac_get_time);
    DEFINEBINDING(isaac_get_pose);
    DEFINEBINDING(isaac_set_pose);
    DEFINEBINDING(isaac_get_parameter);
    DEFINEBINDING(isaac_set_parameter);
    DEFINEBINDING(isaac_set_parameter_from_string);
    DEFINEBINDING(isaac_get_message_json);
    DEFINEBINDING(isaac_read_message_json);
    DEFINEBINDING(isaac_write_message_json);
    DEFINEBINDING(isaac_set_message_auto_convert);
    DEFINEBINDING(isaac_get_message_acqtime);
    DEFINEBINDING(isaac_set_message_acqtime);
    DEFINEBINDING(isaac_get_message_pubtime);
    DEFINEBINDING(isaac_get_message_proto_id);
    DEFINEBINDING(isaac_set_message_proto_id);
    DEFINEBINDING(isaac_read_message_proto_segments);
    DEFINEBINDING(isaac_set_message_proto_segments);
    DEFINEBINDING(isaac_message_get_buffers);
    DEFINEBINDING(isaac_message_append_buffer);
    DEFINEBINDING(isaac_get_external_time_difference);
    DEFINEBINDING(isaac_create_null_json);
    DEFINEBINDING(isaac_create_null_const_json);
    DEFINEBINDING(isaac_get_error_message);

private:
    void* g_c_api_handle = nullptr;
};
}
}
}
