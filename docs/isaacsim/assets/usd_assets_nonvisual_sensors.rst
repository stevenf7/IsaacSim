
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.







.. _isaac_assets_nonvisual_sensors:

================================
Non-Visual Sensors
================================

|isaac-sim_short| models many types of non-visual sensors models, with digital twins found in the Content Browser under ``Isaac Sim/Sensors``, organized into subfolders by manufacturer.

Some non-visual sensor types do not have digital twins. For more information about these sensors,
including how to create them from the GUI, follow the links below:

- :ref:`Contact sensors<isaacsim_sensors_physics_contact>`
- :ref:`IMU sensors<isaacsim_sensors_physics_imu>`
- :ref:`Lightbeam sensors<isaacsim_sensors_physx_lightbeam>`
- :ref:`PhysX Lidars<isaacsim_sensors_physx_lidar>`
- :ref:`RTX Radars<isaacsim_sensors_rtx_radar>`

.. _isaac_assets_nonvisual_sensors_rtx_lidar:

RTX Lidars
==========

RTX Lidars marked as "certified" have Lidar configurations verified by the sensor manufacturer and tested before release.

Some Lidar models feature multiple configurations or profiles, which are implemented as `USD Variants <https://docs.omniverse.nvidia.com/workflows/latest/variant-workflows.html>`_.
In those cases, the available variants and their characteristics will also be provided as tables in the appropriate section below.

NVIDIA
-------

There are several example Lidar configuration files that ship with |isaac-sim_short|. Note none of these Lidars have a mesh,
so only a prim will appear in the Stage window when they are created. To create them via the UI, select the appropriate
option below from the menu: *Create>Sensors>RTX Lidar>NVIDIA*.

.. * **Debug Rotary** - a single emitter rotary Lidar configuration, used to debug simple rotary Lidar issues.

* **Example Rotary 2D** - a 10Hz rotary Lidar configuration with emitters in a single plane.
* **Example Rotary** - a 10Hz rotary Lidar configuration with emitters in a single plane.
* **Example Rotary Beams** - a 10Hz rotary Lidar configuration using a Gaussian beam ray type.
* **Example Solid State** - a solid state Lidar configuration.
* **Example Solid State Beams** - a solid state Lidar configuration using a Gaussian beam ray type.
* **Simple Example Solid State** - a simple 12-emitter solid state Lidar configuration, used to debug solid state Lidar issues.

HESAI
-------

XT32 SD10
#########

`HESAI XT32 SD10 <https://www.hesaitech.com/product/xt32/>`_ is a high precision, 32 Channels 360 degrees spinning mid range Lidar.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_XT-32.png
    :align: center
    :alt: XT32
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>HESAI>XT32 SD10*


To create the sensor from the Content Browser: *Isaac Sim>Sensors>HESAI>XT32_SD10>HESAI_XT32_SD10.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: XT32 SD10 Features
        :file: /csv/Hesai_XT32_SD10.csv
        :align: center
        :widths: 22 40
        :header-rows: 1

    **Other Features**

    - Dimensions: 100 mm (Top Diameter) by 103 mm (Bottom Diameter) by 76.0 mm (Height)

.. Note::
    For the datasheet and full list of specifications, visit the `XT32 SD10 product page. <https://www.hesaitech.com/product/xt32/>`_

Ouster
-------

OS0
###

