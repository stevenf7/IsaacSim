.. _isaac_sim_cumotion_tutorial_rmpflow:

============================
RMPflow Tutorial
============================

This tutorial demonstrates how to use the :class:`RmpFlowController` class in the |cumotion| integration to generate smooth, reactive motions that reach task-space targets while avoiding dynamic obstacles.

By the end of this tutorial, you'll understand:

* How to create and configure the :class:`RmpFlowController`
* How to update world state for dynamic environments

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` to understand how to load robot configurations.
- Review the :doc:`Controllers and the RobotState <../motion_generation/mobile_robot_control_example>` tutorial to understand the :class:`BaseController` interface and :class:`RobotState`.
- Review the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` to understand how to set up :class:`CumotionWorldInterface`.

To follow along with the tutorial, you can search and enable the **cuMotion Examples** extension within your running |isaac-sim_short| instance.
Within the ``isaacsim.robot_motion.cumotion.examples`` extension, there is a fully functional example of RMPflow including following a target, world awareness,
and obstacle avoidance.

Key Concepts
============

The :class:`RmpFlowController` implements the :class:`BaseController` interface from the :doc:`Motion Generation API <../motion_generation/index>`, enabling reactive motion control that:

* **Reaches task-space targets**: The controller drives the robot's end-effector to a target position and orientation
* **Avoids obstacles**: Uses the :class:`CumotionWorldInterface` to access obstacle information for collision avoidance

Setting Up the Controller
==========================

First, set up a :class:`CumotionWorldInterface` as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`. 
In this tutorial, we will use a :class:`WorldBinding` to conveniently initialize the obstacles in the :class:`CumotionWorldInterface`.
Once you have a :class:`CumotionWorldInterface`, you can create the controller:

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-setup-controller-snippet>
   :end-before: <end-setup-controller-snippet>
   :language: python

The controller needs:

* **Robot configuration**: A |cumotion| robot configuration (retrieved via :func:`load_cumotion_supported_robot`). See the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` for details on loading robot configurations.
* **World interface**: A :class:`CumotionWorldInterface` instance
* **Joint and site spaces**: The full ordered control spaces for the robot joints and sites (see the :doc:`Motion Generation API documentation <../motion_generation/mobile_robot_control_example>` for more details)
* **Tool frame**: The name of the end-effector frame to control - at initialization, the controller will confirm that the tool frame is in the site space

If the tool frame is not provided, the controller will use the first tool frame defined in the cumotion robot description.

Creating RobotState Objects
===========================

The controller requires :class:`RobotState` objects for the estimated state (current robot state) and setpoint state (target end-effector pose). For details on :class:`RobotState` creation, see the :doc:`Motion Generation API documentation <../motion_generation/mobile_robot_control_example>`.

**Estimated State** (current robot configuration):

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-get-estimated-state-snippet>
   :end-before: <end-get-estimated-state-snippet>
   :language: python

**Setpoint State** (target end-effector pose):

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-create-setpoint-state-snippet>
   :end-before: <end-create-setpoint-state-snippet>
   :language: python

Resetting the Controller
==========================

Before the controller can be used, it must be reset once with the estimated state, setpoint state, and clock time. The :meth:`reset` method:

* Clears any internal RMPflow setpoints on the tool frame
* Sets the joint-space setpoint equal to the current estimated joint pose of the robot (i.e., initial desired state is where the robot already is, which is the safest)
* Initializes the internal RMPflow algorithm

The :meth:`forward` method **cannot** run before :meth:`reset` is called successfully (it must return ``True``).

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-reset-controller-snippet>
   :end-before: <end-reset-controller-snippet>
   :language: python

Running the Controller
======================

The controller uses the :class:`BaseController` interface. In each update step, you need to:

1. Get the current robot state (estimated state)
2. Create a setpoint state with the target end-effector pose
3. Call the controller's :meth:`forward` method
4. Apply the resulting desired state to the robot

If the setpoint state is set to ``None``, then the controller continues to track the prior setpoint state.

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-run-controller-snippet>
   :end-before: <end-run-controller-snippet>
   :language: python


Updating World State
====================

The world binding must be updated each frame to track moving obstacles and robot base movements. This is critical for dynamic environments:

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-update-world-state-snippet>
   :end-before: <end-update-world-state-snippet>
   :language: python

For more details on world state synchronization, see the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`.

Accessing cuMotion Parameters
==============================

The controller provides access to the underlying |cumotion| RMPflow configuration for parameter modification:

.. literalinclude:: ../snippets/cumotion/rmpflow_example.py
   :start-after: <start-access-parameters-snippet>
   :end-before: <end-access-parameters-snippet>
   :language: python

For a complete list of available parameters and their usage, see the |cumotion| Python and C++ API documentation.

Example Usage
=============

.. note::
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the ``isaacsim.robot_motion.cumotion.examples`` extension at ``isaacsim/robot_motion/cumotion/examples/rmp_flow/scenario.py``.

The following videos show RMPflow as demonstrated in the ``isaacsim.robot_motion.cumotion.examples`` extension. 
Note that in these videos, the setting ``visualize_debug_prims`` is left at the default ``False``. Therefore,
there are no prims to visualize the internal cumotion World objects.

The first video shows RMPflow controlling the robot to reach a target while avoiding obstacles in the scene.

.. figure:: images/rmp_flow/isim_6.0_full_tut_viewport_rmp_flow_basic.webp
   :align: center
   :width: 100%

   RMPflow tracking a target while avoiding obstacles

The second video demonstrates adding a new obstacle to the scene, resetting the world state, and running RMPflow again. 
Objects are added in the same way as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`.
Inside the ``scenario.py`` file, a new ``CumotionWorldInterface`` is created every time the tutorial is reset. This is not generally necessary
if objects are not being added or removed from the scene.

.. figure:: images/rmp_flow/isim_6.0_full_tut_viewport_rmp_flow_add_obstacle.webp
   :align: center
   :width: 100%

   Adding an obstacle, resetting the cumotion world, and running RMPflow again

Summary
=======

This tutorial demonstrated:

1. **RmpFlowController Setup**: Creating the :class:`RmpFlowController` with a :class:`CumotionWorldInterface` for obstacle awareness
2. **RobotState Creation**: Properly creating :class:`RobotState` objects for the controller interface
3. **RmpFlowController Usage**: Using the :meth:`reset` and :meth:`forward` methods to compute desired motions that reach targets while avoiding obstacles
4. **World Updates**: Updating the world state each frame for dynamic environments
5. **Parameter Access**: Accessing underlying |cumotion| objects for advanced configuration

The :class:`RmpFlowController` provides reactive, obstacle-aware motion control that integrates seamlessly with the Motion Generation API.

Next Steps
----------

* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Sampling-based path planning
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Trajectory-based motion
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Optimization-based trajectory planning
* |cumotion| library documentation - Advanced parameter configuration

.. note::
   The :ref:`RMPflow Tuning Guide <isaac_sim_motion_generation_rmpflow_tuning_guide>` is still a valid documentation for tuning RMPflow in |cumotion|.
