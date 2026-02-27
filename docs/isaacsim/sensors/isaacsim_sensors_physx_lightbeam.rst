..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physx_lightbeam:

========================
|physx| Lightbeam Sensor
========================

The |physx| Lightbeam sensor in |isaac-sim_short| uses |physx| raycasts to determine if an object has intersected a light beam.
You can specify the number of rays and height to create a safety light "curtain" of lightbeam sensors.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

.. _isaacsim_sensors_physx_lightbeam_example:

Examples
===================

- |physx| Lightbeam Sensor example: **Robotics Examples > Sensors > Lightbeam**

To run the example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples > Sensors > Lightbeam**.
#. Verify that you have a window containing empty data for each lightbeam, which will be populated with data after you press **play**. It will show if each beam was hit, the linear depth of the hit, and the exact hit position in ``xyz``.
#. Press the **PLAY** button to begin simulating.
#. Press :code:`SHIFT + LEFT_CLICK` to drag the cube or sensor around and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_viewport_lightbeam_sensor.gif
    :align: center
    :width: 100%

