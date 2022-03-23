// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
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


    //! Gets contact raw data from physics engine
    /*! Gets Contact raw data, for validation purposes and ground truth
     * \param primPath path of the sensor prim
     * \param numContacts size of contacts
     * \return Raw Data
     */
    CsRawData*(CARB_ABI* getSensorRawData)(const char* primPath, size_t& numContacts);

    //! Gets size of readings for sensor
    /*! Gets the size of readings for a sensor from last simulation step to current.
     * \param primPath path of the sensor prim
     * \return size of readings
     */
    size_t(CARB_ABI* getSensorReadingsSize)(const char* primPath);

    //! Gets Sensor values
    /*! Gets the sensor values from last simulation step to current simualation step
     * \param primPath path of the sensor prim
     * \param num_readings size of reading
     * \return time-stamped sensor values.
     */
    CsReading*(CARB_ABI* getSensorReadings)(const char* primPath, size_t& num_readings);

    //! Gets Sensor latest simulation
    /*! Gets the sensor latest simulation reading
     * \param primPath path of the sensor prim
     * \return time-stamped sensor values.
     */
    CsReading(CARB_ABI* getSensorSimReading)(const char* primPath);

    //! Gets Sensor latest simulation
    /*! Check is the prim path contact sensor
     * \param primPath path of the sensor prim
     * \return boolean for is contact sensor
     */
    bool(CARB_ABI* isContactSensor)(const char* primPath);

    //! Gets contact raw data of a rigid body with contact report API from physics engine
    /*! Gets Contact raw data, for validation purposes and ground truth
     * \param primPath path of the rigid body prim
     * \param numContacts size of contacts
     * \return Raw Data
     */
    CsRawData*(CARB_ABI* getBodyRawData)(const char* primPath, size_t& numContacts);
};
}
}
}
