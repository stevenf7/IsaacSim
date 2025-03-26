// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#pragma once

#include <isaacsim/ros2/tf_viewer/Tf2Factory.h>

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

/**
 * @class Tf2FactoryImpl
 * @brief Factory implementation for creating TF2 components.
 * @details
 * Provides factory methods for creating ROS 2 transform buffer instances
 * and other TF2-related components.
 */
class Tf2FactoryImpl : public Tf2Factory
{
public:
    /**
     * @brief Creates a new ROS 2 transform buffer instance.
     * @return Shared pointer to the created buffer instance.
     */
    virtual std::shared_ptr<Ros2BufferCore> createBuffer();
};

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim

#ifdef _MSC_VER
/**
 * @brief Factory creation function for Windows platform.
 * @return Pointer to a new TF2 factory instance.
 */
extern "C" __declspec(dllexport) isaacsim::ros2::tf_viewer::Tf2Factory* createFactory();
#else
/**
 * @brief Factory creation function for non-Windows platforms.
 * @return Pointer to a new TF2 factory instance.
 */
extern "C" isaacsim::ros2::tf_viewer::Tf2Factory* createFactory();
#endif
