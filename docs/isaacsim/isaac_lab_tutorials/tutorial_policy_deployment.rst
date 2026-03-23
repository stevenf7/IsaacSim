..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_policy_deployment:

===============================
Deploying Policies in Isaac Sim
===============================


The objective of this tutorial is to explain the process of deploying a policy trained in Isaac Lab by going through an example and exploring robot definition files.

There are many use cases in which you might want to deploy your policy in Isaac Sim; such as enabling robots to accomplish more complex locomotion, testing and integrating the policy with other stacks such as navigation and localization in simulated environments, and interfacing it using with existing bridges such as ROS 2.

Learning Objectives
===================

In this tutorial, you will walk through the policy based robot examples:

1. H1 and Spot flat terrain policy controller demo
2. Training and exporting policies in Isaac Lab
3. Reading the environment parameter file from Isaac Lab
4. Robot definition class
5. Position to torque conversion
6. Debugging tips
7. Sim to Real deployment

Demos
======

First activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.

Unitree H1 Humanoid Example
------------------------------
1. The Unitree H1 humanoid example can be accessed by creating a empty stage.
2. Open the example using **Robotics Examples** > **POLICY** > **Humanoid**.
3. Press **LOAD** to open the scene.

This example uses the H1 Flat Terrain Policy trained in Isaac Lab to control the humanoid's locomotion.

.. image:: /images/tutorial_lab_h1_walk_demo.gif
    :align: center
    :width: 80%

Controls:

- Forward: UP ARROW / NUM 8
- Turn Left: LEFT ARROW / NUM 4
- Turn Right: RIGHT ARROW / NUM 6

Boston Dynamics Spot Quadruped Example
----------------------------------------------

1. The Boston Dynamics Spot quadruped example can be accessed by creating a empty stage.
2. Open the example using **Robotics Examples** > **POLICY** > **Quadruped**.
3. Press **LOAD** to open the scene.

This example uses the Spot Flat Terrain Policy trained in Isaac Lab to control the quadruped's locomotion.

.. image:: /images/tutorial_lab_spot_walk_demo.gif
    :align: center
    :width: 80%

Controls:

- Forward: UP ARROW / NUM 8
- Backward: BACK ARROW / NUM 2
- Move Left: LEFT ARROW / NUM 4
- Move Right: RIGHT ARROW / NUM 6

- Turn Left: N / NUM 7
- Turn Right: M / NUM 9


.. Note:: See :ref:`isaac sim policy example extension document <isaac_sim_policy_example>` for standalone example workflow and the policy files used in the examples.

Training and Exporting Policies in Isaac Lab
==================================================

Training
---------------

Training the policy from Isaac Lab is the first step to deploying the policy.
Consult the `Isaac Lab tutorials <https://isaac-sim.github.io/IsaacLab/main/source/tutorials/03_envs/run_rl_training.html>`_ for training an existing or custom policy.

The policies trained used in the examples above are `Isaac-Velocity-Flat-H1-v0` for the Unitree H1 humanoid and `Isaac-Velocity-Flat-Spot-v0` for the Boston Dynamics Spot robot.

.. Note:: For example, in Isaac Lab 2.0, use the following command to train the H1 flat terrain policy:

    .. code-block:: bash

        ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task Isaac-Velocity-Flat-H1-v0 --headless

Exporting
--------------

Policies trained using ``RSL_rl``, the policies can be exported using the ``scripts/reinforcement_learning/rsl_rl/play.py`` inside the Isaac Lab workspace. The exported files are generated in the ``exported`` folder.

It is also possible to inference using a policy trained in a different framework or with an iteration snapshot, however additional data such as neural network structure may be required.
Follow the documentation of your desired framework for more information.

.. Note:: For example, in Isaac Lab 2.0, use the following command to export the H1 flat terrain policy:

    .. code-block:: bash

        ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py --task Isaac-Velocity-Flat-H1-v0 --num_envs 32

.. Note:: The trained policy files used in the examples are available to download :ref:`here <isaac_sim_policy_example_policies>`.

Understanding the Environment Parameter File
===================================================

The ``agent.yaml`` and ``env.yaml`` are generated with trained policies to describe the policy configurations and they are located in the ``logs/rsl_rl/<task_name>/<time>/params/`` folder.

- ``agent.yaml`` describes the neural network parameters.
- ``env.yaml`` describes the environment and robot configurations.

The below snippets are taken from `Isaac-Velocity-Flat-H1-v0`.

Simulation Setup
----------------------

.. code-block:: bash

    sim:
    physics_prim_path: /physicsScene
    dt: 0.005
    render_interval: 4
    gravity: !!python/tuple
    - 0.0
    - 0.0
    - -9.81
    enable_scene_query_support: false
    use_fabric: true
    disable_contact_processing: true
    use_gpu_pipeline: true
    device: cuda:0

The first snippet describes the simulation environment, the simulation physics is required to run at 0.005s (200hz), with gravity pointing downwards at 9.81m/s^2

