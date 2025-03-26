// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#include "Tf2Impl.h"

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

/**
 * @brief Creates a new ROS 2 transform buffer instance.
 * @details
 * Factory method implementation that instantiates a concrete Ros2BufferCoreImpl object.
 *
 * @return Shared pointer to the newly created buffer instance.
 */
std::shared_ptr<Ros2BufferCore> Tf2FactoryImpl::createBuffer()
{
    return std::make_shared<Ros2BufferCoreImpl>();
}

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim

/**
 * @brief Creates a factory instance for TF2 components.
 * @details
 * Global factory function that creates and returns a new Tf2FactoryImpl instance.
 * This function is exported and can be dynamically loaded by the plugin system.
 *
 * @return Pointer to a newly created TF2 factory instance.
 */
isaacsim::ros2::tf_viewer::Tf2Factory* createFactory()
{
    return new isaacsim::ros2::tf_viewer::Tf2FactoryImpl();
}
