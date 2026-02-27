..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_cortex_7_cortex_extensions:

==================================
Building Cortex Based Extensions
==================================



This tutorial covers the use of Cortex in a custom extension running directly on Isaac Sim App instead of the Python SimulationApp. For this we use the same behaviors from :ref:`isaac_sim_app_tutorial_cortex_4_franka_block_stacking` and :ref:`isaac_sim_app_tutorial_cortex_5_ur10_bin_stacking`. To use Cortex, similar to :ref:`isaac_sim_app_tutorial_core_hello_robot`, but we create a modified version of the Base Sample that replaces the Core World with a Cortex World:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_7_cortex_extension/building_cortex_based_extensions.py
    :language: python

Now, we need to define the world Task, to define how the world behaves, and the Robot Cortex task. That code is equivalent to the standalone examples, except that the functions to step, start and reset the simulation are moved on the callbacks for the task step, and reset callbacks.

Franka Cortex Examples
----------------------


The UI is defined in the ``exts/isaacsim.examples.interactive/isaacsim/examples/interactive/franka_cortex/franka_cortex_extension.py``, This sample shows how to load many different decider networks for Franka. 

First activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.
To load the sample navigate to `Robotics Examples` > `Cortex` > `Franka Cortex Examples`.

First, select the behavior you want from the drop-down, then click on `LOAD`. To begin the decider network, click on `START`.

.. image:: /images/isaac_cortex_franka_extension.png
    :align: center    
    :alt: Franka Cortex Examples.

On the Diagnostic monitor, you can check the decision stack. Due to the different nature of the tasks, the task diagnostics is showed as a diagnostic message, containing the important information for each task.

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
    the **RESET** button instead.

Hot-Swapping Behaviors
^^^^^^^^^^^^^^^^^^^^^^

Cortex allows you to select different behavior policies to run on your robot. In this example you can select which policy is running on the robot, even while it's executing the previous policy. It will change the behavior to conform to the new policy. To do so, choose a new behavior in the drop-down.



UR10 Palletizing Example
------------------------

The UI is defined in the ``exts/isaacsim.examples.interactive/isaacsim/examples/interactive/ur10_palletizing/ur10_palletizing_extension.py``.

To load the sample navigate to `Robotics Examples` > `Cortex` > `UR10 Palletizing`.

Click on `LOAD` to load all the assets and setup the scene. Then, Click on `START PALLETIZING` to begin the task.

On the Diagnostics section, you can inspect the Cortex Decision stack for the robot, and the flags used by the decision network to move forward to the next steps. 


.. image:: /images/isaac_cortex_palletizing_extension.png
    :align: center    
    :alt: Isaac UR10 Palletizing.

