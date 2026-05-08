
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.







.. _isaac_assets_camera_depth_sensors:

================================
Camera and Depth Sensors
================================

|isaac-sim_short| supports camera and depth sensors, with digital twins found in the Content Browser
 under ``Isaac Sim/Sensors``, organized into subfolders by manufacturer.

Cameras
=======

For more information about camera modeling in |isaac-sim_short|, see :ref:`here<isaacsim_sensors_camera>`.

Leopard Imaging
-------------------

.. _hawk_stereo_camera:

Hawk Stereo Camera
#############################

The Hawk Stereo Camera (`LI-AR0234CS-STEREO-GMSL2-30 <https://leopardimaging.com/product/platform-partners/qualcomm/iot-robotics-qualcomm/li-ar0234cs-stereo-gmsl2-qualcomm/li-ar0234cs-stereo-gmsl2-30/>`_) from Leopard Imaging consists of two OnSemi AR0234CS RGB image sensors and a 6-axis IMU, both are simulated in the |isaac-sim|.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_hawk_v1.1_nominal.png
    :align: center
    :alt: Hawk Sensor
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Leopard Imaging>Hawk*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>LeopardImaging>Hawk>hawk_v1.1_nominal.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/hawk_v1.1_nominal.csv
        :align: center
        :widths: 30 30 30
        :header-rows: 1


    **Other Features**

    - Waterproof: IP65
    - Dimensions: 180 mm (length) by 44.33 mm (depth) by 25.0 mm (height)
    - Operating Temperature: -20C to 50C

.. dropdown:: IMU to Hawk sensor (left camera) transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - 0.0
          - 90
          - 0.0
        * - Translation (meters)
          - 0.0
          - -0.0947
          - 0.0061

.. Note::
    For the datasheet and full list of specifications, visit the `Hawk stereo camera product page <https://leopardimaging.com/leopard-imaging-hawk-stereo-camera/>`_ and `purchase here <https://leopardimaging.com/product/platform-partners/qualcomm/iot-robotics-qualcomm/li-ar0234cs-stereo-gmsl2-qualcomm/li-ar0234cs-stereo-gmsl2-30/>`_.

.. _owl_fisheye_camera:

Owl Fisheye camera
#############################

The Owl camera (`LI-AR0234CS-GMSL2-OWL <https://leopardimaging.com/product/automotive-cameras/cameras-by-interface/maxim-gmsl-2-cameras/li-ar0234cs-gmsl2-owl/li-ar0234cs-gmsl2-owl/>`_) from Leopard Imaging consists of a 2.3MP OnSemi AR0234CS RGB image sensor, capable of producing crisp images in low-light and bright scenes.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_owl.png
    :align: center
    :alt: Owl Sensor
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Leopard Imaging>Owl*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>LeopardImaging>Owl>owl.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/owl.csv
        :align: center
        :widths: 30 70
        :header-rows: 1


    **Other Features**

    - Dimensions: 50 mm (length) by 37.63 mm (depth) by 25.0 mm (height)
    - Operating Temperature: -20C to 50C

.. Note::
    For full list of specifications, visit the `product page <https://leopardimaging.com/leopard-imaging-hawk-stereo-camera/>`_ ,and the owl cameras can be `purchased here <https://leopardimaging.com/product/automotive-cameras/cameras-by-interface/maxim-gmsl-2-cameras/li-ar0234cs-gmsl2-owl/li-ar0234cs-gmsl2-owl/>`_.

Sensing
---------

SG2-AR0233C-5200-G2A-H100F1A Camera (Certified by Sensing)
######################################################################

SG2-AR0233C-5200-G2A-H100F1A from the `SG2-AR0233C-5200-G2A-Hxxx Series <https://www.sensing-world.com/en/pd.jsp?id=18>`_ is a megapixel high performance automotive camera module, primarily used for ADAS, HDR imaging functionalities.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG2-AR0233C-5200-G2A-H100F1A.png
    :align: center
    :alt: H100F1A
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG2-AR0233C-5200-G2A-H100F1A*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG2>H100F1A>SG2-AR0233C-5200-G2A-H100F1A.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG2-AR0233C-5200-G2A-H100F1A.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Waterproof: IP67
    - Dimensions: 30 mm (length) by 22.5 mm (depth) by 30 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG2-AR0233C-5200-G2A-Hxxx series product page. <https://www.sensing-world.com/en/pd.jsp?id=18>`_