Robot Setup
-------------------

The ``scene:robot:init_state`` section describes the robot's initial position, orientation, velocity, as well as default joint position and velocity.

.. code-block:: bash

    init_state:
      pos: !!python/tuple
      - 0.0
      - 0.0
      - 1.05
      rot: &id003 !!python/tuple
      - 1.0
      - 0.0
      - 0.0
      - 0.0
      lin_vel: &id001 !!python/tuple
      - 0.0
      - 0.0
      - 0.0
      ang_vel: *id001
      joint_pos:
        .*_hip_yaw: 0.0
        .*_hip_roll: 0.0
        .*_hip_pitch: -0.28
        .*_knee: 0.79
        .*_ankle: -0.52
        torso: 0.0
        .*_shoulder_pitch: 0.28
        .*_shoulder_roll: 0.0
        .*_shoulder_yaw: 0.0
        .*_elbow: 0.52
      joint_vel:
        .*: 0.0

The ``scene:robot:init_state:actuators`` section below describes the robot joint properties such as effort and velocity limit, stiffness and dampening.

.. code-block:: bash

    actuators:
      legs:
        class_type: omni.isaac.lab.actuators.actuator_pd:ImplicitActuator
        joint_names_expr:
        - .*_hip_yaw
        - .*_hip_roll
        - .*_hip_pitch
        - .*_knee
        - torso
        effort_limit: 300
        velocity_limit: 100.0
        stiffness:
          .*_hip_yaw: 150.0
          .*_hip_roll: 150.0
          .*_hip_pitch: 200.0
          .*_knee: 200.0
          torso: 200.0
        damping:
          .*_hip_yaw: 5.0
          .*_hip_roll: 5.0
          .*_hip_pitch: 5.0
          .*_knee: 5.0
          torso: 5.0
        armature: null
        friction: null


Observations Parameters
-------------------------

The observation parameters describes the observations required by the policy, as well as scale or clipping factors that need to be applied to the observation.

.. code-block:: bash

    observations:
        policy:
            concatenate_terms: true
            enable_corruption: true
            base_lin_vel:
            func: omni.isaac.lab.envs.mdp.observations:base_lin_vel
            params: {}
            noise:
                func: omni.isaac.lab.utils.noise.noise_model:uniform_noise
                operation: add
                n_min: -0.1
                n_max: 0.1
            clip: null
            scale: null

Actions Parameters
--------------------------

The actions parameters describes the action outputted by the policy, as well as scaling factors and offsets that need to be applied to the actions.

.. code-block:: bash

    actions:
        joint_pos:
            class_type: omni.isaac.lab.envs.mdp.actions.joint_actions:JointPositionAction
            asset_name: robot
            debug_vis: false
            joint_names:
            - .*
            scale: 0.5
            offset: 0.0
            use_default_offset: true


Commands Parameters
-----------------------

Finally, the command section describers the type of command for the policy, as well as acceptable command ranges for the policy.

.. code-block:: bash

    commands:
        base_velocity:
            class_type: omni.isaac.lab.envs.mdp.commands.velocity_command:UniformVelocityCommand
            resampling_time_range: !!python/tuple
            - 10.0
            - 10.0
            debug_vis: true
            asset_name: robot
            heading_command: true
            heading_control_stiffness: 0.5
            rel_standing_envs: 0.02
            rel_heading_envs: 1.0
            ranges:
                lin_vel_x: !!python/tuple
                - 0.0
                - 1.0
                lin_vel_y: *id006
                ang_vel_z: !!python/tuple
                - -1.0
                - 1.0
                heading: !!python/tuple
                - -3.141592653589793
                - 3.141592653589793

.. _isaac_sim_policy_controller_class:

Policy Controller Class
===========================

The robot definition class defines the robot prim, imports the robot policy, sets up the robot configurations, builds the observation tensor, and finally applies the policy control action to the robot.

Constructor
-------------

The Constructor will spawn the robot USD, and create a single articulation object for controlling the robot.

Load Policy
-------------

This class will load in the policy file and the corresponding environment file which the policy controller will use to set up the Isaac Sim environment.

Initialize
--------------------

The initialize function must be called once after simulation started. The purpose of this function is to match the robot configurations to the policy, by setting the robot effort mode, control mode, joint gains, joint max effort, joint max velocity, and articulation root.

``_set_articulation_prop``
---------------------------

This function parses the articulation root property and set these properties to the robot.

``_compute_action``
--------------------

This function will compute the action from the observation.


``_compute_observation``
------------------------

This function must be overload by the inherited class and it is called by ``advance()`` during every physics step. The purpose of this function is to create an observation tensor in the format expected by the policy.
For example, the code snippet below creates the observation tensor for the H1 flat terrain policy.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/compute_observation.py
    :language: python

.. note:: Remember to multiply the observation terms by the observation scale specified in the ``env.yaml``.

Forward
----------

