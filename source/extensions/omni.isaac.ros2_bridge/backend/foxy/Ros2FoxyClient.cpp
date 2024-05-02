// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Foxy.h"

#include <include/Ros2Macros.h>
#include <rcl/client.h>
#include <rcl/rcl.h>

Ros2ClientFoxy::Ros2ClientFoxy(Ros2NodeBase* node, const char* service_name, const void* type, const Ros2QoSProfile& qos)
    : mNode(node), wait_set_initialized(false)
{
    mClient = std::shared_ptr<rcl_client_t>(new rcl_client_t,
                                            [node](rcl_client_t* client)
                                            {
                                                // Intentionally capture node by copy so shared_ptr can be
                                                // transfered to copies
                                                rcl_ret_t ret =
                                                    rcl_client_fini(client, static_cast<rcl_node_t*>(node->node()));
                                                if (RCL_RET_OK != ret)
                                                {
                                                    RCL_ERROR_MSG(Ros2ClientFoxy, rcl_client_fini);
                                                }
                                                delete client;
                                            });
    (*mClient) = rcl_get_zero_initialized_client();
    rcl_client_options_t srv_ops = rcl_client_get_default_options();
    srv_ops.qos = Ros2QoSProfileFoxyConverter::convert(qos);
    rcl_ret_t rc = rcl_client_init(mClient.get(), static_cast<rcl_node_t*>(mNode->node()),
                                   static_cast<const rosidl_service_type_support_t*>(type), service_name, &srv_ops);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2ClientFoxy, rcl_client_init);
        mClient.reset();
        return;
    }
}
Ros2ClientFoxy::~Ros2ClientFoxy()
{
    if (wait_set_initialized)
    {
        rcl_ret_t rc = rcl_wait_set_fini(&wait_set);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(~Ros2ClientFoxy, rcl_wait_set_fini);
        }
        wait_set_initialized = false;
    }

    mClient.reset();
    return;
}

bool Ros2ClientFoxy::sendRequest(void* req_message)
{
    if (!wait_set_initialized)
    {
        wait_set = rcl_get_zero_initialized_wait_set();
        rcl_ret_t rc =
            rcl_wait_set_init(&wait_set, 0, 0, 0, 1, 0, 0, static_cast<rcl_context_t*>(mNode->handle()->context()),
                              rcl_get_default_allocator());

        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(sendRequest, rcl_wait_set_init);
            return false;
        }
        wait_set_initialized = true;
    }
    // sleep(1);//needed for DDS matching?

    int64_t sequence_number;
    rcl_ret_t rc = rcl_send_request(mClient.get(), req_message, &sequence_number);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(sendRequest, rcl_send_request);
        return false;
    }
    return true;
}

bool Ros2ClientFoxy::getResponse(void* res_message)
{
    while (true)
    {
        rcl_ret_t rc = rcl_wait_set_clear(&wait_set);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(sendRequest, rcl_wait_set_clear);
            return false;
        }
        rc = rcl_wait_set_add_client(&wait_set, mClient.get(), NULL);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(respond, rcl_wait_set_add_subscription);
            return false;
        }
        rc = rcl_wait(&wait_set, 0);
        // CARB_LOG_WARN_ONCE("Client created, check topic name and message type if not active");
        if (rc == RCL_RET_TIMEOUT)
        {
            return false;
        }
        if (rc != RCL_RET_OK)
        {
            // This keeps printing an error if the publisher is not active.
            // Ideally only want to notify user once, when the subscription is created
            RCL_WARN_MSG(getResponse, rcl_wait);
            return false;
        }
        for (size_t i = 0; i < wait_set.size_of_clients; i++)
        {
            if (wait_set.clients[0])
            {
                rmw_request_id_t rmw_request_id;
                rcl_ret_t ret_res = rcl_take_response(mClient.get(), &rmw_request_id, res_message);
                if (ret_res == RCL_RET_OK)
                {
                    return true;
                }
            }
        }
    }


    return false;
}
