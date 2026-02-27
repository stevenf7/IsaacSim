..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



====================================================================================
RTX Sensors Placement and Calibration
====================================================================================


Optimizing camera placement is a crucial technique, particularly in indoor or enclosed spaces such as warehouses, retail stores, hospitals, and other similar environments, to ensure comprehensive coverage while minimizing camera deployment costs. 

Isaac Sim provides two separate extensions to help you optimize camera placement and extract calibration data:

- **Camera Placement** (``isaacsim.sensors.rtx.placement``): Automatically determines optimal camera locations based on scene layout and coverage requirements.

   .. toctree::
      :maxdepth: 1

      ext_sensors_rtx_placement/camera_placement.rst

- **Camera Calibration** (``isaacsim.sensors.rtx.calibration``): Extracts and manages camera calibration data, including position, orientation, and field of view information.
   
   .. toctree::
      :maxdepth: 1

      ext_sensors_rtx_placement/camera_calibration.rst