SG2-OX03CC-5200-GMSL2-H60YA Series Camera (Certified by Sensing)
######################################################################

SG2-OX03CC-5200-GMSL2-H60YA from the `SG2-OX03CC-5200-GMSL2-Hxxx Series <https://www.sensing-world.com/en/pd.jsp?id=106&id=106>`_ is a megapixel high performance automotive camera module, primarily used for ADAS, HDR imaging functionalities.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_Camera_SG2_OX03CC_5200_GMSL2_H60YA.png
    :align: center
    :alt: H60YA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG2-OX03CC-5200-GMSL2-H60YA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG2>H60YA>Camera_SG2_OX03CC_5200_GMSL2_H60YA.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/Camera_SG2_OX03CC_5200_GMSL2_H60YA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Waterproof: IP67
    - Dimensions: 30 mm (length) by 22.5 mm (depth) by 30 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG2-OX03CC-5200-GMSL2F-Hxxx series product page. <https://www.sensing-world.com/en/pd.jsp?id=106&id=106>`_


SG3-ISX031C-GMSL2F-H190XA (Certified by Sensing)
###################################################

`SG3-ISX031C-GMSL2F-H190XA <https://www.sensing-world.com/en/pd.jsp?id=23#_jcp=2>`_ is a 3 megapixels automotive camera for automotive surround view.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG3S-ISX031C-GMSL2F-H190XA.png
    :align: center
    :alt: H190XA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG3-ISX031C-GMSL2F-H190XA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG3>H190XA>SG3S-ISX031C-GMSL2F-H190XA.usd*


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG3S-ISX031C-GMSL2F-H190XA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Waterproof: IP67
    - Dimensions: 30 mm (length) by 22.5 mm (depth) by 30 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG3-ISX031C-GMSL2F-Hxxx series product page. <https://www.sensing-world.com/en/pd.jsp?id=23#_jcp=2>`_


SG5-IMX490C-5300-GMSL2-H110SA (Certified by Sensing)
######################################################

`SG5-IMX490C-5300-GMSL2-H110SA <https://www.sensing-world.com/en/pd.jsp?id=24#_jcp=2>`_ is a 5 megapixels automotive camera for automotive surround view, ADAS and viewing fusion.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG5-IMX490C-5300-GMSL2-H110SA.png
    :align: center
    :alt: H110SA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG5-IMX490C-5300-GMSL2-H110SA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG5>H100SA>SG5-IMX490C-5300-GMSL2-H110SA.usd*


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG5-IMX490C-5300-GMSL2-H110SA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Waterproof: IP67
    - Dimensions: 30 mm (length) by 22.5 mm (depth) by 30 mm (height)
    - Operating Temperature: -40C to 85C
    - Multi camera synchronization support

.. Note::
    For the datasheet and full list of specifications, visit the `SG5-IMX490C-5300-GMSL2-Hxxx series product page. <https://www.sensing-world.com/en/pd.jsp?id=24#_jcp=2>`_


SG8S-AR0820C-5300-G2A-H30YA Camera (Certified by Sensing)
############################################################

`SG8S-AR0820C-5300-G2A-H30YA <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_ is a 4k high performance automotive grade camera that supports advanced on sensor HDR and multi-camera synchronization.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG8S-AR0820C-5300-G2A-H30YA.png
    :align: center
    :alt: H30YA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG8S-AR0820C-5300-G2A-H30YA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG8>H30YA>SG8S-AR0820C-5300-G2A-H30YA.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG8S-AR0820C-5300-G2A-H30YA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Dimensions: 40 mm (length) by 23 mm (depth) by 40 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG8-AR820C-5300-G2A-Hxxx series cameras product page. <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_


SG8S-AR0820C-5300-G2A-H60SA Camera (Certified by Sensing)
############################################################

`SG8S-AR0820C-5300-G2A-H60SA <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_ is a 4k high performance automotive grade camera that supports advanced on sensor HDR and multi-camera synchronization.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG8S-AR0820C-5300-G2A-H60SA.png
    :align: center
    :alt: H60SA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG8S-AR0820C-5300-G2A-H60SA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG8>H60SA>SG8S-AR0820C-5300-G2A-H60SA.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG8S-AR0820C-5300-G2A-H60SA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Dimensions: 40 mm (length) by 23 mm (depth) by 40 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG8-AR820C-5300-G2A-Hxxx series cameras product page. <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_


