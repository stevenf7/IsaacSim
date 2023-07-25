// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

//! @file
//!
//! @brief Factory to instantiate lidar profile reader.

#include <carb/Interface.h>

#include <omni/sensors/lidar/ILidarProfileReader.h>


namespace omni
{
namespace sensors
{
namespace lidar
{

/**
 * @brief an interface for a lidar profile reader factory
 *
 */
class ILidarProfileReaderFactory
{
public:
    CARB_PLUGIN_INTERFACE("omni::sensors::lidar::ILidarProfileReaderFactory", 0, 1)

    /**
     * @brief
     * @return a model object pointer if successful, empty/nullptr otherwise
     *
     * @note the caller owns the model
     */
    virtual ILidarProfileReaderPtr createInstance() = 0;
};

} // namespace lidar
} // namespace sensors
} // namespace omni
