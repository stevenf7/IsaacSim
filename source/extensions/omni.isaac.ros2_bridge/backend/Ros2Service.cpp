// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "Ros2Impl.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>

Ros2ServiceImpl::Ros2ServiceImpl(Ros2NodeBase* node, const char* service_name, const void* type, const Ros2QoSProfile& qos)
    : mNode(node), wait_set_initialized(false)
{
    mService = std::shared_ptr<rcl_service_t>(new rcl_service_t,
                                              [node](rcl_service_t* service)
                                              {
                                                  // Intentionally capture node by copy so shared_ptr can be
                                                  // transfered to copies
                                                  rcl_ret_t ret =
                                                      rcl_service_fini(service, static_cast<rcl_node_t*>(node->node()));
                                                  if (RCL_RET_OK != ret)
                                                  {
                                                      RCL_ERROR_MSG(Ros2ServiceImpl, rcl_service_fini);
                                                  }
                                                  delete service;
                                              });
    (*mService) = rcl_get_zero_initialized_service();
    rcl_service_options_t srv_ops = rcl_service_get_default_options();
    srv_ops.qos = Ros2QoSProfileConverter::convert(qos);
    // srv_ops.qos.depth = history_depth;

    // rcl_service_default_options srv_ops = {
    //     RMW_QOS_POLICY_HISTORY_KEEP_LAST,
    //     10,
    //     RMW_QOS_POLICY_RELIABILITY_RELIABLE,
    //     RMW_QOS_POLICY_DURABILITY_VOLATILE,
    //     RMW_QOS_DEADLINE_DEFAULT,
    //     RMW_QOS_LIFESPAN_DEFAULT,
    //     RMW_QOS_POLICY_LIVELINESS_SYSTEM_DEFAULT,
    //     RMW_QOS_LIVELINESS_LEASE_DURATION_DEFAULT,
    //     false
    // };

    rcl_ret_t rc = rcl_service_init(mService.get(), static_cast<rcl_node_t*>(mNode->node()),
                                    static_cast<const rosidl_service_type_support_t*>(type), service_name, &srv_ops);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2ServiceImpl, rcl_service_init);
        mService.reset();
        return;
    }
}
Ros2ServiceImpl::~Ros2ServiceImpl()
{
    if (wait_set_initialized)
    {
        rcl_ret_t rc = rcl_wait_set_fini(&wait_set);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(~Ros2ServiceImpl, rcl_wait_set_fini);
        }
        wait_set_initialized = false;
    }

    mService.reset();
    return;
}

bool Ros2ServiceImpl::getRequest(void* req_message)
{
    if (!wait_set_initialized)
    {
        wait_set = rcl_get_zero_initialized_wait_set();
        rcl_ret_t rc =
            rcl_wait_set_init(&wait_set, 0, 0, 0, 0, 1, 0, static_cast<rcl_context_t*>(mNode->handle()->context()),
                              rcl_get_default_allocator());

        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(getRequest, rcl_wait_set_init);
            return false;
        }
        wait_set_initialized = true;
    }
    else
    {
        rcl_ret_t rc = rcl_wait_set_clear(&wait_set);
        rc = rcl_wait_set_add_service(&wait_set, mService.get(), NULL);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(getRequest, rcl_wait_set_add_service);
            return false;
        }
        rc = rcl_wait(&wait_set, 0);
        // CARB_LOG_WARN_ONCE("Subscriber created, check topic name and message type if not active");
        if (rc != RCL_RET_OK && rc != RCL_RET_TIMEOUT)
        {
            RCL_WARN_MSG(getRequest, rcl_wait);
            return false;
        }
        if (wait_set.services[0])
        {
            rc = rcl_take_request(mService.get(), &request_id, req_message);
            if (rc != RCL_RET_OK)
            {
                RCL_ERROR_MSG(getRequest, rcl_take_request);
                return false;
            }
            return true;
        }
    }
    return false;
}

bool Ros2ServiceImpl::sendResponse(void* res_message)
{
    if (!wait_set_initialized)
        return false;
    rcl_ret_t rc = rcl_send_response(mService.get(), &request_id, res_message);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(sendResponse, rcl_send_response);
        return false;
    }
    return true;
}