SG8S-AR0820C-5300-G2A-H120YA Camera (Certified by Sensing)
############################################################

`SG8S-AR0820C-5300-G2A-H120YA <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_ is a 4k high performance automotive grade camera that supports advanced on sensor HDR and multi-camera synchronization.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_SG8S-AR0820C-5300-G2A-H120YA.png
    :align: center
    :alt: H120YA
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Sensing>Sensing SG8S-AR0820C-5300-G2A-H120YA*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Sensing>SG8>H120YA>SG8S-AR0820C-5300-G2A-H120YA.usd*


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/SG8S-AR0820C-5300-G2A-H120YA.csv
        :align: center
        :widths: 22 26
        :header-rows: 1


    **Other Features**

    - Dimensions: 40 mm (length) by 23 mm (depth) by 40 mm (height)
    - Operating Temperature: -40C to 85C

.. Note::
    For the datasheet and full list of specifications, visit the `SG8-AR820C-5300-G2A-Hxxx series cameras product page. <https://www.sensing-world.com/en/pd.jsp?id=26#_jcp=2>`_

SICK
----

Inspector83x (Certified by SICK)
################################

.. mdinclude:: SICK/Inspector83x/readme.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_Inspector83x.png
    :align: center
    :alt: SICK Inspector83x
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>SICK>Inspector83x*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>Inspector83x>SICK_Inspector83x.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: SICK/Inspector83x/features.md

InspectorP61x (Certified by SICK)
##################################

.. mdinclude:: SICK/InspectorP61x/readme.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_InspectorP61x.png
    :align: center
    :alt: SICK InspectorP61x
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>SICK>InspectorP61x*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>InspectorP61x>SICK_InspectorP61x.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: SICK/InspectorP61x/features.md

.. _isaac_assets_camera_depth_sensors_depth_sensors:

Depth Sensors
=============

For more information about depth sensor modeling in |isaac-sim_short|, see :ref:`here<isaacsim_sensors_camera_depth>`.

Realsense
---------

Realsense D455 (Certified by Realsense)
#######################################

.. mdinclude:: Realsense/D455/D455.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_rsd455.png
    :align: center
    :alt: Realsense D455
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>RealSense>Realsense D455*

.. dropdown:: Camera Attributes
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/realsense.csv
        :align: center
        :widths: 20 20 20 20 20
        :header-rows: 1

.. dropdown:: IMU to RealSense transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - 0.0
          - 0.0
          - 0.0
        * - Translation (meters)
          - 0.016
          - -0.01728
          - 0.0074

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Realsense>D455>rsd455.usd*

Realsense D457 (Certified by Realsense)
#######################################

.. mdinclude:: Realsense/D457/D457.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_rsd457.png
    :align: center
    :alt: Realsense D457
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>RealSense>Realsense D457*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Realsense>D457>rsd457.usd*

.. dropdown:: Camera Attributes
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/realsense.csv
        :align: center
        :widths: 20 20 20 20 20
        :header-rows: 1

.. dropdown:: IMU to RealSense transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - 0.0
          - 0.0
          - 0.0
        * - Translation (meters)
          - 0.016
          - -0.01728
          - 0.0074

Realsense D555 (Certified by Realsense)
#######################################

.. mdinclude:: Realsense/D555/D555.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_rsd555.png
    :align: center
    :alt: Realsense D555
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>RealSense>Realsense D555*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Realsense>D555>rsd555.usd*

.. dropdown:: Camera Attributes
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/realsense.csv
        :align: center
        :widths: 20 20 20 20 20
        :header-rows: 1

.. dropdown:: IMU to RealSense transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - 0.0
          - 0.0
          - 0.0
        * - Translation (meters)
          - 0.016
          - -0.01728
          - 0.0074

Orbbec
---------

Orbbec Gemini 2 (Certified by Orbbec)
########################################

