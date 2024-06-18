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
#include "Ros2Humble.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>

Ros2SubscriberHumble::Ros2SubscriberHumble(Ros2NodeBase* node,
                                           const char* topic_name,
                                           const void* type,
                                           const Ros2QoSProfile& qos)
    : mNode(node), wait_set_initialized(false)
{
    mSub = std::shared_ptr<rcl_subscription_t>(new rcl_subscription_t,
                                               [node](rcl_subscription_t* subscription)
                                               {
                                                   // Intentionally capture node by copy so shared_ptr can be
                                                   // transfered to copies
                                                   rcl_ret_t ret = rcl_subscription_fini(
                                                       subscription, static_cast<rcl_node_t*>(node->node()));
                                                   if (RCL_RET_OK != ret)
                                                   {
                                                       RCL_ERROR_MSG(Ros2SubscriberHumble, rcl_subscription_fini);
                                                   }
                                                   delete subscription;
                                               });
    (*mSub) = rcl_get_zero_initialized_subscription();
    rcl_subscription_options_t sub_ops = rcl_subscription_get_default_options();
    sub_ops.qos = Ros2QoSProfileHumbleConverter::convert(qos);

    // rcl_subscription_default_options sub_ops = {
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

    rcl_ret_t rc = rcl_subscription_init(mSub.get(), static_cast<rcl_node_t*>(mNode->node()),
                                         static_cast<const rosidl_message_type_support_t*>(type), topic_name, &sub_ops);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2SubscriberHumble, rcl_subscription_init);
        mSub.reset();
        return;
    }
}
Ros2SubscriberHumble::~Ros2SubscriberHumble()
{
    if (wait_set_initialized)
    {
        rcl_ret_t rc = rcl_wait_set_fini(&wait_set);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(~Ros2SubscriberHumble, rcl_wait_set_fini);
        }
        wait_set_initialized = false;
    }

    mSub.reset();
    return;
}

bool Ros2SubscriberHumble::spin(void* ros_message)
{
    if (!wait_set_initialized)
    {
        wait_set = rcl_get_zero_initialized_wait_set();
        rcl_ret_t rc =
            rcl_wait_set_init(&wait_set, 1, 0, 0, 0, 0, 0, static_cast<rcl_context_t*>(mNode->handle()->context()),
                              rcl_get_default_allocator());

        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(spin, rcl_wait_set_init);
            return false;
        }
        wait_set_initialized = true;
    }
    else
    {
        // void* data;
        rmw_message_info_t messageInfo;

        rcl_ret_t rc = rcl_wait_set_clear(&wait_set);

        rc = rcl_wait_set_add_subscription(&wait_set, mSub.get(), NULL);
        if (rc != RCL_RET_OK)
        {
            RCL_ERROR_MSG(spin, rcl_wait_set_add_subscription);
            return false;
        }
        rc = rcl_wait(&wait_set, 0);
        CARB_LOG_WARN_ONCE("Subscriber created, check topic name and message type if not active");
        if (rc != RCL_RET_OK)
        {
            // This keeps printing an error if the publisher is not active.
            // Ideally only want to notify user once, when the subscription is created
            // RCL_WARN_MSG(spin, rcl_wait);
            return false;
        }
        if (wait_set.subscriptions[0])
        {
            rcl_ret_t ret = rcl_take(mSub.get(), ros_message, &messageInfo, NULL);
            if (ret != RCL_RET_OK)
            {
                RCL_ERROR_MSG(spin, rcl_take);
                return false;
            }
            // Successful rcl_take
            return true;
        }
    }
    return false;
}
