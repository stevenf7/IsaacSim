..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_inspect_physics:


===============================
Simulation Data Visualizer
===============================

.. _isaac_inspect_physics_about:


The :ref:`isaac_inspect_physics` is used to visualize information for the selected prim. You can use this tool to better understand the behaviors of physics-enabled geometry during simulation.

If a non-physics prim is selected, position changes over the course of simulation are tracked. However, when a physics element is selected, it shows more physics properties, including position and velocities (linear, angular).

.. _isaac_inspect_physics_conventions:

Conventions
^^^^^^^^^^^^^^^^^^^^^^^^^^

The simulation data visualizer provides the following information:

- **Position**: in :ref:`isaac_sim_glossary_stage` `units [X, Y, Z]`
- **Rotation**: in `degrees [X, Y, Z]`
- **Linear Velocity**: in :ref:`isaac_sim_glossary_stage` `units/s`
- **Angular Velocity**: in `degrees/s`
- **Linear Acceleration**: in :ref:`isaac_sim_glossary_stage` `units/s^2`
- **Mass**: in :ref:`isaac_sim_glossary_stage` `mass unit`
- **Moment of Inertia**: in :ref:`isaac_sim_glossary_stage` `mass unit*`:ref:`isaac_sim_glossary_stage` `units^2`

For velocities, there's a fourth plot `M`, which is the magnitude of the vector.


.. _isaac_inspect_physics_user_tutorial:

Inspect Physics Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run this utility:

#. Open the Simulation Data Visualizer by going to the **Visibility Menu (eye icon on viewport) > Show by Type > Physics > Simulation Data Visualizer**.
#. Activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.
#. Load some simulation-ready example, such as the `Cortex Franka` example, by clicking **Robotics Examples > Cortex > Franka Cortex Examples**.
#. Press the **Load Robot** button.
#. Select the **/World/Franka/panda_hand** prim from the :ref:`isaac_sim_glossary_stage`.
#. Press the **START** button to begin simulating.

After simulation starts, the physics state of the selected rigid body updates in the **Inspect Physics** window.

.. figure:: /images/isaac_inspect_physics_ui_1.png
    :align: center
    :alt: Inspect Physics UI