The `Orbbec Gemini 2 <https://www.orbbec.com/products/stereo-vision-camera/gemini-2/>`_ is a depth camera based on Active Stereo IR technology.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_orbbec_gemini2_v1.0.png
    :align: center
    :alt: Orbbec Gemini 2
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Orbbec>Orbbec Gemini 2*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Orbbec>Gemini 2>orbbec_gemini2_V1.0.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/orbbec_gemini2_V1.0.csv
        :align: center
        :widths: 20 20 20 20 20
        :header-rows: 1


    **Other Features**

    - Dimensions: 90 mm (length) by 25 mm (depth) by 30 mm (height)
    - IMU supported with multi camera synchronization
    - Ideal Range: 0.15m to 10m
    - Depth accuracy: under 2% at 2m


.. Note::
    For the datasheet and full list of specifications, visit the `Gemini 2 product page. <https://www.orbbec.com/products/stereo-vision-camera/gemini-2>`_

Orbbec Femto Mega (Certified by Orbbec)
##########################################

The `Orbbec Femto Mega <https://www.orbbec.com/products/tof-camera/femto-mega/>`_ is a programmable multi-mode Depth and RGB camera.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_orbbec_femtomega_v1.0.png
    :align: center
    :alt: Orbbec Femto Mega
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Orbbec>Orbbec FemtoMega*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Orbbec>FemtoMega>orbbec_femtomega_v1.0.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/orbbec_femtomega_v1.0.csv
        :align: center
        :widths: 22 26 26 26
        :header-rows: 1


    **Other Features**

    - Dimensions: 115mm (length) by 145 mm (depth) by 40mm (height)
    - IMU supported
    - Ideal Range: 0.25m to 5.46m
    - Depth accuracy: under 11mm + 0.1% distance

.. Note::
    For the datasheet and full list of specifications, visit the `Femto Mega product page. <https://www.orbbec.com/products/tof-camera/femto-mega/>`_

Orbbec Gemini 335 (Certified by Orbbec)
##########################################

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_orbbec_gemini_335.png
    :align: center
    :alt: Orbbec Gemini 335
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Orbbec>Orbbec Gemini 335*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Orbbec>Gemini335>orbbec_gemini_335.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/orbbec_gemini_335.csv
        :align: center
        :widths: 22 26 26 26
        :header-rows: 1

Orbbec Gemini 335L (Certified by Orbbec)
##########################################

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_orbbec_gemini_335L.png
    :align: center
    :alt: Orbbec Gemini 335L
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Orbbec>Orbbec Gemini 335L*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Orbbec>Gemini335L>orbbec_gemini_335L.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/orbbec_gemini_335L.csv
        :align: center
        :widths: 22 26 26 26
        :header-rows: 1

Luxonis
-------

OAK4-D (Certified by Luxonis)
##############################

.. mdinclude:: Luxonis/OAK4-D/OAK4-D.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_OAK4-D.png
    :align: center
    :alt: Luxonis OAK4-D
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Luxonis>Luxonis OAK4-D*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Luxonis>OAK4-D>oak4_d.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: Luxonis/OAK4-D/features.md

OAK4-D Wide (Certified by Luxonis)
###################################

.. mdinclude:: Luxonis/OAK4-D_Wide/OAK4-D_Wide.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_OAK4-D_Wide.png
    :align: center
    :alt: Luxonis OAK4-D Wide
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Luxonis>Luxonis OAK4-D Wide*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Luxonis>OAK4-D_Wide>oak4_d_wide.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: Luxonis/OAK4-D_Wide/features.md

OAK-D Pro PoE (Certified by Luxonis)
#####################################

.. mdinclude:: Luxonis/OAK-D_Pro_PoE/OAK-D_Pro_PoE.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_OAK-D_Pro_PoE.png
    :align: center
    :alt: Luxonis OAK-D Pro PoE
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Luxonis>Luxonis OAK-D Pro PoE*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Luxonis>OAK-D_Pro_PoE>oak_d_pro_poe.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: Luxonis/OAK-D_Pro_PoE/features.md

OAK-D Pro W PoE (Certified by Luxonis)
#######################################

.. mdinclude:: Luxonis/OAK-D_Pro_W_PoE/OAK-D_Pro_W_PoE.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_OAK-D_Pro_W_PoE.png
    :align: center
    :alt: Luxonis OAK-D Pro W PoE
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Luxonis>Luxonis OAK-D Pro W PoE*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Luxonis>OAK-D_Pro_W_PoE>oak_d_pro_w_poe.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: Luxonis/OAK-D_Pro_W_PoE/features.md

