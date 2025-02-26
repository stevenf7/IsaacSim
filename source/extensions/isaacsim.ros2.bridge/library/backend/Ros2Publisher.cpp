// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include "Ros2Impl.h"

#include <isaacsim/ros2/bridge/Ros2Macros.h>
#include <rcl/rcl.h>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

Ros2PublisherImpl::Ros2PublisherImpl(Ros2NodeHandle* nodeHandle,
                                     const char* topicName,
                                     const void* typeSupport,
                                     const Ros2QoSProfile& qos)
    : m_nodeHandle(nodeHandle)
{
    // Allocate memory for publisher
    m_publisher = std::shared_ptr<rcl_publisher_t>(new rcl_publisher_t,
                                                   [nodeHandle](rcl_publisher_t* pub)
                                                   {
                                                       rcl_ret_t ret = rcl_publisher_fini(
                                                           pub, static_cast<rcl_node_t*>(nodeHandle->getNode()));
                                                       if (RCL_RET_OK != ret)
                                                       {
                                                           RCL_ERROR_MSG(Ros2PublisherImpl, rcl_publisher_fini);
                                                       }
                                                       delete pub;
                                                   });
    // Init publisher
    (*m_publisher) = rcl_get_zero_initialized_publisher();
    rcl_publisher_options_t publisherOptions = rcl_publisher_get_default_options();
    publisherOptions.qos = Ros2QoSProfileConverter::convert(qos);
    rcl_ret_t rc = rcl_publisher_init(m_publisher.get(), static_cast<rcl_node_t*>(m_nodeHandle->getNode()),
                                      static_cast<const rosidl_message_type_support_t*>(typeSupport), topicName,
                                      &publisherOptions);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2PublisherImpl, rcl_publisher_init);
        m_publisher.reset();
        return;
    }
}

Ros2PublisherImpl::~Ros2PublisherImpl()
{
    m_publisher.reset();
    return;
}

void Ros2PublisherImpl::publish(const void* msg)
{
    rcl_ret_t rc = rcl_publish(m_publisher.get(), msg, NULL);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(publish, rcl_publish);
    }
}

size_t Ros2PublisherImpl::getSubscriptionCount()
{
    size_t subscriptionCount = 0;
    rcl_ret_t rc = rcl_publisher_get_subscription_count(m_publisher.get(), &subscriptionCount);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(getSubscriptionCount, rcl_publisher_get_subscription_count);
    }
    return subscriptionCount;
}

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
