// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "IMUSensorTypes.h"


namespace omni
{
namespace isaac
{
namespace imu_sensor
{

struct IMUSensorInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::imu_sensor::struct IMUSensor", 0, 1);


    size_t(CARB_ABI* getNumSensorsOnBody)(const char* usdPath);

    IsHandle*(CARB_ABI* getSensorsOnBody)(const char* usdPath, size_t& num_sensors);

    //! Gets size of readings for sensor
    /*! Gets the size of readings for a sensor from last simulation step to current.
     * \param sensors sensor handle to probe
     * \return size of readings
     */
    size_t(CARB_ABI* getSensorReadingsSize)(const IsHandle sensor);

    //! Gets Sensor values
    /*! Gets the sensor values from last simulation step to current simualation step
     * \param sensors sensor handle to probe
     * \return time-stamped sensor values.
     */
    IsReading*(CARB_ABI* getSensorReadings)(const IsHandle sensor, size_t& num_readings);

    //! Gets Sensor latest simulation
    /*! Gets the sensor latest simulation reading
     * \param sensors sensor handle to probe
     * \return time-stamped sensor values.
     */
    IsReading(CARB_ABI* getSensorSimReading)(const IsHandle sensor);

    IsHandle(CARB_ABI* addSensorOnBody)(const char* usdPath, const IsProperties props);

    bool(CARB_ABI* removeSensor)(IsHandle sensor);
};
}
}
}