OAK-D ToF (Certified by Luxonis)
#################################

.. mdinclude:: Luxonis/OAK-D_ToF/OAK-D_ToF.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_OAK-D_ToF.png
    :align: center
    :alt: Luxonis OAK-D ToF
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Luxonis>Luxonis OAK-D ToF*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Luxonis>OAK-D_ToF>oak_d_tof.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: Luxonis/OAK-D_ToF/features.md

SICK
----

safeVisionary2 (Certified by SICK)
###################################

.. mdinclude:: SICK/safeVisionary2/readme.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_safeVisionary2.png
    :align: center
    :alt: SICK safeVisionary2
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>SICK>safeVisionary2*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>safeVisionary2>SICK_safeVisionary2.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. mdinclude:: SICK/safeVisionary2/features.md

Visionary-T Mini (Certified by SICK)
#####################################

.. mdinclude:: SICK/Visionary-T_Mini/readme.md

.. figure:: /images/usd_assets_sensors/isim_6.0_full_ref_viewport_Isaac_Sensors_Visionary-T_Mini.png
    :align: center
    :alt: SICK Visionary-T Mini
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>SICK>Visionary-T Mini*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>Visionary-T_Mini>SICK_Visionary-T_Mini.usd*

Stereolabs
----------

ZED X (Certified by Stereolabs)
####################################

The `ZED X Stereo Camera <https://www.stereolabs.com/zed-x/>`_ from Stereolabs consists of two 1200p 60fps RGB image sensors and a 6-axis IMU, all simulated in the |isaac-sim|.

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_ZED_X.png
    :align: center
    :alt: Zed X Camera
    :width: 50%

    To create the camera from the menu: *Create>Sensors>Camera and Depth Sensors>Stereolabs>ZED_X*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Stereolabs>ZED_X>ZED_X.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/ZED_X.csv
        :align: center
        :widths: 30 35 35
        :header-rows: 1


    **Other Features**

    - Dimensions: 163.4 mm (length) by 31.8 mm (depth) by 36.7 mm (height)
    - Operating Temperature: -20C to 55C

.. dropdown:: IMU to ZED X transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - -90.0
          - 0.0
          - 0.0
        * - Translation (meters)
          - 0.06
          - -0.0
          - 0.00185

.. Note::
    For the datasheet and full list of specifications, visit the `ZED X datasheet <https://www.stereolabs.com/datasheets>`_, for usage in |isaac-sim_short|, see `Stereolabs Documentation <https://www.stereolabs.com/docs/isaac-sim>`_.

ZED X Mini (Certified by Stereolabs)
####################################

The `ZED X Mini Stereo Camera <https://www.stereolabs.com/zed-x/>`_ from Stereolabs consists of two 1200p 60fps RGB image sensors and a 6-axis IMU, all simulated in the |isaac-sim|.

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_ZED_X_Mini.png
    :align: center
    :alt: Zed X Mini Camera
    :width: 50%

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Stereolabs>ZED_X_mini>ZED_X_Mini.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: Camera Features
        :file: /csv/ZED_X_Mini.csv
        :align: center
        :widths: 30 35 35
        :header-rows: 1


    **Other Features**

    - Dimensions: 93.6 mm (length) by 31.8 mm (depth) by 36.7 mm (height)
    - Operating Temperature: -20C to 55C

.. dropdown:: IMU to ZED X Mini transformation in Isaac Sim
    :animate: fade-in
    :color: light

    .. list-table:: IMU Sensor transformation
        :align: center
        :widths: 40 20 20 20
        :header-rows: 1

        * - Transformation
          - x
          - y
          - z
        * - Rotation (degrees)
          - -90.0
          - 0.0
          - 0.0
        * - Translation (meters)
          - 0.06
          - -0.0
          - 0.00185

.. Note::
    For the datasheet and full list of specifications, visit the `ZED X Mini datasheet <https://www.stereolabs.com/datasheets>`_, for usage in |isaac-sim_short|, see `Stereolabs Documentation <https://www.stereolabs.com/docs/isaac-sim>`_.
