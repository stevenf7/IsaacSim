// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Foxy.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>
Ros2PublisherFoxy::Ros2PublisherFoxy(Ros2NodeBase* node, const char* topic_name, const void* type, const size_t history_depth)
    : mNode(node)
{
    // Allocate memory for publisher
    mPub = std::shared_ptr<rcl_publisher_t>(new rcl_publisher_t,
                                            [node](rcl_publisher_t* pub)
                                            {
                                                rcl_ret_t ret =
                                                    rcl_publisher_fini(pub, static_cast<rcl_node_t*>(node->node()));
                                                if (RCL_RET_OK != ret)
                                                {
                                                    RCL_ERROR_MSG(Ros2PublisherFoxy, rcl_publisher_fini);
                                                }
                                                delete pub;
                                            });
    // Init publisher
    (*mPub) = rcl_get_zero_initialized_publisher();
    rcl_publisher_options_t pub_opt = rcl_publisher_get_default_options();
    pub_opt.qos.depth = history_depth;
    rcl_ret_t rc = rcl_publisher_init(mPub.get(), static_cast<rcl_node_t*>(mNode->node()),
                                      static_cast<const rosidl_message_type_support_t*>(type), topic_name, &pub_opt);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2PublisherFoxy, rcl_publisher_init);
        mPub.reset();
        return;
    }
}

Ros2PublisherFoxy::~Ros2PublisherFoxy()
{
    mPub.reset();
    return;
}

void Ros2PublisherFoxy::publish(const void* msg)
{
    rcl_ret_t rc = rcl_publish(mPub.get(), msg, NULL);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(publish, rcl_publish);
    }
}

size_t Ros2PublisherFoxy::get_subscription_count()
{
    size_t sub_count = 0;
    rcl_ret_t rc = rcl_publisher_get_subscription_count(mPub.get(), &sub_count);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(publish, rcl_publish);
    }
    return sub_count;
}