This function must be overload by the inherited class and is called every physics step to generate control action for the robot.
For example, the code snippet below creates the controls for the H1 flat terrain policy.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/forward.py
    :language: python

.. note::
 - The policy does not need to be called every step, refer to the decimation parameter in ``env.yaml``.
 - Remember to multiply the action output by the action scale specified in ``env.yaml``.

.. warning:: For position based controls, do not use ``set_joint_position()`` as that will teleport the joint to the desired position.

Position to Torque Controls
==============================

Some robots may require torque control as output. If the policy generates position as an output, then you must convert position to torque. There are many ways to do this, here an actuator network is used to convert position to torque.

The actuator network class is defined in ``source/extensions/isaacsim.robot.policy.examples/isaacsim/robot/policy/examples/utils/actuator_network.py``.
The actuator network policy for the Anymal robot is stored on the Content Browser at *SAMPLES* > *POLICY* > *ANYMAL_POLICIES*

Import Policy
---------------

For our LSTMSeaNetwork implementation, the policy file is loaded into the helper actuator network using the snippet below from the Anymal Flat Terrain Policy class:

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/import_policy.py
    :language: python

Run the Actuator Network
---------------------------

In the advance function, insert the position outputs from the locomotion policy into the actuator network and apply the torque to the robot using the snippet below:

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/run_the_actuator_network.py
    :language: python

Debugging Tips
=======================

If your robot doesn't work right away, you can use the following tips to start debugging:

Verify Your Policy
---------------------

You can start by verifying that your policy is working properly by `playing it in Isaac Lab. <https://isaac-sim.github.io/IsaacLab/main/source/tutorials/03_envs/run_rl_training.html#playing-the-trained-agent>`_

Remember to use the correct ``play.py`` for your workflow and select the correct task.

Verify the Robot Joint Properties
---------------------------------

Robot Joint Order
########################

If the policy is working on Isaac Lab, then you should verify is the joint order of the robot, joint properties, and default joint positions.

To see the joint order, open your asset USD, create an articulation with the robot prim, start the simulation, initialize articulation, and call the ``dof_names`` function.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/robot_joint_order.py
    :language: python
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

Print out the ``dof_names`` for both the Isaac Sim asset and the asset you used to train in Isaac Lab, make sure that the names and orders match exactly.

The ANYmal robot below has control commands in the wrong order, as a result the robot is falling over.

.. image:: /images/tutorial_lab_anymal_joint_error.gif
    :align: center
    :width: 80%


Default Joint Position
#######################

After you have the joint positions, verify that your default joint positions are inserted correctly. If the joint positions are incorrect, the robot joints will not go to the correct position.


For example, in the video below, the ankle joint was set incorrectly and the H1 humanoid was tip toeing, doing a "moonwalk".

.. image:: /images/tutorial_lab_h1_moonwalk.gif
    :align: center
    :width: 80%

Robot Joint Properties
########################

If you observe the joints are moving too much or not enough, then the joint properties may not be set up correctly.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_policy_deployment/robot_joint_properties.py
    :language: python
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

Then, you can compare the joint properties with the env YAML file generated by Isaac Lab. Check the articulation API documentation for  the properties for the DOFs.

For example, in the video below, the spot robot's stiffness and dampening are set too high, resulting in underactuated movement.

.. image:: /images/tutorial_lab_spot_wrong_gains.gif
    :align: center
    :width: 80%

For example, in the video below, the H1 robot's arm stiffness and dampening are set too low, resulting in over movement.

.. image:: /images/tutorial_lab_h1_arm_shake.gif
    :align: center
    :width: 80%


Verify the Simulation Environment
-----------------------------------

If the robot matches exactly and the inference examples are still not working, then it's time to check the simulation parameters.

Physics Scene
###################

Physics scene describes the time stepping with ``Time Steps Per Second (Hz)``, so take the inverse of the ``dt`` parameter in the ``env.yaml`` and set this correctly.
Also match the physics scene properties with the physx section of the ``env.yaml`` file.

For example, in the video below, time step was set to 60Hz, instead of the 500Hz expected by the controller.

.. image:: /images/tutorial_lab_spot_wrong_timestep.gif
    :align: center
    :width: 80%

Verify the Observation and Action Tensor
-------------------------------------------

Finally, verify the observation and action tensors, and make sure your tensor structures are correct, the data passed in to the tensors are correct, and the correct scale factors are applied to the input and outputs.

Also, make sure the actions output from the policy matches the expected type of inputs of articulation and are in the correct order to correctly power the robot.


Sim To Real Deployment
=============================

Congratulations, your robot and policy are working correctly in Isaac Sim now and you have tested it with the rest of your stack. Now it's time to deploy it on a real robot.

Please read this `article <https://developer.nvidia.com/blog/closing-the-sim-to-real-gap-training-spot-quadruped-locomotion-with-nvidia-isaac-lab/>`_ on deploying an reinforcement learning policy to a spot robot.