`Ouster OS0 <https://ouster.com/products/hardware/os0-lidar-sensor>`_ is a high precision Lidar for autonomous vehicles, heavy machinery, robot, and mapping solutions. |isaac-sim_short| has several pre-configured frequencies and resolutions that can be added to the stage easily.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_os0_mesh.png
    :align: center
    :alt: Ouster OS0
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>Ouster>OS0*, then select the desired sensor configuration.

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Ouster>OS0>OS0.usd*


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. tab-set::
        .. tab-item:: OS0 Rev6 Features
            :sync: os0

            .. tab-set::
                .. tab-item:: 10 Hz
                    :sync: os0_rev6_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os0_rev6_10_hz_512_res

                            .. csv-table:: Variant: OS0_REV6_128ch10hz512res
                                :file: /csv/OS0_REV6_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os0_rev6_10_hz_1024_res

                            .. csv-table:: Variant: OS0_REV6_128ch10hz1024res
                                :file: /csv/OS0_REV6_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os0_rev6_10_hz_2048_res

                            .. csv-table:: Variant: OS0_REV6_128ch10hz2048res
                                :file: /csv/OS0_REV6_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 20 Hz
                    :sync: os0_rev6_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os0_rev6_20_hz_512_res

                            .. csv-table:: Variant: OS0_REV6_128ch20hz512res
                                :file: /csv/OS0_REV6_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os0_rev6_20_hz_1024_res

                            .. csv-table:: Variant: OS0_REV6_128ch20hz1024res
                                :file: /csv/OS0_REV6_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
        .. tab-item:: OS0 Rev7 Features
            :sync: os0

            .. tab-set::
                .. tab-item:: 10 Hz
                    :sync: os0_rev7_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os0_rev7_10_hz_512_res

                            .. csv-table:: Variant: OS0_REV7_128ch10hz512res
                                :file: /csv/OS0_REV7_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os0_rev7_10_hz_1048_res

                            .. csv-table:: Variant: OS0_REV7_128ch10hz1024res
                                :file: /csv/OS0_REV7_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os0_rev7_10_hz_2048_res

                            .. csv-table:: Variant: OS0_REV7_128ch10hz2048res
                                :file: /csv/OS0_REV7_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 20 Hz
                    :sync: os0_rev7_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os0_rev7_20_hz_512_res

                            .. csv-table:: Variant: OS0_REV7_128ch20hz512res
                                :file: /csv/OS0_REV7_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os0_rev7_20_hz_1024_res

                            .. csv-table:: Variant: OS0_REV7_128ch20hz1024res
                                :file: /csv/OS0_REV7_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1

    **Other Features**

    - Rotation Rate: 10 or 20 hz (configurable)
    - Dimensions: 87 mm (Diameter) by 58.35 mm (Height). With thermal cap, height is 74.2 mm.
    - IMU supported: `InvenSense IAM-20680HT <https://invensense.tdk.com/download-pdf/iam-20680ht-datasheet/>`_


.. Note::
    For the datasheet and full list of specifications, visit the `OS0 product page. <https://ouster.com/products/hardware/os0-lidar-sensor>`_


OS1
###

`Ouster OS1 <https://ouster.com/products/hardware/os1-lidar-sensor>`_ is a high precision Lidar for autonomous vehicles, heavy machinery, robot, and mapping solutions.
|isaac-sim_short| has several pre-configured frequencies and resolutions that can be easily added to the stage.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_os1_mesh.png
    :align: center
    :alt: Ouster OS1
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>Ouster>OS1*.

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Ouster>OS1>OS1.usd*


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. tab-set::
        .. tab-item:: OS1 Rev6 Features
            :sync: os1

            .. tab-set::
                .. tab-item:: 32 Channels 10 Hz
                    :sync: os1_rev6_32_ch

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev6_32_ch_10_hz_512_res

                            .. csv-table:: Variant: OS1_REV6_32ch10hz512res
                                :file: /csv/OS1_REV6_32ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev6_32_ch_10_hz_1024_res

                            .. csv-table:: Variant: OS1_REV6_32ch10hz1024res
                                :file: /csv/OS1_REV6_32ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os1_rev6_32_ch_10_hz_2048_res

                            .. csv-table:: Variant: OS1_REV6_32ch10hz2048res
                                :file: /csv/OS1_REV6_32ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 32 Channels 20 Hz
                    :sync: os1_rev6_32_ch_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev6_32_ch_20_hz_512_res

                            .. csv-table:: Variant: OS1_REV6_32ch20hz512res
                                :file: /csv/OS1_REV6_32ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev6_32_ch_20_hz_1024_res

                            .. csv-table:: Variant: OS1_REV6_32ch20hz1024res
                                :file: /csv/OS1_REV6_32ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 128 Channels 10 Hz
                    :sync: os1_rev6_128_ch_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev6_128_ch_10_hz_512_res

                            .. csv-table:: Variant: OS1_REV6_128ch10hz512res
                                :file: /csv/OS1_REV6_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev6_128_ch_10_hz_1024_res

                            .. csv-table:: Variant: OS1_REV6_128ch10hz1024res
                                :file: /csv/OS1_REV6_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os1_rev6_128_ch_10_hz_2048_res

                            .. csv-table:: Variant: OS1_REV6_128ch10hz2048res
                                :file: /csv/OS1_REV6_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 128 Channels 20 Hz
                    :sync: os1_rev6_128_ch_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev6_128_ch_20_hz_512_res

                            .. csv-table:: Variant: OS1_REV6_128ch20hz512res
                                :file: /csv/OS1_REV6_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev6_128_ch_20_hz_1024_res

                            .. csv-table:: Variant: OS1_REV6_128ch20hz1024res
                                :file: /csv/OS1_REV6_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
        .. tab-item:: OS1 Rev7 Features
            :sync: os1

            .. tab-set::
                .. tab-item:: 10 Hz
                    :sync: os1_rev7_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev7_10_hz_512_res

                            .. csv-table:: Variant: OS1_REV7_128ch10hz512res
                                :file: /csv/OS1_REV7_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev7_10_hz_1048_res

                            .. csv-table:: Variant: OS1_REV7_128ch10hz1024res
                                :file: /csv/OS1_REV7_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os1_rev7_10_hz_2048_res

                            .. csv-table:: Variant: OS1_REV7_128ch10hz2048res
                                :file: /csv/OS1_REV7_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 20 Hz
                    :sync: os1_rev7_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os1_rev7_20_hz_512_res

                            .. csv-table:: Variant: OS1_REV7_128ch20hz512res
                                :file: /csv/OS1_REV7_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os1_rev7_20_hz_1024_res

                            .. csv-table:: Variant: OS1_REV7_128ch20hz1024res
                                :file: /csv/OS1_REV7_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1

    **Other Features**

    - Dimensions: 87 mm (Diameter) by 58.35 mm (Height). With thermal cap, height is 74.2 mm.
    - IMU supported: `InvenSense IAM-20680HT <https://invensense.tdk.com/download-pdf/iam-20680ht-datasheet/>`_


