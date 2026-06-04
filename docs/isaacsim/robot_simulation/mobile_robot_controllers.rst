..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_mobile_robot_controllers:

==========================
Mobile Robot Controllers
==========================

.. note::
   For new controller development, consider using the newer experimental motion generation API in :doc:`Motion Generation (Experimental) <../motion_generation/index>`, which provides improved interfaces and additional features.

.. _isaac_sim_mobile_robot_controller_differential:

Differential controller
===============================

The differential controller uses the speed differential between the left and right wheels to control the robot's linear and angular velocity. The differential robot enables the robot to turn in place and is used in the NVIDIA Nova Carter robot.

.. figure:: /images/usd_assets_robots/isim_4.5_full_ref_viewport_Isaac_Robots_Carter_nova_carter.usd.png
    :align: center
    :alt: Nova Carter
    :width: 60%

The Math
----------------

.. math::

   \omega_R &= \frac{1}{2r}(2V + \omega l_{tw})

   \omega_L &= \frac{1}{2r}(2V - \omega l_{tw})


where :math:`\omega` is the desired angular velocity, :math:`V` is the desired linear velocity, :math:`r` is the radius of the wheels, and :math:`l_{tw}` is the distance between them.
:math:`\omega_R` is the desired right wheel angular velocity and :math:`\omega_L` is the desired left wheel angular velocity.

OmniGraph Node
----------------

.. list-table:: Differential Controller OmniGraph Inputs
   :widths: 30 70
   :header-rows: 1

   * - Input Commands
     - description
   * - execIn
     - Input execution
   * - wheelRadius
     - Radius of the wheels in meters
   * - wheelDistance
     - Distance between the wheels in meters
   * - dt
     - Delta time in seconds
   * - maxAcceleration
     - Max linear acceleration for moving forward and reverse in m/s^2, 0.0 means not set
   * - maxDeceleration
     - Max linear breaking of the robot in m/s^2, 0.0 means not set
   * - maxAngularAcceleration
     - Max angular acceleration of the robot in rad/s^2, 0.0 means not set
   * - maxLinearSpeed
     - Max linear speed allowed for the robot in m/s, 0.0 means not set
   * - maxAngularSpeed
     - Max angular speed allowed for the robot in rad/s, 0.0 means not set
   * - maxWheelSpeed
     - Max wheel speed in rad/s
   * - Desired Linear Velocity
     - Desired linear velocity in m/s
   * - Desired Angular Velocity
     - Desired angular velocity in rad/s

.. list-table:: Differential Controller OmniGraph Outputs
   :widths: 30 70
   :header-rows: 1

   * - Output Commands
     - description
   * - VelocityCommand
     - Velocity command for the left and right wheel in m/s and rad/s

.. note::
   ``VelocityCommand`` is ordered as ``[left_wheel_velocity, right_wheel_velocity]``. When wiring this output to an Articulation Controller, list the wheel joint names or indices in the same left-wheel, right-wheel order.


Python
----------------

The code snippet below setups the differential controller for a NVIDIA Jetbot with a wheel radius of 3 cm and a base of 11.25cm, with a linear speed of 0.3m/s and angular speed of 1.0rad/s. 

.. literalinclude:: ../snippets/robot_simulation/mobile_robot_controllers/differential_controller.py
    :language: python

.. _isaac_sim_mobile_robot_controller_holonomic:

Holonomic Controller
===============================

The holonomic controller computes the joint drive commands required on omni-directional robots to produce the commanded forward, lateral, and yaw speeds of the robot. An example of a holonomic robot is the NVIDIA Kaya robot.
The problem is framed as a quadratic program to minimize the residual "net force" acting on the center of mass.

.. figure:: /images/usd_assets_robots/isim_4.5_full_ref_viewport_Isaac_Robots_Kaya_kaya.usd.png
   :align: center
   :alt: Kaya
   :width: 60%


.. Note::

   The wheel joints of the robot prim must have additional attributes to definine the roller angles and radii of the mecanum wheels.

   .. literalinclude:: ../snippets/robot_simulation/mobile_robot_controllers/holonomic_robot_usd_setup.py
       :language: python
       :start-after: # -- End test setup --

   The :class:`HolonomicRobotUsdSetup` class automates this process.

The Math
----------------

The cost funciton is defined as the control input to the robot joints. By minimizing the control inputs, excess acceleration and be reduced.

.. math::

   J = min(X^T \cdot X)

The equality constrains are set by the linear and angular target velocity Inputs:

.. math::

   v_{input} &= V^T \cdot X 

   w_{input} &= (V \times D_{wheel dist to COM}) \cdot X 


OmniGraph Node
----------------

.. list-table:: Holonomic Controller OmniGraph Inputs
   :widths: 30 70
   :header-rows: 1

   * - Input Commands
     - description
   * - execIn
     - Input execution
   * - wheelRadius
     - Array of wheel radius in meters
   * - wheelPositions
     - Position of the wheel with respect to chassis' center of mass in meters
   * - wheelOrientations
     - Orientation of the wheel with respect to chassis' center of mass frame
   * - mecanumAngles
     - Angles of the mecanum wheels with respect to wheel's rotation axis in radians
   * - wheelAxis
     - The rotation axis of the wheels
   * - upAxis
     - The up axis (default to z axis)
   * - Velocity Commands for the vehicle
     - Velocity in x and y (m/s) and rotation (rad/s)
   * - maxLinearSpeed
     - Maximum speed allowed for the vehicle in m/s
   * - maxAngularSpeed
     - Maximum angular rotation speed allowed for the vehicles in rad/s
   * - maxWheelSpeed
     - Maximum rotation speed allowed for the wheel joints in rad/s
   * - linearGain
     - Gain for the linear velocity input
   * - angularGain
     - Gain for the angular input


