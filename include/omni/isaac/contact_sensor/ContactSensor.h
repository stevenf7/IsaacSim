// Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "ContactSensorTypes.h"


namespace omni
{
namespace isaac
{
namespace contact_sensor
{

struct ContactSensorInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::contact_sensor::struct ContactSensor", 0, 1);


    size_t(CARB_ABI* getNumSensorsOnBody)(const char* usdPath);

    CsHandle*(CARB_ABI* getSensorsOnBody)(const char* usdPath, size_t& num_sensors);


    //! Gets contact raw data from physics engine
    //*! Gets Contact raw data, for validation purposes and ground truth
    CsRawData*(CARB_ABI* getBodyCsRawData)(const char* usdPath, size_t& numContacts);

    //! Gets size of readings for sensor
    /*! Gets the size of readings for a sensor from last simulation step to current.
     * \param sensors sensor handle to probe
     * \return size of readings
     */
    size_t(CARB_ABI* getSensorReadingsSize)(const CsHandle sensor);

    //! Gets Sensor values
    /*! Gets the sensor values from last simulation step to current simualation step
     * \param sensors sensor handle to probe
     * \return time-stamped sensor values.
     */
    CsReading*(CARB_ABI* getSensorReadings)(const CsHandle sensor, size_t& num_readings);

    //! Gets Sensor latest simulation
    /*! Gets the sensor latest simulation reading
     * \param sensors sensor handle to probe
     * \return time-stamped sensor values.
     */
    CsReading(CARB_ABI* getSensorSimReading)(const CsHandle sensor);

    CsHandle(CARB_ABI* addSensorOnBody)(const char* usdPath, const CsProperties props);

    bool(CARB_ABI* removeSensor)(CsHandle sensor);
};
}
}
}