.. Note::
    For the datasheet and full list of specifications, visit the `OS1 product page. <https://ouster.com/products/hardware/os1-lidar-sensor>`_


OS2
###

`Ouster OS2 <https://ouster.com/products/hardware/os2-lidar-sensor>`_ is a high precision Lidar for autonomous vehicles, heavy machinery, robot, and mapping solutions.
|isaac-sim_short| has several pre-configured frequencies and resolutions that can be easily added to the stage.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_os2_mesh.png
    :align: center
    :alt: Ouster OS2
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>Ouster>OS2*.

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Ouster>OS2>OS2.usd*



.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. tab-set::
        .. tab-item:: OS2 Rev6 Features
            :sync: os2

            .. tab-set::
                .. tab-item:: 10 Hz
                    :sync: os2_rev6_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os2_rev6_10_hz_512_res

                            .. csv-table:: Variant: OS2_REV6_128ch10hz512res
                                :file: /csv/OS2_REV6_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os2_rev6_10_hz_1024_res

                            .. csv-table:: Variant: OS2_REV6_128ch10hz1024res
                                :file: /csv/OS2_REV6_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os2_rev6_10_hz_2048_res

                            .. csv-table:: Variant: OS2_REV6_128ch10hz2048res
                                :file: /csv/OS2_REV6_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 20 Hz
                    :sync: os2_rev6_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os2_rev6_20_hz_512_res

                            .. csv-table:: Variant: OS2_REV6_128ch20hz512res
                                :file: /csv/OS2_REV6_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os2_rev6_20_hz_1024_res

                            .. csv-table:: Variant: OS2_REV6_128ch20hz1024res
                                :file: /csv/OS2_REV6_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
        .. tab-item:: OS2 Rev7 Features
            :sync: os2

            .. tab-set::
                .. tab-item:: 10 Hz
                    :sync: os2_rev7_10_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os2_rev7_10_hz_512_res

                            .. csv-table:: Variant: OS2_REV7_128ch10hz512res
                                :file: /csv/OS2_REV7_128ch10hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os2_rev7_10_hz_1048_res

                            .. csv-table:: Variant: OS2_REV7_128ch10hz1024res
                                :file: /csv/OS2_REV7_128ch10hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 2048 Resolution
                            :sync: os2_rev7_10_hz_2048_res

                            .. csv-table:: Variant: OS2_REV7_128ch10hz2048res
                                :file: /csv/OS2_REV7_128ch10hz2048res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                .. tab-item:: 20 Hz
                    :sync: os2_rev7_20_hz

                    .. tab-set::
                        .. tab-item:: 512 Resolution
                            :sync: os2_rev7_20_hz_512_res

                            .. csv-table:: Variant: OS2_REV7_128ch20hz512res
                                :file: /csv/OS2_REV7_128ch20hz512res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1
                        .. tab-item:: 1024 Resolution
                            :sync: os2_rev7_20_hz_1024_res

                            .. csv-table:: Variant: OS2_REV7_128ch20hz1024res
                                :file: /csv/OS2_REV7_128ch20hz1024res.csv
                                :align: center
                                :widths: 22 40
                                :header-rows: 1

    **Other Features**

    - Dimensions: 87 mm (Diameter) by 58.35 mm (Height). With thermal cap, height is 74.2 mm.
    - IMU supported: `InvenSense IAM-20680HT <https://invensense.tdk.com/download-pdf/iam-20680ht-datasheet/>`_


