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

namespace omni
{
namespace isaac
{
namespace ros2_bridge
{

Ros2NodeHandleImpl::Ros2NodeHandleImpl(const char* name, const char* namespaceName, Ros2ContextHandle* contextHandle)
    : m_contextHandle(contextHandle), m_node(nullptr)
{
    rcl_ret_t rc;
    m_node = std::shared_ptr<rcl_node_t>(new rcl_node_t,
                                         [](rcl_node_t* node)
                                         {
                                             rcl_ret_t ret = rcl_node_fini(node);
                                             if (RCL_RET_OK != ret)
                                             {
                                                 RCL_ERROR_MSG(Ros2NodeHandleImpl, rcl_node_fini);
                                             }
                                             delete node;
                                         });
    if (m_node != NULL)
    {
        (*m_node) = rcl_get_zero_initialized_node();
        rcl_node_options_t nodeOptions = rcl_node_get_default_options();
        rc = rcl_node_init(m_node.get(), name, namespaceName,
                           static_cast<rcl_context_t*>(m_contextHandle->getContext()), &nodeOptions);
        if (rc != RCL_RET_OK)
        {
            m_node.reset();
            RCL_ERROR_MSG(Ros2NodeHandleImpl, rcl_node_init);
            return;
        }
    }
}

Ros2NodeHandleImpl::~Ros2NodeHandleImpl()
{
    m_node.reset();
}

Ros2ContextHandle* Ros2NodeHandleImpl::getContextHandle()
{
    return m_contextHandle;
}

void* Ros2NodeHandleImpl::getNode()
{
    return m_node.get();
}

} // namespace ros2_bridge
} // namespace isaac
} // namespace omni
