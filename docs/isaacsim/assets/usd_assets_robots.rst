..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_assets_robots:

================================
Robot Assets
================================

|isaac-sim| supports a wide range of robots with differential bases, form factors, and functions.

These robots can be categorized as wheeled robots, holonomic robots, quadruped robots, robotic manipulator and aerial robots (drones). They can be found in the Content Browser in the ``Isaac Sim/Robots`` folder.

.. tab-set::

    .. tab-item:: Wheeled


        | **iRobot**

        .. tab-set::

            .. tab-item:: Create3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_iRobot_Create3_create_3.usd.png
                  :align: center
                  :alt: Create3 Robot
                  :width: 80%

                  **USD Path:** iRobot/Create3/create_3.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 4
                        * - Number of Links
                          - 5
                        * - Number of DOFs
                          - 4

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/iRobotEducation/create3_sim/tree/main>`__

        | **Turtlebot**

        .. tab-set::

            .. tab-item:: Turtlebot3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Turtlebot_Turtlebot3_turtlebot3_burger.usd.png
                  :align: center
                  :alt: Turtlebot3 Robot
                  :width: 80%

                  **USD Path:** Turtlebot/Turtlebot3/turtlebot3_burger.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `Apache 2.0 <https://github.com/ROBOTIS-GIT/turtlebot3/tree/master/turtlebot3_description>`__

        | **NVIDIA**

        .. tab-set::

            .. tab-item:: Robomaker


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Robomaker_aws_robomaker_jetbot.usd.png
                  :align: center
                  :alt: Robomaker Robot
                  :width: 80%

                  **USD Path:** NVIDIA/Robomaker/aws_robomaker_jetbot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 5
                        * - Number of Links
                          - 6
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `MIT <https://github.com/aws-samples/aws-robomaker-jetbot-ros/blob/main/LICENSE>`__  

            .. tab-item:: NovaCarter


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_NovaCarter_nova_carter.usd.png
                  :align: center
                  :alt: NovaCarter Robot
                  :width: 80%

                  **USD Path:** NVIDIA/NovaCarter/nova_carter.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 7

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensor/Accessory
                          - Count

                        * - Camera
                          - 12

                        * - IMU
                          - 5

                        * - OmniSensor Lidar
                          - 3

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing - Nova Carter.pdf>`

            .. tab-item:: Leatherback


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Leatherback_leatherback.usd.png
                  :align: center
                  :alt: Leatherback Robot
                  :width: 80%

                  **USD Path:** NVIDIA/Leatherback/leatherback.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 26
                        * - Number of Links
                          - 27
                        * - Number of DOFs
                          - 26

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 4

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX CollisionAPI

                    **License:** NVIDIA

            .. tab-item:: Jetbot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Jetbot_jetbot.usd.png
                  :align: center
                  :alt: Jetbot Robot
                  :width: 80%

                  **USD Path:** NVIDIA/Jetbot/jetbot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 2

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    - PhysX SceneAPI

                    **License:** Email confirmation: `Jetbot 3D drawing <http://www.waveshare.net/w/upload/4/49/Jetbot_3D_Drawing.zip>`__  

            .. tab-item:: Carter


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Carter_carter_v1.usd.png
                          :align: center
                          :alt: Carter Robot Variant 1
                          :width: 80%

                          **USD Path:** NVIDIA/Carter/carter_v1.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 4

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensors
                                  - Count
                                * - Camera
                                  - 5

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                            **License:** NVIDIA

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Carter_carter_v1_physx_lidar.usd.png
                          :align: center
                          :alt: Carter Robot Variant 2
                          :width: 80%

                          **USD Path:** NVIDIA/Carter/carter_v1_physx_lidar.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 4

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensors
                                  - Count
                                * - Camera
                                  - 4

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                            **License:** NVIDIA

        | **IsaacSim**

        .. tab-set::

            .. tab-item:: ForkliftC


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_ForkliftC_forklift_c.usd.png
                  :align: center
                  :alt: ForkliftC Robot
                  :width: 80%

                  **USD Path:** IsaacSim/ForkliftC/forklift_c.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 7

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX CollisionAPI

            .. tab-item:: ForkliftB


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_ForkliftB_forklift_b.usd.png
                          :align: center
                          :alt: ForkliftB Robot Variant 1
                          :width: 80%

                          **USD Path:** IsaacSim/ForkliftB/forklift_b.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 7
                                * - Number of Links
                                  - 8
                                * - Number of DOFs
                                  - 7

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX CollisionAPI

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_ForkliftB_forklift_b_sensor.usd.png
                          :align: center
                          :alt: ForkliftB Robot Variant 2
                          :width: 80%

                          **USD Path:** IsaacSim/ForkliftB/forklift_b_sensor.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensor/Accessory
                                  - Count

                                * - Camera
                                  - 6

                                * - IMU
                                  - 3

                                * - OmniSensor Lidar
                                  - 1

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX CollisionAPI

        | **Idealworks**

        .. tab-set::

            .. tab-item:: iwhub


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Idealworks_iwhub_iw_hub.usd.png
                          :align: center
                          :alt: iwhub Robot Variant 1
                          :width: 80%

                          **USD Path:** Idealworks/iwhub/iw_hub.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 7
                                * - Number of Links
                                  - 8
                                * - Number of DOFs
                                  - 7

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Idealworks_iwhub_iw_hub_sensors.usd.png
                          :align: center
                          :alt: iwhub Robot Variant 2
                          :width: 80%

                          **USD Path:** Idealworks/iwhub/iw_hub_sensors.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensors
                                  - Count
                                * - Camera
                                  - 2

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX CollisionAPI

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            - PhysX SceneAPI

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Idealworks_iwhub_iw_hub_static.usd.png
                          :align: center
                          :alt: iwhub Robot Variant 3
                          :width: 80%

                          **USD Path:** Idealworks/iwhub/iw_hub_static.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

        | **Fraunhofer**

        .. tab-set::

            .. tab-item:: Evobot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Fraunhofer_Evobot_evobot.usd.png
                  :align: center
                  :alt: Evobot Robot
                  :width: 80%

                  **USD Path:** Fraunhofer/Evobot/evobot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/CLA-1_OpenLogisticsFoundation_Fraunhofer_-_NVIDIA.pdf>`

        | **Clearpath**

        .. tab-set::

            .. tab-item:: Jackal


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_Jackal_jackal.usd.png
                          :align: center
                          :alt: Jackal Robot Variant 1
                          :width: 80%

                          **USD Path:** Clearpath/Jackal/jackal.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 4
                                * - Number of Links
                                  - 5
                                * - Number of DOFs
                                  - 4

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensor/Accessory
                                  - Count

                                * - Camera
                                  - 2

                                * - IMU
                                  - 1

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/jackal/jackal/blob/noetic-devel/LICENSE>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_Jackal_jackal_basic.usd.png
                          :align: center
                          :alt: Jackal Robot Variant 2
                          :width: 80%

                          **USD Path:** Clearpath/Jackal/jackal_basic.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 4
                                * - Number of Links
                                  - 5
                                * - Number of DOFs
                                  - 4

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/jackal/jackal/blob/noetic-devel/LICENSE>`__  

            .. tab-item:: Dingo


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_Dingo_dingo.usd.png
                          :align: center
                          :alt: Dingo Robot Variant 1
                          :width: 80%

                          **USD Path:** Clearpath/Dingo/dingo.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 2
                                * - Number of Links
                                  - 3
                                * - Number of DOFs
                                  - 2

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensors
                                  - Count
                                * - Camera
                                  - 2

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/dingo-cpr/dingo/blob/noetic-devel/dingo_description/package.xml>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_Dingo_dingo_basic.usd.png
                          :align: center
                          :alt: Dingo Robot Variant 2
                          :width: 80%

                          **USD Path:** Clearpath/Dingo/dingo_basic.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 2
                                * - Number of Links
                                  - 3
                                * - Number of DOFs
                                  - 2

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/dingo-cpr/dingo/blob/noetic-devel/dingo_description/package.xml>`__  

        | **AgilexRobotics**

        .. tab-set::

            .. tab-item:: limo


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_AgilexRobotics_limo_limo.usd.png
                  :align: center
                  :alt: limo Robot
                  :width: 80%

                  **USD Path:** AgilexRobotics/limo/limo.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 4
                        * - Number of Links
                          - 5
                        * - Number of DOFs
                          - 4

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 1

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    **License:** `BSD-3 <https://github.com/agilexrobotics/Limo-Isaac-Sim>`__

    .. tab-item:: Manipulator


        | **Yaskawa**

        .. tab-set::

            .. tab-item:: Motoman Next


                .. tab-set::

                    .. tab-item:: NHC12

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NHC12_NHC12_A00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NHC12
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NHC12/NHC12_A00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

                    .. tab-item:: NEX7

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NEX7_NEX7_C00_c00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NEX7
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NEX7/NEX7_C00_c00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

                    .. tab-item:: NEX4

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NEX4_NEX4_C00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NEX4
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NEX4/NEX4_C00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

                    .. tab-item:: NEX35

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NEX35_NEX35_C00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NEX35
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NEX35/NEX35_C00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

                    .. tab-item:: NEX20

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NEX20_NEX20_C00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NEX20
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NEX20/NEX20_C00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

                    .. tab-item:: NEX10

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Yaskawa_Motoman_Next_NEX10_NEX10_C00.usd.png
                          :align: center
                          :alt: Motoman Next Robot NEX10
                          :width: 80%

                          **USD Path:** Yaskawa/Motoman Next/NEX10/NEX10_C00.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 6
                                * - Number of Links
                                  - 7
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing_YASKAWA Signed.pdf>`

        | **Yahboom**

        .. tab-set::

            .. tab-item:: Dofbot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Yahboom_Dofbot_dofbot.usd.png
                  :align: center
                  :alt: Dofbot Robot
                  :width: 80%

                  **USD Path:** Yahboom/Dofbot/dofbot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 11
                        * - Number of Links
                          - 12
                        * - Number of DOFs
                          - 11

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 1

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    - PhysX SceneAPI

                    **License:** Email confirmation: `Yahboom Technology <https://github.com/YahboomTechnology/dofbot-jetson_nano>`__  

        | **WonikRobotics**

        .. tab-set::

            .. tab-item:: AllegroHand


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_WonikRobotics_AllegroHand_allegro.usd.png
                          :align: center
                          :alt: AllegroHand Robot Variant 1
                          :width: 80%

                          **USD Path:** WonikRobotics/AllegroHand/allegro.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 20
                                * - Number of Links
                                  - 21
                                * - Number of DOFs
                                  - 16

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-2 <https://github.com/simlabrobotics/allegro_hand_ros_v4/blob/master/LICENSE>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_WonikRobotics_AllegroHand_allegro_hand.usd.png
                          :align: center
                          :alt: AllegroHand Robot Variant 2
                          :width: 80%

                          **USD Path:** WonikRobotics/AllegroHand/allegro_hand.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 20
                                * - Number of Links
                                  - 21
                                * - Number of DOFs
                                  - 16

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            **License:** `BSD-2 <https://github.com/simlabrobotics/allegro_hand_ros_v4/blob/master/LICENSE>`__

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_WonikRobotics_AllegroHand_allegro_hand_instanceable.usd.png
                          :align: center
                          :alt: AllegroHand Robot Variant 3
                          :width: 80%

                          **USD Path:** WonikRobotics/AllegroHand/allegro_hand_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 20
                                * - Number of Links
                                  - 21
                                * - Number of DOFs
                                  - 16

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            * This robot is in Isaac Lab

                            **License:** `BSD-2 <https://github.com/simlabrobotics/allegro_hand_ros_v4/blob/master/LICENSE>`__ 

        | **UniversalRobots**

        .. tab-set::

            .. tab-item:: ur5e


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur5e_ur5e.usd.png
                  :align: center
                  :alt: ur5e Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur5e/ur5e.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur5


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur5_ur5.usd.png
                  :align: center
                  :alt: ur5 Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur5/ur5.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur3e


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur3e_ur3e.usd.png
                  :align: center
                  :alt: ur3e Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur3e/ur3e.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur30


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur30_ur30.usd.png
                  :align: center
                  :alt: ur30 Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur30/ur30.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur3_ur3.usd.png
                  :align: center
                  :alt: ur3 Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur3/ur3.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur20


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur20_ur20.usd.png
                  :align: center
                  :alt: ur20 Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur20/ur20.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur16e


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur16e_ur16e.usd.png
                  :align: center
                  :alt: ur16e Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur16e/ur16e.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur10e


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur10e_ur10e.usd.png
                  :align: center
                  :alt: ur10e Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur10e/ur10e.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Accessories:**

                    - Robotiq_2f_140

                    - Robotiq_2f_85

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

            .. tab-item:: ur10


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_UniversalRobots_ur10_ur10.usd.png
                  :align: center
                  :alt: ur10 Robot
                  :width: 80%

                  **USD Path:** UniversalRobots/ur10/ur10.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Accessories:**

                    - Long_Suction

                    - Short_Suction

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/fmauch/universal_robot>`__  

        | **Unitree**

        .. tab-set::

            .. tab-item:: Z1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Z1_z1.usd.png
                  :align: center
                  :alt: Z1 Robot
                  :width: 80%

                  **USD Path:** Unitree/Z1/z1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: Dex5


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Dex5_Dex5_URDF_R.usd.png
                  :align: center
                  :alt: Dex5 Robot
                  :width: 80%

                  **USD Path:** Unitree/Dex5/Dex5-URDF-R.usda

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 20
                        * - Number of Links
                          - 21
                        * - Number of DOFs
                          - 20

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: Dex3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Dex3_dex3_1_r.usd.png
                  :align: center
                  :alt: Dex3 Robot
                  :width: 80%

                  **USD Path:** Unitree/Dex3/dex3_1_r.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 7

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

        | **Ufactory**

        .. tab-set::

            .. tab-item:: xarm_gripper


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_xarm_gripper_xarm_gripper.usd.png
                  :align: center
                  :alt: xarm_gripper Robot
                  :width: 80%

                  **USD Path:** Ufactory/xarm_gripper/xarm_gripper.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

            .. tab-item:: xarm7


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_xarm7_xarm7.usd.png
                  :align: center
                  :alt: xarm7 Robot
                  :width: 80%

                  **USD Path:** Ufactory/xarm7/xarm7.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 13

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

            .. tab-item:: xarm6


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_xarm6_xarm6.usd.png
                  :align: center
                  :alt: xarm6 Robot
                  :width: 80%

                  **USD Path:** Ufactory/xarm6/xarm6.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 13
                        * - Number of Links
                          - 14
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI
                    
                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

            .. tab-item:: uf850


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_uf850_uf850.usd.png
                  :align: center
                  :alt: uf850 Robot
                  :width: 80%

                  **USD Path:** Ufactory/uf850/uf850.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

            .. tab-item:: lite6_gripper


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_lite6_gripper_uf_lite_gripper.usd.png
                  :align: center
                  :alt: lite6_gripper Robot
                  :width: 80%

                  **USD Path:** Ufactory/lite6_gripper/uf_lite_gripper.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    - PhysX RigidBodyAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

            .. tab-item:: lite6


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ufactory_lite6_lite6.usd.png
                  :align: center
                  :alt: lite6 Robot
                  :width: 80%

                  **USD Path:** Ufactory/lite6/lite6.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing 1_Ufactory.pdf>`

        | **Techman**

        .. tab-set::

            .. tab-item:: TM12


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Techman_TM12_tm12.usd.png
                  :align: center
                  :alt: TM12 Robot
                  :width: 80%

                  **USD Path:** Techman/TM12/tm12.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 9
                        * - Number of Links
                          - 10
                        * - Number of DOFs
                          - 6

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 1

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Techman - Signed 3D Content Sharing.pdf>`

        | **ShadowRobot**

        .. tab-set::

            .. tab-item:: ShadowHand


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_ShadowRobot_ShadowHand_shadow_hand.usd.png
                          :align: center
                          :alt: ShadowHand Robot Variant 1
                          :width: 80%

                          **USD Path:** ShadowRobot/ShadowHand/shadow_hand.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 25
                                * - Number of Links
                                  - 26
                                * - Number of DOFs
                                  - 24

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            **License:** `BSD-3 <https://github.com/shadow-robot/sr_common/blob/noetic-devel/LICENSE>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_ShadowRobot_ShadowHand_shadow_hand_instanceable.usd.png
                          :align: center
                          :alt: ShadowHand Robot Variant 2
                          :width: 80%

                          **USD Path:** ShadowRobot/ShadowHand/shadow_hand_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 25
                                * - Number of Links
                                  - 26
                                * - Number of DOFs
                                  - 24

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            * This robot is in Isaac Lab

                            **License:** `BSD-3 <https://github.com/shadow-robot/sr_common/blob/noetic-devel/LICENSE>`__  

        | **Robotiq**

        .. tab-set::

            .. tab-item:: Hand-E


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_Hand_E_Robotiq_Hand_E_base.usd.png
                          :align: center
                          :alt: Hand-E Robot Variant 1
                          :width: 80%

                          **USD Path:** Robotiq/Hand-E/Robotiq_Hand_E_base.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 2
                                * - Number of Links
                                  - 3
                                * - Number of DOFs
                                  - 2

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_Hand_E_Robotiq_Hand_E_edit.usd.png
                          :align: center
                          :alt: Hand-E Robot Variant 3
                          :width: 80%

                          **USD Path:** Robotiq/Hand-E/Robotiq_Hand_E_edit.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 2
                                * - Number of Links
                                  - 3
                                * - Number of DOFs
                                  - 2

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

            .. tab-item:: 2F-85


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_85_Robotiq_2F_85_edit.usd.png
                  :align: center
                  :alt: 2F-85 Robot
                  :width: 80%

                  **USD Path:** Robotiq/2F-85/Robotiq_2F_85_edit.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 8
                        * - Number of Links
                          - 9
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

            .. tab-item:: 2F-140


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_140_2f140_instanceable.usd.png
                          :align: center
                          :alt: 2F-140 Robot Variant 1
                          :width: 80%

                          **USD Path:** Robotiq/2F-140/2f140_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 10
                                * - Number of Links
                                  - 11
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_140_Robotiq_2F_140_base.usd.png
                          :align: center
                          :alt: 2F-140 Robot Variant 2
                          :width: 80%

                          **USD Path:** Robotiq/2F-140/Robotiq_2F_140_base.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 8
                                * - Number of Links
                                  - 9
                                * - Number of DOFs
                                  - 8

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_140_Robotiq_2F_140_config.usd.png
                          :align: center
                          :alt: 2F-140 Robot Variant 3
                          :width: 80%

                          **USD Path:** Robotiq/2F-140/Robotiq_2F_140_config.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 10
                                * - Number of Links
                                  - 11
                                * - Number of DOFs
                                  - 10

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensor/Accessory
                                  - Count

                                * - Contact Sensor
                                  - 1

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX SceneAPI

                            - PhysX ResidualReportingAPI

                            - PhysX MimicJointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

                    .. tab-item:: Variant 4

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_140_Robotiq_2F_140_physics_edit.usd.png
                          :align: center
                          :alt: 2F-140 Robot Variant 4
                          :width: 80%

                          **USD Path:** Robotiq/2F-140/Robotiq_2F_140_physics_edit.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 8
                                * - Number of Links
                                  - 9
                                * - Number of DOFs
                                  - 8

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensor/Accessory
                                  - Count

                                * - Contact Sensor
                                  - 1

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX MimicJointAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

                    .. tab-item:: Variant 5

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Robotiq_2F_140_Collected_2f140_instanceable_2f140_instanceable.usd.png
                          :align: center
                          :alt: 2F-140 Robot Variant 5
                          :width: 80%

                          **USD Path:** Robotiq/2F-140/Collected_2f140_instanceable/2f140_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 10
                                * - Number of Links
                                  - 11
                                * - Number of DOFs
                                  - 6

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/NVIDIA - Robotiq 3D Content Sharing.docx.pdf>`

        | **Psyonic**

        .. tab-set::

            .. tab-item:: ability_hand_left_large


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Psyonic_ability_hand_left_large_ability_hand_left_large.usd.png
                  :align: center
                  :alt: ability_hand_left_large Robot
                  :width: 80%

                  **USD Path:** Psyonic/ability_hand_left_large/ability_hand_left_large.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 11

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_Psyonic Inc.pdf>`

            .. tab-item:: ability_hand_left_small


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Psyonic_ability_hand_left_small_ability_hand_left_small.usd.png
                  :align: center
                  :alt: ability_hand_left_small Robot
                  :width: 80%

                  **USD Path:** Psyonic/ability_hand_left_small/ability_hand_left_small.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 11

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_Psyonic Inc.pdf>`

            .. tab-item:: ability_hand_right_large


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Psyonic_ability_hand_right_large_ability_hand_right_large.usd.png
                  :align: center
                  :alt: ability_hand_right_large Robot
                  :width: 80%

                  **USD Path:** Psyonic/ability_hand_right_large/ability_hand_right_large.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 11

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_Psyonic Inc.pdf>`

            .. tab-item:: ability_hand_right_small


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Psyonic_ability_hand_right_small_ability_hand_right_small.usd.png
                  :align: center
                  :alt: ability_hand_right_small Robot
                  :width: 80%

                  **USD Path:** Psyonic/ability_hand_right_small/ability_hand_right_small.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 11

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_Psyonic Inc.pdf>`

        | **Schunk**

        .. tab-set::

            .. tab-item:: egk_25


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Schunk_egk_25_schunk_egk_25.usd.png
                  :align: center
                  :alt: egk_25 Robot
                  :width: 80%

                  **USD Path:** Schunk/egk_25/schunk_egk_25.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_SCHUNK SE & Co KG.pdf>`

            .. tab-item:: egu_50


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Schunk_egu_50_schunk_egu_50.usd.png
                  :align: center
                  :alt: egu_50 Robot
                  :width: 80%

                  **USD Path:** Schunk/egu_50/schunk_egu_50.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_SCHUNK SE & Co KG.pdf>`

            .. tab-item:: ezu_35


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Schunk_ezu_35_schunk_ezu_35.usd.png
                  :align: center
                  :alt: ezu_35 Robot
                  :width: 80%

                  **USD Path:** Schunk/ezu_35/schunk_ezu_35.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_SCHUNK SE & Co KG.pdf>`

            .. tab-item:: svh-flat-l


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Schunk_svh_flat_l_svh_flat_l_v2.usd.png
                  :align: center
                  :alt: svh-flat-l Robot
                  :width: 80%

                  **USD Path:** Schunk/svh-flat-l/svh-flat-l_v2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 24
                        * - Number of Links
                          - 25
                        * - Number of DOFs
                          - 24

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_SCHUNK SE & Co KG.pdf>`

            .. tab-item:: svh-flat-r


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Schunk_svh_flat_r_svh_flat_r_v2.usd.png
                  :align: center
                  :alt: svh-flat-r Robot
                  :width: 80%

                  **USD Path:** Schunk/svh-flat-r/svh-flat-r_v2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 24
                        * - Number of Links
                          - 25
                        * - Number of DOFs
                          - 24

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_SCHUNK SE & Co KG.pdf>`

        | **RobotStudio**

        .. tab-set::

            .. tab-item:: so101_new_calib


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_RobotStudio_so101_new_calib_so101_new_calib.usd.png
                  :align: center
                  :alt: so101_new_calib Robot
                  :width: 80%

                  **USD Path:** RobotStudio/so101_new_calib/so101_new_calib.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `Apache 2.0 <https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation/SO101>`__

            .. tab-item:: so100


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_RobotStudio_so100_so100.usd.png
                  :align: center
                  :alt: so100 Robot
                  :width: 80%

                  **USD Path:** RobotStudio/so100/so100.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `Apache 2.0 <https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation/SO101>`__

        | **RethinkRobotics**

        .. tab-set::

            .. tab-item:: Sawyer


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_RethinkRobotics_Sawyer_sawyer_instanceable.usd.png
                  :align: center
                  :alt: Sawyer Robot
                  :width: 80%

                  **USD Path:** RethinkRobotics/Sawyer/sawyer_instanceable.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 8

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    * This robot is in Isaac Lab

                    **License:** `Apache 2.0 <http://github.com/RethinkRobotics/sawyer_robot>`__

        | **Kuka**

        .. tab-set::

            .. tab-item:: KR210_L150


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kuka_KR210_L150_kr210_l150.usd.png
                  :align: center
                  :alt: KR210_L150 Robot
                  :width: 80%

                  **USD Path:** Kuka/KR210_L150/kr210_l150.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 8
                        * - Number of Links
                          - 9
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `Apache 2.0 <https://github.com/ros-industrial/kuka_experimental>`__

        | **Kinova**

        .. tab-set::

            .. tab-item:: Jaco2


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kinova_Jaco2_J2N7S300_j2n7s300_instanceable.usd.png
                          :align: center
                          :alt: Jaco2 Robot Variant 1
                          :width: 80%

                          **USD Path:** Kinova/Jaco2/J2N7S300/j2n7s300_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 14
                                * - Number of Links
                                  - 15
                                * - Number of DOFs
                                  - 13

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kinova_Jaco2_J2N6S300_j2n6s300_instanceable.usd.png
                          :align: center
                          :alt: Jaco2 Robot Variant 2
                          :width: 80%

                          **USD Path:** Kinova/Jaco2/J2N6S300/j2n6s300_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 13
                                * - Number of Links
                                  - 14
                                * - Number of DOFs
                                  - 12

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

            .. tab-item:: Gen3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kinova_Gen3_gen3n7_instanceable.usd.png
                  :align: center
                  :alt: Gen3 Robot
                  :width: 80%

                  **USD Path:** Kinova/Gen3/gen3n7_instanceable.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 8
                        * - Number of Links
                          - 9
                        * - Number of DOFs
                          - 7

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

        | **Kawasaki**

        .. tab-set::

            .. tab-item:: RS080N


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kawasaki_RS080N_rs080n_onrobot_rg2.usd.png
                  :align: center
                  :alt: RS080N Robot
                  :width: 80%

                  **USD Path:** Kawasaki/RS080N/rs080n_onrobot_rg2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 15
                        * - Number of Links
                          - 16
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-Kawasaki.pdf>`

            .. tab-item:: RS025N


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kawasaki_RS025N_rs025n_onrobot_rg2.usd.png
                  :align: center
                  :alt: RS025N Robot
                  :width: 80%

                  **USD Path:** Kawasaki/RS025N/rs025n_onrobot_rg2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 15
                        * - Number of Links
                          - 16
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-Kawasaki.pdf>`

            .. tab-item:: RS013N


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kawasaki_RS013N_rs013n_onrobot_rg2.usd.png
                  :align: center
                  :alt: RS013N Robot
                  :width: 80%

                  **USD Path:** Kawasaki/RS013N/rs013n_onrobot_rg2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 15
                        * - Number of Links
                          - 16
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-Kawasaki.pdf>`

            .. tab-item:: RS007N


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kawasaki_RS007N_rs007n_onrobot_rg2.usd.png
                  :align: center
                  :alt: RS007N Robot
                  :width: 80%

                  **USD Path:** Kawasaki/RS007N/rs007n_onrobot_rg2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 15
                        * - Number of Links
                          - 16
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-Kawasaki.pdf>`

            .. tab-item:: RS007L


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Kawasaki_RS007L_rs007l_onrobot_rg2.usd.png
                  :align: center
                  :alt: RS007L Robot
                  :width: 80%

                  **USD Path:** Kawasaki/RS007L/rs007l_onrobot_rg2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 15
                        * - Number of Links
                          - 16
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-Kawasaki.pdf>`

        | **FrankaRobotics**

        .. tab-set::

            .. tab-item:: FrankaPanda


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FrankaRobotics_FrankaPanda_franka.usd.png
                  :align: center
                  :alt: FrankaPanda Robot
                  :width: 80%

                  **USD Path:** FrankaRobotics/FrankaPanda/franka.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 10
                        * - Number of Links
                          - 11
                        * - Number of DOFs
                          - 9

                    **Accessories:**

                    - AlternateFinger

                    - Default

                    - Robotiq_2F_85

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX RigidBodyAPI

                    **License:** `Apache 2.0 <https://github.com/frankaemika/franka_ros/tree/kinetic-devel/franka_description>`__  

            .. tab-item:: FrankaFR3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FrankaRobotics_FrankaFR3_fr3.usd.png
                  :align: center
                  :alt: FrankaFR3 Robot
                  :width: 80%

                  **USD Path:** FrankaRobotics/FrankaFR3/fr3.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 9

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** `Apache 2.0 <https://github.com/frankaemika/franka_ros/tree/kinetic-devel/franka_description>`__  

            .. tab-item:: FrankaEmika


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FrankaRobotics_FrankaEmika_panda_instanceable.usd.png
                  :align: center
                  :alt: FrankaEmika Robot
                  :width: 80%

                  **USD Path:** FrankaRobotics/FrankaEmika/panda_instanceable.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 10
                        * - Number of Links
                          - 11
                        * - Number of DOFs
                          - 9

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `Apache 2.0 <https://github.com/frankaemika/franka_ros/tree/kinetic-devel/franka_description>`__  

            .. tab-item:: FactoryFranka


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FrankaRobotics_FactoryFranka_factory_franka.usd.png
                          :align: center
                          :alt: FactoryFranka Robot Variant 1
                          :width: 80%

                          **USD Path:** FrankaRobotics/FactoryFranka/factory_franka.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 11
                                * - Number of Links
                                  - 12
                                * - Number of DOFs
                                  - 9

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            **License:** `Apache 2.0 <https://github.com/frankaemika/franka_ros/tree/kinetic-devel/franka_description>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FrankaRobotics_FactoryFranka_factory_franka_instanceable.usd.png
                          :align: center
                          :alt: FactoryFranka Robot Variant 2
                          :width: 80%

                          **USD Path:** FrankaRobotics/FactoryFranka/factory_franka_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 11
                                * - Number of Links
                                  - 12
                                * - Number of DOFs
                                  - 9

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI
                            
                            **License:** `Apache 2.0 <https://github.com/frankaemika/franka_ros/tree/kinetic-devel/franka_description>`__  

        | **Flexiv**

        .. tab-set::

            .. tab-item:: Rizon4


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Flexiv_Rizon4_flexiv_rizon4.usd.png
                  :align: center
                  :alt: Rizon4 Robot
                  :width: 80%

                  **USD Path:** Flexiv/Rizon4/flexiv_rizon4.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 8
                        * - Number of Links
                          - 9
                        * - Number of DOFs
                          - 7

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing- FlexIV.pdf>`

        | **Fanuc**

        .. tab-set::

            .. tab-item:: CRX10IAL


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Fanuc_CRX10IAL_crx10ial.usd.png
                  :align: center
                  :alt: CRX10IAL Robot
                  :width: 80%

                  **USD Path:** Fanuc/CRX10IAL/crx10ial.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 9
                        * - Number of Links
                          - 10
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: cr_50f_16b


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_cr_50f_16b_cr_50f_16b.usd.png
                  :align: center
                  :alt: cr_50f_16b Robot
                  :width: 80%

                  **USD Path:** Fanuc/cr_50f_16b/cr_50f_16b.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: crx10ia


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_crx10ia_crx10ia.usd.png
                  :align: center
                  :alt: crx10ia Robot
                  :width: 80%

                  **USD Path:** Fanuc/crx10ia/crx10ia.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: crx5ia


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_crx5ia_crx5ia.usd.png
                  :align: center
                  :alt: crx5ia Robot
                  :width: 80%

                  **USD Path:** Fanuc/crx5ia/crx5ia.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: lrmate200id


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_lrmate200id_lrmate200id.usd.png
                  :align: center
                  :alt: lrmate200id Robot
                  :width: 80%

                  **USD Path:** Fanuc/lrmate200id/lrmate200id.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: m710ic_50


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_m710ic_50_m710ic_50.usd.png
                  :align: center
                  :alt: m710ic_50 Robot
                  :width: 80%

                  **USD Path:** Fanuc/m710ic_50/m710ic_50.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: r2000ic_165f


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_r2000ic_165f_r2000ic_165f.usd.png
                  :align: center
                  :alt: r2000ic_165f Robot
                  :width: 80%

                  **USD Path:** Fanuc/r2000ic_165f/r2000ic_165f.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: sr12ia


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_sr12ia_sr12ia.usd.png
                  :align: center
                  :alt: sr12ia Robot
                  :width: 80%

                  **USD Path:** Fanuc/sr12ia/sr12ia.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: sr3ia


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_sr3ia_sr3ia.usd.png
                  :align: center
                  :alt: sr3ia Robot
                  :width: 80%

                  **USD Path:** Fanuc/sr3ia/sr3ia.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: m900ib280


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_Fanuc_m900ib280_m900ib280.usd.png
                  :align: center
                  :alt: m900ib280 Robot
                  :width: 80%

                  **USD Path:** Fanuc/m900ib280/m900ib280.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing Agreement_FANUC.pdf>`

            .. tab-item:: More


                .. note::

                    Additional FANUC robot assets (84+ models) can be found in the Content Browser at ``IsaacSim/Robots/Fanuc``.

        | **Denso**

        .. tab-set::

            .. tab-item:: CobottaPro900


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Denso_CobottaPro900_cobotta_pro_900.usd.png
                  :align: center
                  :alt: CobottaPro900 Robot
                  :width: 80%

                  **USD Path:** Denso/CobottaPro900/cobotta_pro_900.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing- Denso.pdf>`

            .. tab-item:: CobottaPro1300


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Denso_CobottaPro1300_cobotta_pro_1300.usd.png
                  :align: center
                  :alt: CobottaPro1300 Robot
                  :width: 80%

                  **USD Path:** Denso/CobottaPro1300/cobotta_pro_1300.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing- Denso.pdf>`

        | **Comau**

        .. tab-set::

            .. tab-item:: n-220-27


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_comau_n_220_27_n_220_27.usd.png
                  :align: center
                  :alt: n-220-27 Robot
                  :width: 80%

                  **USD Path:** comau/n-220-27/n-220-27.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 7
                        * - Number of Links
                          - 8
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

        | **OpenArm**

        .. tab-set::

            .. tab-item:: openarm_unimanual


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_OpenArm_openarm_unimanual_openarm_unimanual.usd.png
                  :align: center
                  :alt: openarm_unimanual Robot
                  :width: 80%

                  **USD Path:** OpenArm/openarm_unimanual/openarm_unimanual.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 11
                        * - Number of Links
                          - 12
                        * - Number of DOFs
                          - 11

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    - PhysX MimicJointAPI

                    **License:** `Apache 2.0 <https://github.com/enactic/openarm>`__

            .. tab-item:: openarm_bimanual


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_OpenArm_openarm_bimanual_openarm_bimanual.usd.png
                  :align: center
                  :alt: openarm_bimanual Robot
                  :width: 80%

                  **USD Path:** OpenArm/openarm_bimanual/openarm_bimanual.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 22
                        * - Number of Links
                          - 23
                        * - Number of DOFs
                          - 22

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    - PhysX MimicJointAPI

                    **License:** `Apache 2.0 <https://github.com/enactic/openarm>`__

    .. tab-item:: Humanoid


        | **XiaoPeng**

        .. tab-set::

            .. tab-item:: PX5


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_XiaoPeng_PX5_px5.usd.png
                          :align: center
                          :alt: PX5 Robot Variant 1
                          :width: 80%

                          **USD Path:** XiaoPeng/PX5/px5.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 16
                                * - Number of Links
                                  - 17
                                * - Number of DOFs
                                  - 16

                            **Physics APIs:**

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/XPENG Robotics-Signed 3D Content Sharing.pdf>`

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_XiaoPeng_PX5_px5_without_housing.usd.png
                          :align: center
                          :alt: PX5 Robot Variant 2
                          :width: 80%

                          **USD Path:** XiaoPeng/PX5/px5_without_housing.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 16
                                * - Number of Links
                                  - 17
                                * - Number of DOFs
                                  - 16

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/XPENG Robotics-Signed 3D Content Sharing.pdf>`

        | **X-Humanoid**

        .. tab-set::

            .. tab-item:: Tien Kung


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_XHumanoid_Tien_Kung_tienkung.usd.png
                  :align: center
                  :alt: Tien Kung Robot
                  :width: 80%

                  **USD Path:** XHumanoid/Tien Kung/tienkung.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 59
                        * - Number of Links
                          - 60
                        * - Number of DOFs
                          - 54

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-HRIC.pdf>`

        | **Unitree**

        .. tab-set::

            .. tab-item:: H1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_H1_h1.usd.png
                  :align: center
                  :alt: H1 Robot
                  :width: 80%

                  **USD Path:** Unitree/H1/h1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 24
                        * - Number of Links
                          - 25
                        * - Number of DOFs
                          - 19

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: G1_23dof


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_G1_23dof_g1.usd.png
                          :align: center
                          :alt: G1_23dof Robot Variant 1
                          :width: 80%

                          **USD Path:** Unitree/G1_23dof/g1.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_G1_23dof_g1_minimal.usd.png
                          :align: center
                          :alt: G1_23dof Robot Variant 2
                          :width: 80%

                          **USD Path:** Unitree/G1_23dof/g1_minimal.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: G1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_G1_g1.usd.png
                  :align: center
                  :alt: G1 Robot
                  :width: 80%

                  **USD Path:** Unitree/G1/g1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 45
                        * - Number of Links
                          - 46
                        * - Number of DOFs
                          - 43

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

        | **SanctuaryAI**

        .. tab-set::

            .. tab-item:: Phoenix


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_SanctuaryAI_Phoenix_phoenix.usd.png
                  :align: center
                  :alt: Phoenix Robot
                  :width: 80%

                  **USD Path:** SanctuaryAI/Phoenix/phoenix.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 77
                        * - Number of Links
                          - 78
                        * - Number of DOFs
                          - 77

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Sanctuary-Signed 3D Content Sharing.pdf>`

        | **RobotEra**

        .. tab-set::

            .. tab-item:: STAR1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_RobotEra_STAR1_star1.usd.png
                  :align: center
                  :alt: STAR1 Robot
                  :width: 80%

                  **USD Path:** RobotEra/STAR1/star1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 55
                        * - Number of Links
                          - 56
                        * - Number of DOFs
                          - 55

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/3D Content Sharing-RobotEra20250117.pdf>`

        | **Ihmcrobotics**

        .. tab-set::

            .. tab-item:: Valkyrie


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Ihmcrobotics_Valkyrie_valkyrie.usd.png
                  :align: center
                  :alt: Valkyrie Robot
                  :width: 80%

                  **USD Path:** Ihmcrobotics/Valkyrie/valkyrie.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 25
                        * - Number of Links
                          - 26
                        * - Number of DOFs
                          - 25

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `Apache 2.0 <https://github.com/ihmcrobotics/valkyrie>`__

        | **FourierIntelligence**

        .. tab-set::

            .. tab-item:: GR-1


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FourierIntelligence_GR_1_GR1T2_fourier_hand_6dof_GR1T2_fourier_hand_6dof.usd.png
                          :align: center
                          :alt: GR-1 Robot Variant 1
                          :width: 80%

                          **USD Path:** FourierIntelligence/GR-1/GR1T2_fourier_hand_6dof/GR1T2_fourier_hand_6dof.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 54
                                * - Number of Links
                                  - 55
                                * - Number of DOFs
                                  - 54

                            **Physics APIs:**

                            - PhysX MimicJointAPI

                            - PhysX JointAPI

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            * This robot is in Isaac Lab

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Fourier Intelligence-Signed 3D Content Sharing.pdf>`

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_FourierIntelligence_GR_1_GR1T1_GR1_T1.usd.png
                          :align: center
                          :alt: GR-1 Robot Variant 2
                          :width: 80%

                          **USD Path:** FourierIntelligence/GR-1/GR1T1/GR1_T1.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 40
                                * - Number of Links
                                  - 41
                                * - Number of DOFs
                                  - 32

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI
                            
                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Fourier Intelligence-Signed 3D Content Sharing.pdf>`

        | **Agility**

        .. tab-set::

            .. tab-item:: Digit


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Agility_Digit_digit_v4.usd.png
                  :align: center
                  :alt: Digit Robot
                  :width: 80%

                  **USD Path:** Agility/Digit/digit_v4.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 42
                        * - Number of Links
                          - 43
                        * - Number of DOFs
                          - 38

                    .. list-table::
                        :align: center
                        :widths: 40 40
                        :header-rows: 1

                        * - Sensors
                          - Count
                        * - Camera
                          - 4

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    - PhysX ArticulationAPI

                    * This robot is in Isaac Lab

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Agility - Signed 3D Content Sharing.pdf>`

            .. tab-item:: Cassie


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Agility_Cassie_cassie.usd.png
                  :align: center
                  :alt: Cassie Robot
                  :width: 80%

                  **USD Path:** Agility/Cassie/cassie.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 14

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    - PhysX CollisionAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Agility - Signed 3D Content Sharing.pdf>`

        | **Agibot**

        .. tab-set::

            .. tab-item:: A2D


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Agibot_A2D_A2D.usd.png
                  :align: center
                  :alt: A2D Robot
                  :width: 80%

                  **USD Path:** Agibot/A2D/A2D.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 34
                        * - Number of Links
                          - 35
                        * - Number of DOFs
                          - 34

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Agitbot G1 Model Sharing Agreement.pdf>`

        | **1X**

        .. tab-set::

            .. tab-item:: Neo


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_1X_Neo_Neo.usd.png
                  :align: center
                  :alt: Neo Robot
                  :width: 80%

                  **USD Path:** 1X/Neo/Neo.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 33
                        * - Number of Links
                          - 34
                        * - Number of DOFs
                          - 33

                    **Physics APIs:**

                    - PhysX MimicJointAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/1X-signed 3D Content Sharing.pdf>`

        | **BoosterRobotics**

        .. tab-set::

            .. tab-item:: BoosterT1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_BoosterRobotics_BoosterT1_T1_locomotion.usd.png
                  :align: center
                  :alt: BoosterT1 Robot
                  :width: 80%

                  **USD Path:** BoosterRobotics/BoosterT1/T1_locomotion.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 23
                        * - Number of Links
                          - 24
                        * - Number of DOFs
                          - 23

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `Apache 2.0 <https://github.com/BoosterRobotics/booster_gym>`__

    .. tab-item:: Quadruped


        | **Unitree**

        .. tab-set::

            .. tab-item:: laikago


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_laikago_laikago.usd.png
                  :align: center
                  :alt: laikago Robot
                  :width: 80%

                  **USD Path:** Unitree/laikago/laikago.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: aliengo


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_aliengo_aliengo.usd.png
                  :align: center
                  :alt: aliengo Robot
                  :width: 80%

                  **USD Path:** Unitree/aliengo/aliengo.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 12
                        * - Number of Links
                          - 13
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: Go2


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Go2_go2.usd.png
                  :align: center
                  :alt: Go2 Robot
                  :width: 80%

                  **USD Path:** Unitree/Go2/go2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 38
                        * - Number of Links
                          - 39
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: Go1


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Go1_go1.usd.png
                          :align: center
                          :alt: Go1 Robot Variant 1
                          :width: 80%

                          **USD Path:** Unitree/Go1/go1.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 16
                                * - Number of Links
                                  - 17
                                * - Number of DOFs
                                  - 12

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_Go1_go1_sensor.usd.png
                          :align: center
                          :alt: Go1 Robot Variant 2
                          :width: 80%

                          **USD Path:** Unitree/Go1/go1_sensor.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 16
                                * - Number of Links
                                  - 17
                                * - Number of DOFs
                                  - 12

                            .. list-table::
                                :align: center
                                :widths: 40 40
                                :header-rows: 1

                                * - Sensor/Accessory
                                  - Count

                                * - Contact Sensor
                                  - 4

                            **Physics APIs:**

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: B2


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_B2_b2.usd.png
                  :align: center
                  :alt: B2 Robot
                  :width: 80%

                  **USD Path:** Unitree/B2/b2.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 30
                        * - Number of Links
                          - 31
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

            .. tab-item:: A1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Unitree_A1_a1.usd.png
                  :align: center
                  :alt: A1 Robot
                  :width: 80%

                  **USD Path:** Unitree/A1/a1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/unitreerobotics/unitree_ros>`__

        | **IsaacSim**

        .. tab-set::

            .. tab-item:: Ant


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Ant_ant.usd.png
                          :align: center
                          :alt: Ant Robot Variant 1
                          :width: 80%

                          **USD Path:** IsaacSim/Ant/ant.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 8
                                * - Number of Links
                                  - 9
                                * - Number of DOFs
                                  - 8

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `MIT <https://github.com/openai/gym/blob/master/LICENSE.md>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Ant_ant_colored.usd.png
                          :align: center
                          :alt: Ant Robot Variant 2
                          :width: 80%

                          **USD Path:** IsaacSim/Ant/ant_colored.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                            **License:** `MIT <https://github.com/openai/gym/blob/master/LICENSE.md>`__   

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Ant_ant_instanceable.usd.png
                          :align: center
                          :alt: Ant Robot Variant 3
                          :width: 80%

                          **USD Path:** IsaacSim/Ant/ant_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 8
                                * - Number of Links
                                  - 9
                                * - Number of DOFs
                                  - 8

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            * This robot is in Isaac Lab

                            **License:** `MIT <https://github.com/openai/gym/blob/master/LICENSE.md>`__  

        | **BostonDynamics**

        .. tab-set::

            .. tab-item:: spot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_BostonDynamics_spot_spot.usd.png
                  :align: center
                  :alt: spot Robot
                  :width: 80%

                  **USD Path:** BostonDynamics/spot/spot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    * This robot is in Isaac Lab

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Boston Dynamics-Signed 3D Content Sharing.pdf>`

        | **ANYbotics**

        .. tab-set::

            .. tab-item:: anymal_d


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_ANYbotics_anymal_d_anymal_d.usd.png
                  :align: center
                  :alt: anymal_d Robot
                  :width: 80%

                  **USD Path:** ANYbotics/anymal_d/anymal_d.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/ANYbotics/anymal_d_simple_description/blob/master/LICENSE>`__  

            .. tab-item:: anymal_c


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_ANYbotics_anymal_c_anymal_c.usd.png
                  :align: center
                  :alt: anymal_c Robot
                  :width: 80%

                  **USD Path:** ANYbotics/anymal_c/anymal_c.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 17
                        * - Number of Links
                          - 18
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/ANYbotics/anymal_c_simple_description/blob/master/LICENSE>`__  

            .. tab-item:: anymal_b


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_ANYbotics_anymal_b_anymal_b.usd.png
                  :align: center
                  :alt: anymal_b Robot
                  :width: 80%

                  **USD Path:** ANYbotics/anymal_b/anymal_b.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

                    **License:** `BSD-3 <https://github.com/ANYbotics/anymal_b_simple_description/blob/master/LICENSE>`__ 

        | **DeepRobotics**

        .. tab-set::

            .. tab-item:: X30


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_DeepRobotics_X30_X30.usd.png
                  :align: center
                  :alt: X30 Robot
                  :width: 80%

                  **USD Path:** DeepRobotics/X30/X30.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/DeepRoboticsLab/deep_robotics_model/blob/main/LICENSE.txt>`__

            .. tab-item:: M20


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_DeepRobotics_M20_M20.usd.png
                  :align: center
                  :alt: M20 Robot
                  :width: 80%

                  **USD Path:** DeepRobotics/M20/M20.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 16

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/DeepRoboticsLab/deep_robotics_model/blob/main/LICENSE.txt>`__

            .. tab-item:: Lite3


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_DeepRobotics_Lite3_Lite3.usd.png
                  :align: center
                  :alt: Lite3 Robot
                  :width: 80%

                  **USD Path:** DeepRobotics/Lite3/Lite3.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 16
                        * - Number of Links
                          - 17
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/DeepRoboticsLab/deep_robotics_model/blob/main/LICENSE.txt>`__

    .. tab-item:: Holonomic


        | **NVIDIA**

        .. tab-set::

            .. tab-item:: Kaya


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Kaya_kaya.usd.png
                          :align: center
                          :alt: Kaya Robot Variant 1
                          :width: 80%

                          **USD Path:** NVIDIA/Kaya/kaya.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 33
                                * - Number of Links
                                  - 34
                                * - Number of DOFs
                                  - 33

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            **License:** NVIDIA

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NVIDIA_Kaya_kaya_ogn_gamepad.usd.png
                          :align: center
                          :alt: Kaya Robot Variant 2
                          :width: 80%

                          **USD Path:** NVIDIA/Kaya/kaya_ogn_gamepad.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            **Physics APIs:**

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            **License:** NVIDIA

        | **Fraunhofer**

        .. tab-set::

            .. tab-item:: O3dyn


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Fraunhofer_O3dyn_o3dyn.usd.png
                          :align: center
                          :alt: O3dyn Robot Variant 1
                          :width: 80%

                          **USD Path:** Fraunhofer/O3dyn/o3dyn.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 76
                                * - Number of Links
                                  - 77
                                * - Number of DOFs
                                  - 64

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/CLA-1_OpenLogisticsFoundation_Fraunhofer_-_NVIDIA.pdf>`

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Fraunhofer_O3dyn_o3dyn_controller.usd.png
                          :align: center
                          :alt: O3dyn Robot Variant 2
                          :width: 80%

                          **USD Path:** Fraunhofer/O3dyn/o3dyn_controller.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - N/A
                                * - Number of Links
                                  - N/A
                                * - Number of DOFs
                                  - N/A

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX CollisionAPI

                            - PhysX JointAPI

                            - PhysX ArticulationAPI

                            - PhysX SceneAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/CLA-1_OpenLogisticsFoundation_Fraunhofer_-_NVIDIA.pdf>`

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Fraunhofer_O3dyn_o3dyn_trimmed.usd.png
                          :align: center
                          :alt: O3dyn Robot Variant 3
                          :width: 80%

                          **USD Path:** Fraunhofer/O3dyn/o3dyn_trimmed.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 52
                                * - Number of Links
                                  - 53
                                * - Number of DOFs
                                  - 40

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            - PhysX CollisionAPI

                            - PhysX SceneAPI

                            **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/CLA-1_OpenLogisticsFoundation_Fraunhofer_-_NVIDIA.pdf>`

    .. tab-item:: Aerial


        | **NASA**

        .. tab-set::

            .. tab-item:: Ingenuity


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_NASA_Ingenuity_ingenuity.usd.png
                  :align: center
                  :alt: Ingenuity Robot
                  :width: 80%

                  **USD Path:** NASA/Ingenuity/ingenuity.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 4
                        * - Number of Links
                          - 5
                        * - Number of DOFs
                          - 4

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX CollisionAPI

                    **License:** `NASA/JPL-Caltech 3D Model Download <https://science.nasa.gov/resource/mars-ingenuity-helicopter-3d-model>`__

        | **IsaacSim**

        .. tab-set::

            .. tab-item:: Quadcopter


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Quadcopter_quadcopter.usd.png
                  :align: center
                  :alt: Quadcopter Robot
                  :width: 80%

                  **USD Path:** IsaacSim/Quadcopter/quadcopter.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 8
                        * - Number of Links
                          - 9
                        * - Number of DOFs
                          - 8

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

        | **Bitcraze**

        .. tab-set::

            .. tab-item:: Crazyflie


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Bitcraze_Crazyflie_cf2x.usd.png
                  :align: center
                  :alt: Crazyflie Robot
                  :width: 80%

                  **USD Path:** Bitcraze/Crazyflie/cf2x.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 4
                        * - Number of Links
                          - 5
                        * - Number of DOFs
                          - 4

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    * This robot is in Isaac Lab

                    **License:** `MIT <https://github.com/bitcraze/crazyflie-simulation/blob/main/LICENSE>`__  

        | **NTNU**

        .. tab-set::

            .. tab-item:: ARL-Robot-1


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_6.0_full_ref_viewport_Isaac_Robots_NTNU_ARL_Robot_1_arl_robot_1.usd.png
                  :align: center
                  :alt: ARL-Robot-1 Robot
                  :width: 80%

                  **USD Path:** NTNU/ARL-Robot-1/arl_robot_1.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 4
                        * - Number of Links
                          - 5
                        * - Number of DOFs
                          - 4

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/ntnu-arl/robot_model>`__

    .. tab-item:: Isaac Sim Simple


        | **IsaacSim**

        .. tab-set::

            .. tab-item:: Vehicle


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Vehicle_basic_vehicle_m.usd.png
                  :align: center
                  :alt: Vehicle Robot
                  :width: 80%

                  **USD Path:** IsaacSim/Vehicle/basic_vehicle_m.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - N/A
                        * - Number of Links
                          - N/A
                        * - Number of DOFs
                          - N/A

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX CollisionAPI

                    - PhysX SceneAPI

                    **License:** NVIDIA

            .. tab-item:: SimpleArticulation


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_SimpleArticulation_articulation_3_joints.usd.png
                          :align: center
                          :alt: SimpleArticulation Robot Variant 1
                          :width: 80%

                          **USD Path:** IsaacSim/SimpleArticulation/articulation_3_joints.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 3
                                * - Number of Links
                                  - 4
                                * - Number of DOFs
                                  - 3

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_SimpleArticulation_revolute_articulation.usd.png
                          :align: center
                          :alt: SimpleArticulation Robot Variant 2
                          :width: 80%

                          **USD Path:** IsaacSim/SimpleArticulation/revolute_articulation.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 1
                                * - Number of Links
                                  - 2
                                * - Number of DOFs
                                  - 1

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

                    .. tab-item:: Variant 3

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_SimpleArticulation_simple_articulation.usd.png
                          :align: center
                          :alt: SimpleArticulation Robot Variant 3
                          :width: 80%

                          **USD Path:** IsaacSim/SimpleArticulation/simple_articulation.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 2
                                * - Number of Links
                                  - 3
                                * - Number of DOFs
                                  - 2

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX SceneAPI

                            - PhysX CollisionAPI

            .. tab-item:: Humanoid28


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Humanoid28_humanoid_28.usd.png
                  :align: center
                  :alt: Humanoid28 Robot
                  :width: 80%

                  **USD Path:** IsaacSim/Humanoid28/humanoid_28.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 14
                        * - Number of Links
                          - 15
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

            .. tab-item:: Humanoid


                .. tab-set::

                    .. tab-item:: Variant 1

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Humanoid_humanoid.usd.png
                          :align: center
                          :alt: Humanoid Robot Variant 1
                          :width: 80%

                          **USD Path:** IsaacSim/Humanoid/humanoid.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 15
                                * - Number of Links
                                  - 16
                                * - Number of DOFs
                                  - 12

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            **License:** `MIT <https://github.com/openai/gym/blob/master/LICENSE.md>`__  

                    .. tab-item:: Variant 2

                        .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Humanoid_humanoid_instanceable.usd.png
                          :align: center
                          :alt: Humanoid Robot Variant 2
                          :width: 80%

                          **USD Path:** IsaacSim/Humanoid/humanoid_instanceable.usd

                        .. dropdown:: Properties
                            :animate: fade-in
                            :color: light

                            .. list-table::
                                :align: center
                                :widths: 40 40

                                * - Number of Joints
                                  - 15
                                * - Number of Links
                                  - 16
                                * - Number of DOFs
                                  - 12

                            **Physics APIs:**

                            - PhysX RigidBodyAPI

                            - PhysX ArticulationAPI

                            - PhysX JointAPI

                            * This robot is in Isaac Lab

                            **License:** `MIT <https://github.com/openai/gym/blob/master/LICENSE.md>`__ 

            .. tab-item:: DifferentialBase


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_DifferentialBase_differential_base.usd.png
                  :align: center
                  :alt: DifferentialBase Robot
                  :width: 80%

                  **USD Path:** IsaacSim/DifferentialBase/differential_base.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX SceneAPI

                    - PhysX JointAPI

            .. tab-item:: Cartpole


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_Cartpole_cartpole.usd.png
                  :align: center
                  :alt: Cartpole Robot
                  :width: 80%

                  **USD Path:** IsaacSim/Cartpole/cartpole.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 2
                        * - Number of Links
                          - 3
                        * - Number of DOFs
                          - 2

                    **Physics APIs:**

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

            .. tab-item:: CartDoublePendulum


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_CartDoublePendulum_cart_double_pendulum.usd.png
                  :align: center
                  :alt: CartDoublePendulum Robot
                  :width: 80%

                  **USD Path:** IsaacSim/CartDoublePendulum/cart_double_pendulum.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 3
                        * - Number of Links
                          - 4
                        * - Number of DOFs
                          - 3

                    **Physics APIs:**

                    - PhysX JointAPI

                    - PhysX ArticulationAPI

            .. tab-item:: BalanceBot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_IsaacSim_BalanceBot_balance_bot.usd.png
                  :align: center
                  :alt: BalanceBot Robot
                  :width: 80%

                  **USD Path:** IsaacSim/BalanceBot/balance_bot.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 6
                        * - Number of Links
                          - 7
                        * - Number of DOFs
                          - 6

                    **Physics APIs:**

                    - PhysX RigidBodyAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

    .. tab-item:: Mobile Manipulator


        | **Clearpath**

        .. tab-set::

            .. tab-item:: RidgebackUr


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_RidgebackUr_ridgeback_ur5.usd.png
                  :align: center
                  :alt: RidgebackUr Robot
                  :width: 80%

                  **USD Path:** Clearpath/RidgebackUr/ridgeback_ur5.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 9
                        * - Number of Links
                          - 10
                        * - Number of DOFs
                          - 9

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** `BSD-3 <https://github.com/orgs/clearpathrobotics/repositories?q=dingo>`__

            .. tab-item:: RidgebackFranka


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_Clearpath_RidgebackFranka_ridgeback_franka.usd.png
                  :align: center
                  :alt: RidgebackFranka Robot
                  :width: 80%

                  **USD Path:** Clearpath/RidgebackFranka/ridgeback_franka.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 18
                        * - Number of Links
                          - 19
                        * - Number of DOFs
                          - 12

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    * This robot is in Isaac Lab

                    **License:** `BSD-3 <https://github.com/orgs/clearpathrobotics/repositories?q=dingo>`__

        | **BostonDynamics**

        .. tab-set::

            .. tab-item:: spot


                .. figure:: /images/usd_assets_robots/robot_assets_docs_thumbnails/isim_5.1_full_ref_viewport_Isaac_Robots_BostonDynamics_spot_spot_with_arm.usd.png
                  :align: center
                  :alt: spot Robot
                  :width: 80%

                  **USD Path:** BostonDynamics/spot/spot_with_arm.usd

                .. dropdown:: Properties
                    :animate: fade-in
                    :color: light

                    .. list-table::
                        :align: center
                        :widths: 40 40

                        * - Number of Joints
                          - 19
                        * - Number of Links
                          - 20
                        * - Number of DOFs
                          - 19

                    **Physics APIs:**

                    - PhysX SceneAPI

                    - PhysX ArticulationAPI

                    - PhysX JointAPI

                    **License:** :download:`3D Content Sharing Agreement <robot_asset_licenses/Boston Dynamics-Signed 3D Content Sharing.pdf>`