.. list-table:: Holonomic Controller OmniGraph Outputs
   :widths: 30 70
   :header-rows: 1

   * - Output Commands
     - description
   * - jointVelocityCommand
     - Velocity command for the wheel joints in rad/s



Python
----------------

The code snippet below computes the joint velocity output for a three wheeled NVIDIA Kaya holonomic robot with command velocity of [1.0, 1.0, 0.1]

.. literalinclude:: ../snippets/robot_simulation/mobile_robot_controllers/holonomic_controller.py
    :language: python

.. _isaac_sim_mobile_robot_controller_ackermann:

Ackermann Controller
===============================

The Ackermann controller is commonly used for robots with steerable wheels, an example of steerable robot is the NVIDIA leatherback robot. 
The Ackermann controller in Isaac Sim assumes the desired steering angle and linear velocity are provided, and based on the robot geometry 

.. figure:: /images/usd_assets_robots/isim_4.5_full_ref_viewport_Isaac_Robots_Leatherback_leatherback.usd.png
   :align: center
   :alt: Leatherback
   :width: 60%


The Math
----------------

Compute the steering angle offset between the left and right steering wheels:

.. math::

   R_{icr} &= \frac{l_{wb}}{tan(\theta_{steer})} 

   \theta_L &= \arctan[\frac{l_{wb}}{R_{icr} - 0.5 * l_{tw}}]

   \theta_R &= \arctan[\frac{l_{wb}}{R_{icr} + 0.5 * l_{tw}}]
 
where :math:`R_{icr}` is the radius to the instantaneous center of rotation, :math:`\theta_{steer}` is the desired steering angle, :math:`l_{wb}` is the distance between rear and front axles (wheel base), :math:`l_{tw}` is the track width


Compute the individual wheel velocities (Forward steering case):

First step is to find the distance between the wheels and the instantaneous center of rotation.

.. math::

   D_{front}  &= \sqrt{ (R_{icr} \pm 0.5 l_{tw})^2 + (l_{wb})^2 }

   D_{rear} &= R_{icr} \pm 0.5 l_{tw}

.. Note:: for :math:`\pm`, use :math:`-` for the wheel closer to the :math:`R_{icr}` and :math:`+` for the wheel further to the :math:`R_{icr}`

Then desired wheel velocity can be computed

.. math::

   \omega_{front} &= \frac{V_{desired}}{R_{icr}} \cdot \frac{D_{front}}{r_{front}}

   \omega_{rear} &= \frac{V_{desired}}{R_{icr}} \cdot \frac{D_{rear}}{r_{rear}}

Where :math:`V_{desired}` is the desired linear velocity, :math:`r_{front}` is the desired front wheel radius, and  :math:`r_{rear}` is the desired rear wheel radius.


OmniGraph Node
----------------

.. list-table:: Ackermann Controller OmniGraph Inputs
   :widths: 30 70
   :header-rows: 1

   * - Input Commands
     - description
   * - execIn
     - Input execution
   * - acceleration
     - Desired forward acceleration for the robot in m/s^2
   * - speed
     - Desired forward speed in m/s
   * - steeringAngle
     - Desired steering angle in radians, by default it is positive for turning left for a front wheel drive
   * - currentLinearVelocity
     - Current linear velocity of the robot in m/s
   * - wheelBase
     - Distance between the front and rear axles of the robot in meters
   * - trackWidth
     - Distance between the left and right rear wheels of the robot in meters
   * - turningWheelRadius
     - Radius of the front wheels of the robot in meters
   * - maxWheelVelocity
     - Maximum angular velocity of the robot wheel in rad/s
   * - invertSteeringAngle
     - Flips the sign of the steering angle, Set to true for rear wheel steering
   * - useAcceleration
     - Use acceleration as an input, Set to false to use speed as input instead
   * - maxWheelRotation
     - Maximum angle of rotation for the front wheels in radians
   * - dt
     - Delta time for the simulation step

.. list-table:: Ackermann Controller OmniGraph Outputs
   :widths: 30 70
   :header-rows: 1

   * - Output Commands
     - description
   * - execOut
     - Output execution
   * - leftWheelAngle
     - Angle for the left turning wheel in radians
   * - rightWheelAngle
     - Angle for the right turning wheel in radians
   * - wheelRotationVelocity
     - Angular velocity for the turning wheels in rad/s



Python
----------------

The python snippet below creates an Ackermann controller for a NVIDIA Leatherback robot with a wheel base of 1.65m, track width of 1.25m, and wheel radius of 0.25m, sending it a desired forward velocity of 1.1 m/s and steering angle of 0.1 rad.

.. literalinclude:: ../snippets/robot_simulation/mobile_robot_controllers/ackemann_controller.py
    :language: python