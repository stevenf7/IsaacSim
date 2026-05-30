..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaacsim_sensors_rtx_custom:

=====================================
Creating Custom RTX Sensor Profiles
=====================================

.. note::

    This section is under development. Additional content will be added in a future update.

This page covers how to create custom RTX sensor configurations by setting attributes on ``OmniLidar`` and ``OmniRadar`` prims.

Getting Started
---------------

When creating custom RTX sensor profiles, it is recommended to start with an existing Lidar or Radar configuration shipped with |isaac-sim_short| as a reference:

- :ref:`RTX Lidar Asset Library <isaac_assets_nonvisual_sensors_rtx_lidar>` - Pre-configured Lidar sensors from various vendors
- :ref:`RTX Radar Sensor <isaacsim_sensors_rtx_radar>` - RTX Radar documentation and examples

You can load an existing configuration, inspect its USD attributes in the *Property* panel, and modify them to suit your needs.

Setting Lidar Attributes
------------------------

RTX Lidar sensors are configured via USD attributes on ``OmniLidar`` prims using the ``OmniSensorGenericLidarCoreAPI`` schema.

Key configuration areas include:

- **Output configuration**: Setting coordinate systems, motion compensation, and auxiliary data detail levels
- **Scanning principle**: Configuring rotary vs. solid-state scanning
- **Firing pattern**: Defining scan rate, emitter patterns, and number of returns
- **Field of view**: Constraining azimuth and elevation ranges
- **Intensity modeling**: Configuring beam properties, detector sensitivity, and atmospheric effects

For complete documentation on all Lidar attributes and their values, see `Setting Lidar Attributes <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.lidar/latest/lidar_extension.html#setting-lidar-attributes>`_ in the Omniverse Lidar Extension documentation.

Setting Radar Attributes
------------------------

RTX Radar sensors are configured via USD attributes on ``OmniRadar`` prims using the ``OmniSensorGenericRadarWpmDmatAPI`` schema.

For complete documentation on all Radar attributes and their values, see `Setting Radar Attributes <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.radar/latest/radar_extension.html#setting-radar-attributes>`_ in the Omniverse Radar Extension documentation.

Schema Reference
----------------

For the full USD schema definitions, refer to:

- `OmniSensorGenericLidarCoreAPI Schema <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreapi>`_
- `OmniSensorGenericLidarCoreEmitterStateAPI Schema <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreemitterstateapi>`_
- `OmniSensorGenericRadarWpmDmatAPI Schema <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericradarwpmdmatapi>`_

Validating Your Configuration
-----------------------------

After creating a custom sensor configuration, you can validate it by:

1. Adding the sensor to a scene using the methods described in :ref:`isaacsim_sensors_rtx_lidar` or :ref:`isaacsim_sensors_rtx_radar`.
2. Visualizing the sensor output using the :ref:`Debug Draw Extension <isaac_debug_draw>` or the techniques described in :ref:`isaacsim_sensors_rtx_lidar_visualization` and :ref:`isaacsim_sensors_rtx_radar_visualization`.
3. Collecting data using :ref:`RTX Sensor Annotators <rtx_sensor_annotator_descriptions>` to verify the output matches your expectations.

