// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Ros2Humble.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>

void* Ros2HandleHumble::context()
{
    return mContext.get();
}

void Ros2HandleHumble::init(int argc, char const* const* argv, bool setDomainId, size_t domainId)
{
    rcl_ret_t rc;
    // Initialize RCL init options and copy them
    mInitOptions = rcl_get_zero_initialized_init_options();
    rc = rcl_init_options_init(&mInitOptions, rcl_get_default_allocator());
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2HandleBase, rcl_init_options_init);
        return;
    }
    if (setDomainId)
    {
        rcl_init_options_get_rmw_init_options(&mInitOptions)->domain_id = domainId;
    }

    mContext = std::shared_ptr<rcl_context_t>(new rcl_context_t,
                                              [this](rcl_context_t* context)
                                              {
                                                  if (NULL != context->impl)
                                                  {
                                                      rcl_ret_t ret;
                                                      if (this->is_valid())
                                                      {
                                                          // shutdown first, if still valid
                                                          ret = rcl_shutdown(context);
                                                          if (RCL_RET_OK != ret)
                                                          {
                                                              RCL_ERROR_MSG(Ros2HandleBase, rcl_shutdown);
                                                          }

                                                          ret = rcl_context_fini(context);
                                                          if (RCL_RET_OK != ret)
                                                          {
                                                              RCL_ERROR_MSG(Ros2HandleBase, rcl_context_fini);
                                                          }
                                                      }
                                                  }
                                                  delete context;
                                              });

    // Init RCL Context
    *mContext = rcl_get_zero_initialized_context();
    rc = rcl_init(argc, argv, &mInitOptions, mContext.get());
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(Ros2HandleBase, rcl_init);
        return;
    }
}
bool Ros2HandleHumble::is_valid()
{
    return rcl_context_is_valid(mContext.get());
}
bool Ros2HandleHumble::shutdown(const char* shutdown_reason)
{
    mContext.reset();
    // Finalize RCL options
    rcl_ret_t rc = rcl_init_options_fini(&mInitOptions);
    if (rc != RCL_RET_OK)
    {
        RCL_ERROR_MSG(~Ros2HandleBase, rcl_init_options_fini);
        return false;
    }
    return true;
}
