..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaac_sim_policy_example:

=======================================================
Reinforcement Learning Policies Examples in Isaac Sim
=======================================================

.. _isaac_sim_policy_example_about:

About
======================

The isaac_sim_policy_example Extension is a framework and has a set of helper functions to deploy Isaac Lab Reinforcement Learning Policies in Isaac Sim.
For details for training and building the policy in Isaac Sim, visit :ref:`deploying policy in Isaac Sim <isaac_sim_app_tutorial_policy_deployment>`.

This Extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.robot.policy.example``.
To run examples below activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.


Unitree H1 Humanoid Example
------------------------------

1. The Unitree H1 humanoid example can be accessed by creating a empty stage.
2. Open the example menu using **Robotics Examples** > **POLICY** > **Humanoid**.
3. (Optional) Use the **Physics Engine** menu in the viewport to switch between PhysX and Newton before loading. The example automatically selects the matching policy for the active engine.
4. Press **LOAD** to open the scene.

This example uses an H1 Flat Terrain Policy trained in Isaac Lab to control the humanoid's locomotion. Both PhysX and Newton policies are provided so you can compare locomotion behavior across physics engines.

.. image:: /images/tutorial_lab_h1_walk_demo.gif
    :align: center
    :width: 100%

Controls:

- Forward: UP ARROW / NUM 8
- Turn Left: LEFT ARROW / NUM 4
- Turn Right: RIGHT ARROW / NUM 6

Boston Dynamics Spot Quadruped Example
----------------------------------------------

1. The Boston Dynamics Spot quadruped example can be accessed by creating a empty stage.
2. Open the example menu using **Robotics Examples** > **POLICY** > **Quadruped**.
3. (Optional) Use the **Physics Engine** menu in the viewport to switch between PhysX and Newton before loading. The example automatically selects the matching policy for the active engine.
4. Press **LOAD** to open the scene.

This example uses a Spot Flat Terrain Policy trained in Isaac Lab to control the quadruped's locomotion. Both PhysX and Newton policies are provided so you can compare locomotion behavior across physics engines.

.. image:: /images/tutorial_lab_spot_walk_demo.gif
    :align: center
    :width: 100%

Controls:

- Forward: UP ARROW / NUM 8
- Backward: BACK ARROW / NUM 2
- Move Left: LEFT ARROW / NUM 4
- Move Right: RIGHT ARROW / NUM 6

- Turn Left: N / NUM 7
- Turn Right: M / NUM 9

Unitree Go2 Quadruped Example
----------------------------------------------

1. The Unitree Go2 quadruped example can be accessed by creating a empty stage.
2. Open the example menu using **Robotics Examples** > **POLICY** > **Go2**.
3. (Optional) Use the **Physics Engine** menu in the viewport to switch between PhysX and Newton before loading. The example automatically selects the matching policy for the active engine.
4. Press **LOAD** to open the scene.

This example uses a Go2 Flat Terrain Policy trained in Isaac Lab to control the quadruped's locomotion. Both PhysX and Newton policies are provided so you can compare locomotion behavior across physics engines.

.. image:: /images/isim_6.0_full_ext-isaacsim.robot.policy.examples_go2_locomotion.webp
    :alt: Unitree Go2 quadruped following keyboard locomotion commands using the Go2 flat terrain policy.
    :align: center
    :width: 100%

Controls:

- Forward: UP ARROW / NUM 8
- Backward: BACK ARROW / NUM 2
- Move Left: LEFT ARROW / NUM 4
- Move Right: RIGHT ARROW / NUM 6

- Turn Left: N / NUM 7
- Turn Right: M / NUM 9

.. _isaac_sim_policy_example_policies:

Franka Panda Open Drawer Example
--------------------------------

1. The Franka Panda Open Drawer example can be accessed by creating a empty stage.
2. Open the example menu using **Robotics Examples** > **POLICY** > **Franka**.
3. Press **LOAD** to open the scene.

This example uses the Franka Open Drawer Policy trained in Isaac Lab to control the robot's arm.
The robot will open the drawer, hold it open until the would reset.

.. image:: /images/isim_5.0_full_ref_viewport_franka_open_drawer.webp
    :align: center
    :width: 100%

Policies Files
======================

The policies used in the examples are trained in Isaac Lab and are available here:

