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

Ros2NodeHumble::Ros2NodeHumble(const char* name, const char* name_space, Ros2HandleBase* handle)
    : mHandle(handle), mNode(nullptr)
{
    rcl_ret_t rc;
    mNode = std::shared_ptr<rcl_node_t>(new rcl_node_t,
                                        [](rcl_node_t* node)
                                        {
                                            rcl_ret_t ret = rcl_node_fini(node);
                                            if (RCL_RET_OK != ret)
                                            {
                                                RCL_ERROR_MSG(Ros2NodeHumble, rcl_node_fini);
                                            }
                                            delete node;
                                        });
    if (mNode != NULL)
    {
        (*mNode) = rcl_get_zero_initialized_node();
        rcl_node_options_t node_ops = rcl_node_get_default_options();
        rc = rcl_node_init(mNode.get(), name, name_space, static_cast<rcl_context_t*>(mHandle->context()), &node_ops);
        if (rc != RCL_RET_OK)
        {
            mNode.reset();
            RCL_ERROR_MSG(Ros2NodeHumble, rcl_node_init);
            return;
        }
    }
}
Ros2NodeHumble::~Ros2NodeHumble()
{
    mNode.reset();
}
Ros2HandleBase* Ros2NodeHumble::handle()
{
    return mHandle;
}
void* Ros2NodeHumble::node()
{
    return mNode.get();
}