.. Note::
    For the datasheet and full list of specifications, visit the `OS2 product page. <https://ouster.com/products/hardware/os2-lidar-sensor>`_

VLS 128
#######

`Ouster VLS 128 <https://ouster.com/products/hardware/vls-128>`_ is a long range, ultra high resolution 3D Lidar for autonomous vehicles.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_vls_128.png
    :align: center
    :alt: Ouster VLS 128
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>Ouster>VLS 128*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Ouster>VLS_128>Ouster_VLS_128.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: VLS 128 Features
        :file: /csv/Velodyne_VLS128.csv
        :align: center
        :widths: 22 40
        :header-rows: 1


    **Other Features**

    - Dimensions: 165.5 mm (Diameter) by 141.3 mm (Height)
    - Operating Temperature: -20C to 60C

.. Note::
     `VLS 128 product page. <https://ouster.com/products/hardware/vls-128>`_

SICK
----

.. mdinclude:: SICK/LRS4581R/readme.md

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_LRS4581R.png
    :align: center
    :alt: SICK LRS4581R
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>LRS4581R*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>LRS4581R>SICK_LRS4581R.usd*

.. mdinclude:: SICK/microScan3/readme.md

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_microScan3.png
    :align: center
    :alt: SICK microScan 3
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>microScan3*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>microScan3>SICK_microScan3.usd*

.. mdinclude:: SICK/MRS1104C/readme.md

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_MRS1104C.png
    :align: center
    :alt: SICK MRS1104C
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>MRS1104C*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>MRS1104C>SICK_MRS1104C.usd*

.. mdinclude:: SICK/multiScan136/readme.md

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_multiScan136.png
    :align: center
    :alt: SICK multiScan136
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>multiScan136*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>multiScan136>SICK_multiScan136.usd*

.. mdinclude:: SICK/multiScan165/readme.md

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_multiScan165.png
    :align: center
    :alt: SICK multiScan165
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>multiScan165*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>multiScan165>SICK_multiScan165.usd*

.. mdinclude:: SICK/nanoScan3/readme.md

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_nanoScan3.png
    :align: center
    :alt: SICK nanoScan3
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>nanoScan3*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>nanoScan3>SICK_nanoScan3.usd*

.. mdinclude:: SICK/picoScan150/readme.md

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_picoScan150.png
    :align: center
    :alt: SICK picoScan150
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>picoScan150*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>picoScan150>SICK_picoScan150.usd*

.. mdinclude:: SICK/TIM781/readme.md

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_tim781.png
    :align: center
    :alt: SICK TiM781 3
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>SICK>TiM781*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>SICK>tim781.usd*

SLAMTEC
----------

RPLIDAR S2E
################

`SLAMTEC RPLIDAR S2E <https://download-en.slamtec.com/api/download/rplidar-s2m1-RxE-datasheet/1.8?lang=en>`_ is a low cost 360 degrees 2D laser scanner Lidar from SLAMTEC.

.. figure:: /images/usd_assets_sensors/isim_4.5_full_ref_viewport_Isaac_Sensors_RPLidar_S2e.png
    :align: center
    :alt: RPLIDAR S2E
    :width: 50%

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>Slamtec>RPLIDAR S2E*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Slamtec>RPLIDAR_S2E.usd*

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: RPLIDAR S2E Features
        :file: /csv/RPLIDAR_S2E.csv
        :align: center


.. Note::
    For the datasheet and full list of specifications, vist the `RPLIDAR S2 product page. <https://www.slamtec.com/en/support#rplidar-s2>`_

ZVISION
-----------

ML-30s+ (Certified)
########################################

