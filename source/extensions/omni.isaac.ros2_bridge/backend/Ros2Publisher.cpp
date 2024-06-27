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

Ros2PublisherImpl::Ros2PublisherImpl(Ros2NodeBase* node, const char* topic_name, const void* type, const Ros2QoSProfile& qos)
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
                                                    RCL_ERROR_MSG(Ros2PublisherImpl, rcl_publisher_fini);
                                                }
                                                delete pub;
                                            });
    // Init publisher
    (*mPub) = rcl_get_zero_initialized_publisher();
    rcl_publisher_options_t pub_opt = rcl_publisher_get_default_options();
    pub_opt.qos = Ros2QoSProfileConverter::convert(qos);
    rcl_ret_t rc = rcl_publisher_init(mPub.get(), static_cast<rcl_node_t*>(mNode->node()),
                                      static_cast<const rosidl_message_type_support_t*>(type), topic_name, &pub_opt);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2PublisherImpl, rcl_publisher_init);
        mPub.reset();
        return;
    }
}

Ros2PublisherImpl::~Ros2PublisherImpl()
{
    mPub.reset();
    return;
}

void Ros2PublisherImpl::publish(const void* msg)
{
    rcl_ret_t rc = rcl_publish(mPub.get(), msg, NULL);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(publish, rcl_publish);
    }
}

size_t Ros2PublisherImpl::get_subscription_count()
{
    size_t sub_count = 0;
    rcl_ret_t rc = rcl_publisher_get_subscription_count(mPub.get(), &sub_count);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(get_subscription_count, rcl_publisher_get_subscription_count);
    }
    return sub_count;
}
