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

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

void* Ros2ContextHandleImpl::getContext()
{
    return m_context.get();
}

void Ros2ContextHandleImpl::init(int argc, char const* const* argv, bool setDomainId, size_t domainId)
{
    rcl_ret_t rc;
    // Initialize RCL init options and copy them
    m_initOptions = rcl_get_zero_initialized_init_options();
    rc = rcl_init_options_init(&m_initOptions, rcl_get_default_allocator());
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2ContextHandle, rcl_init_options_init);
        return;
    }
    if (setDomainId)
    {
        rcl_init_options_get_rmw_init_options(&m_initOptions)->domain_id = domainId;
    }

    m_context = std::shared_ptr<rcl_context_t>(new rcl_context_t,
                                               [this](rcl_context_t* context)
                                               {
                                                   if (NULL != context->impl)
                                                   {
                                                       rcl_ret_t ret;
                                                       if (this->isValid())
                                                       {
                                                           // shutdown first, if still valid
                                                           ret = rcl_shutdown(context);
                                                           if (RCL_RET_OK != ret)
                                                           {
                                                               RCL_ERROR_MSG(Ros2ContextHandle, rcl_shutdown);
                                                           }

                                                           ret = rcl_context_fini(context);
                                                           if (RCL_RET_OK != ret)
                                                           {
                                                               RCL_ERROR_MSG(Ros2ContextHandle, rcl_context_fini);
                                                           }
                                                       }
                                                   }
                                                   delete context;
                                               });

    // Init RCL Context
    *m_context = rcl_get_zero_initialized_context();
    rc = rcl_init(argc, argv, &m_initOptions, m_context.get());
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2ContextHandle, rcl_init);
        return;
    }
}

bool Ros2ContextHandleImpl::isValid()
{
    if (m_context.get())
    {
        return rcl_context_is_valid(m_context.get());
    }
    return false;
}

bool Ros2ContextHandleImpl::shutdown(const char* shutdownReason)
{
    // If the context is not valid, no need to do cleanup
    if (!m_context)
    {
        return true;
    }
    m_context.reset();
    // Finalize RCL options
    rcl_ret_t rc = rcl_init_options_fini(&m_initOptions);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(~Ros2ContextHandle, rcl_init_options_fini);
        return false;
    }
    return true;
}

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
