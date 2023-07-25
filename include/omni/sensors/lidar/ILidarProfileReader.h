// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

//! @file
//!
//! @brief LidarProfileReader: This class reads the different lidar profiles (json) for the generic lidar simulation
//! plugin


#pragma once

#include "LidarProfileTypes.h"

#include <carb/IObject.h>

#include <memory>
#include <string>

namespace omni
{
namespace sensors
{
namespace lidar
{

/**
 * LidarProfileReader, reads the json sensor profile
 */
class ILidarProfileReader : public carb::IObject
{
public:
    virtual ~ILidarProfileReader(){};

    /**
     * init document
     * @param json [in] json file name with path
     */
    virtual void init(const char* json) = 0;

    /**
     * returns if the document is valid
     */
    virtual bool isValid() const = 0;

    /**
     * returns the name of the lidar sensor
     */
    virtual const char* name() const = 0;

    /**
     * returns the driveworksId of the lidar sensor
     */
    virtual uint32_t driveWorksId() const = 0;

    /**
     * updates the given lidar profile object and returns if it was successful
     * @param profile pointer pointing to profile data blob
     */
    virtual bool update(void* profile) = 0;

    /**
     * returns the scan type of the lidar sensor
     */
    virtual LidarScanType lidarScanType() const = 0;
};

/**
 * @brief a carb object pointer for an object that implements the ILidarProfileReader interface
 *
 */
using ILidarProfileReaderPtr = carb::ObjectPtr<ILidarProfileReader>;

} // namespace lidar
} // namespace sensors
} // namespace omni