`ZVISION ML-30s+ <http://zvision.xyz/en/h-col-262.html>`_ is a short range automotive grade solid state Lidar. Note there is no mesh for this lidar, so
when it is created via the UI, only a prim will appear in the Stage window.


.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: ML-30s+ Features
        :file: /csv/ZVISION_ML30S.csv
        :align: center
        :widths: 22 40
        :header-rows: 1

    To create the sensor from the menu: *Create>Sensors>RTX Lidar>ZVISION>ML30S+*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>ZVISION>ZVISION_ML30S.usda*

.. Note::
    For the datasheet and full list of specifications, visit the `ML-30s+ product page. <http://zvision.xyz/en/h-col-262.html>`_



ML-Xs (Certified)
#####################################

`ZVISION ML-Xs <http://zvision.xyz/en/h-col-279.html>`_ is a long range automotive high performance grade solid state Lidar. Note there is no mesh for this lidar, so
when it is created via the UI, only a prim will appear in the Stage window.

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    .. csv-table:: ML-30s+ Features
        :file: /csv/ZVISION_MLXS.csv
        :align: center
        :widths: 22 40
        :header-rows: 1

    To create the Lidar prim: *Create>Sensors>RTX Lidar>ZVISION>MLXS*

To create the sensor from the Content Browser: *Isaac Sim>Sensors>ZVISION>ZVISION_MLXS.usda*

.. Note::
    For the datasheet and full list of specifications, visit the `ML-Xs product page. <http://zvision.xyz/en/h-col-279.html>`_

Tactile Sensors
===============

Tashan Technology
------------------

Universal Tactile Sensor TS-F-A (Certified)
###########################################

`Tashan Technology Universal Tactile Sensor TS-F-A <https://github.com/TashanTec/Tashan-Isaac-Sim>`_ is a tactile simulation model based on real products to advance research and innovation in robotic tactile perception technology and promote the development of embodied intelligent robots.

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_viewport_Isaac_Sensors_Tashan_TS-F-A.png
    :align: center
    :alt: Tashan TS-F-A
    :width: 50%

.. dropdown:: Features and Specification
    :animate: fade-in
    :color: light

    Outputs 11 dimensional feature channels:
        - Proximity sensing [1]
        - Tactile sensing [2-4]: Normal force, tangential force, tangential force direction
        - Raw capacitance values [5-11]: 7-channel raw capacitance data

To create the sensor from the Content Browser: *Isaac Sim>Sensors>Tashan>TS-F-A>TS-F-A.usd*

.. Note::
    For usage in |isaac-sim_short|, visit the `Tashan Technology Tactile Simulation Platform User Manual. <https://github.com/TashanTec/Tashan-Isaac-Sim>`_

IMU Sensors
===========

STMicroelectronics
------------------

STMicroelectronics provides an Isaac Sim extension for simulating their MEMS-based IMU sensors. The doc link is available `here <https://github.com/STMicroelectronics/st-mems-isaac-sim2real>`__.

Please follow the instructions in the link to install the extension and create the sensor.

ASM330LHH
#########   

`STMicroelectronics ASM330LHH <https://www.st.com/resource/en/datasheet/asm330lhh.pdf>`_ is a automotive 6 axis inertial module with 3D accelerometer and 3D gyroscope.

.. Note:: Datasheet is available for download `here <https://www.st.com/resource/en/datasheet/asm330lhh.pdf>`__

LSM6DSV
#########

`STMicroelectronics LSM6DSV <https://www.st.com/resource/en/datasheet/lsm6dsv.pdf>`_ is a automotive 6 axis inertial module with 3 axis digital accelerometer and 3 axis digital gyroscope.

.. Note:: Datasheet is available for download `here <https://www.st.com/resource/en/datasheet/lsm6dsv.pdf>`__

Sensor Gizmo in Viewport
=========================

In |isaac-sim_short|, the sensor functions are decoupled from physical meshes, and you can have sensors on stage without any mesh associated with the sensor. We use sensor gizmo to track the location of the actual sensing functions regardless of mesh. The gizmos are not visible by default, but you can toggle them on or off in the viewport.

To toggle the sensor gizmos, go to **Viewport Menu** > |eyecon| > **Show By Type** > **Sensors**.

.. figure:: /images/usd_assets_sensors/isim_5.0_full_ref_gui_sensor_gizmos.webp
    :width: 500
    :align: center

.. |eyecon| image:: /images/isim_4.5_base_ref_gui_eyecon.png
    :width: 30