.. list-table::

    * - Name
      - Policy
      - Parameters

    * - H1 Flat Terrain Policy (PhysX)
      - `H1 Flat Terrain Policy (PhysX) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/h1/physx_policy.pt>`_
      - `H1 Flat Terrain Policy (PhysX) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/h1/physx_env.yaml>`_

    * - H1 Flat Terrain Policy (Newton)
      - `H1 Flat Terrain Policy (Newton) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/h1/newton_policy.pt>`_
      - `H1 Flat Terrain Policy (Newton) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/h1/newton_env.yaml>`_

    * - Spot Flat Terrain Policy (PhysX)
      - `Spot Flat Terrain Policy (PhysX) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Spot_Policies/spot_policy.pt>`_
      - `Spot Flat Terrain Policy (PhysX) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Spot_Policies/spot_env.yaml>`_

        `Spot Flat Terrain Policy Network Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Spot_Policies/agent.yaml>`_

    * - Spot Flat Terrain Policy (Newton)
      - `Spot Flat Terrain Policy (Newton) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Spot_Policies/newton_policy.pt>`_
      - `Spot Flat Terrain Policy (Newton) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Spot_Policies/newton_env.yaml>`_

    * - ANYmal C Flat Terrain Policy
      - `ANYmal C Flat Terrain Policy <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Anymal_Policies/anymal_policy.pt>`_

        `ANYmal C Actuator Network <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/IsaacLab/ActuatorNets/ANYbotics/anydrive_3_lstm_jit.pt>`_
      - `ANYmal C Flat Terrain Policy Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Anymal_Policies/anymal_env.yaml>`_

        `ANYmal C Flat Terrain Policy Network Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Anymal_Policies/agent.yaml>`_

    * - Franka Panda Open Drawer Policy
      - `Franka Panda Open Drawer Policy <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Franka_Policies/Open_Drawer_Policy/policy.pt>`_
      - `Franka Panda Open Drawer Policy Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/Franka_Policies/Open_Drawer_Policy/env.yaml>`_

    * - Go2 Flat Terrain Policy (PhysX)
      - `Go2 Flat Terrain Policy (PhysX) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/go2/physx_policy.pt>`_
      - `Go2 Flat Terrain Policy (PhysX) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/go2/physx_env.yaml>`_

    * - Go2 Flat Terrain Policy (Newton)
      - `Go2 Flat Terrain Policy (Newton) <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/go2/newton_policy.pt>`_
      - `Go2 Flat Terrain Policy (Newton) Environment Parameters <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/go2/newton_env.yaml>`_

.. Note:: The policies can also be downloaded directly from the Content Browser by right clicking the policy and selecting ``Download``.

API Documentation
====================

See the `API documentation <../py/source/extensions/isaacsim.robot.policy.examples/docs/index.html>`_ for complete usage information.

.. _isaac_sim_policy_example_tutorials:


Standalone Examples
======================

**h1_standalone.py**

- This standalone example demonstrates a Unitree H1 controlled by a flat terrain policy, following a set of predetermined command sequences.  It may be run via the following command:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.robot.policy.examples/h1_standalone.py --num-robots <number of robot> --env-url </path/to/environment>

    For example, this will spawn 5 robots on the flat grid scene below:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.robot.policy.examples/h1_standalone.py --num-robots 5 --env-url /Isaac/Environments/Grid/default_environment.usd

    .. image:: /images/isim_4.5_full_ref_viewport_humanoid_standalone.webp
        :align: center
        :width: 100%

**spot_standalone.py**

- This standalone example demonstrates a Boston Dynamics Spot controlled by a flat terrain policy, following a set of predetermined command sequences.  It may be run via the following command:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.robot.policy.examples/spot_standalone.py

    .. image:: /images/isim_4.5_full_ref_viewport_spot_standalone.webp
        :align: center
        :width: 100%

**anymal_standalone.py**

- This standalone example demonstrates an ANYmal C robot that is controlled by a neural network policy. The rough terrain policy was trained in Isaac Lab and takes as input the state of the robot, the commanded base velocity, and the surrounding terrain and outputs joint position targets. The example may be run via the following command:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.robot.policy.examples/anymal_standalone.py

    .. image:: /images/isim_4.5_full_ref_viewport_anymal_standalone.webp
        :align: center
        :width: 100%

Controls:

- Forward: UP ARROW / NUM 8
- Backward: BACK ARROW / NUM 2
- Move Left: LEFT ARROW / NUM 4
- Move Right: RIGHT ARROW / NUM 6
- Turn Left: N / NUM 7
- Turn Right: M / NUM 9


.. _isaac_sim_policy_example_api_doc:
