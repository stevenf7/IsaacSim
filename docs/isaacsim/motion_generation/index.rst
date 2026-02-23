
=====================
Motion Generation API
=====================

The Motion Generation API provides a unified framework for real-time motion generation in |isaac-sim_short|. 
The framework includes a flexible, composable system for controlling robots, supporting both simple single-controller setups 
and complex multi-controller architectures. Additionally, the API provides tools for querying, configuring, and synchronizing 
collision objects from the USD scene to the internal world representations used by motion planning software.

This page provides a high-level overview of the components that make up the Motion Generation API. Detailed tutorials for each component are linked at the end of this page.

What is Motion Generation?
--------------------------

Motion generation is the process of computing desired robot states over time. In |isaac-sim_short|, this occurs in real-time during simulation. 
The Motion Generation API provides a flexible foundation for building motion generation systems, from simple single-controller setups to complex multi-controller architectures.

The API enables bidirectional integration between |isaac-sim_short| and motion planning software:

* **Reading Simulation Data** - Efficiently extract obstacle data from the simulation for motion planning
* **Writing Motion** - Provide a uniform interface for motion planning software to express motion to the simulation

Reading Simulation Data
-----------------------

The API provides tools for efficiently querying the USD scene and moving data from simulation to motion planning software. 
These tools enable motion planning algorithms to access collision geometries, robot information, and scene data without 
constraining how the planning software works internally.

Key components:

* :class:`SceneQuery` - Searches the scene for objects matching specific criteria, useful for finding the list of prims which should be added to the planning library's world model
* :class:`WorldInterface` - An adapter interface that translates obstacle data from |isaac-sim_short| format (warp arrays) into the planning library's format
* :class:`ObstacleStrategy` - Manages how obstacles geometries are approximated for planning, separating this representation from the approximation used in the physics engine
* :class:`WorldBinding` - A convenience class to extract all collision environment data from USD, and then initialize/synchronize the planning library's internal world model via :class:`WorldInterface`

The API is designed to be highly modular, but a typical workflow is broken into :

* obstacle discovery, configuration, and initialization
* obstacle synchronization

**Configuration Workflow** - Discovering, configuring, and initializing obstacles:

.. figure:: images/isim_6.0_full_tut_external_scene_interaction_configuration_workflow.svg
   :alt: Configuration workflow for scene interaction
   :align: center
   :width: 100%

   SceneQuery discovers objects in the USD scene, ObstacleStrategy configures how they should 
   be represented, and WorldBinding initializes the planning library's world model.

**Obstacle Synchronization** - Updating the planning library's world model:

.. figure:: images/isim_6.0_full_tut_external_scene_interaction_data_flow.svg
   :alt: Obstacle synchronization workflow
   :align: center
   :width: 90%

   WorldBinding extracts updated transforms and properties from USD, updating the WorldInterface.

Writing Motion
--------------

The API provides a uniform interface for different motion generation software to express motion to the simulation.

RobotState: Unified State Representation
##########################################

All controllers work with :class:`RobotState`, a unified representation of robot state that supports multiple control spaces:

* **Joint-space** - Control of individual joints
* **Site-space** - Control of specific points on the robot (like end effectors, or other meaningful points of reference on the robot)
* **Link-space** - Control of robot links
* **Root-space** - Control of the robot base

The :func:`combine_robot_states()` function enables different controllers to control different parts of the robot simultaneously, supporting sophisticated control strategies.

BaseController: The Interface
###############################

All motion generation in this API is based on the :class:`BaseController` interface. 
A controller is a component that takes the current robot state and produces a desired robot state for the next time step.

Every controller implements two key methods:

* :meth:`reset` - Initializes the controller to a safe starting state before the controller starts running
* :meth:`forward` - Computes the next desired robot state at every time step

Controllers can be simple (such as following a trajectory) or complex (combining multiple sub-controllers). All controllers share the 
same interface, enabling composition and integration.

Controller Composition
#######################

The API provides several convenient controller composition classes for building complex behaviors from simpler controllers:

* :class:`SequentialController` - Runs controllers sequentially, passing the output of one as input to the next
* :class:`ParallelController` - Runs multiple controllers simultaneously and combines their outputs, supporting independent control of different parts of the robot
* :class:`ControllerContainer` - Supports runtime controller switching for seamless integration with higher-level control systems, including state machines and behavior trees

These composition classes are themselves controllers, enabling nested hierarchies for complex control architectures.
Of course, these are just helper classes; it is also possible to compose controllers in any custom way that meets
the :class:`BaseController` interface.

Trajectories and Paths
######################

A :class:`Trajectory` represents a continuous-time path through robot state space. The Motion Generation API provides:

* :class:`Trajectory` - An interface for any time-indexable trajectory
* :class:`Path` - A class for representing discrete waypoints, with built-in conversion to a minimal-time trajectory
* :class:`TrajectoryFollower` - A :class:`BaseController` that executes any :class:`Trajectory`

Putting It All Together
-----------------------

The Motion Generation API is designed around a simple, bidirectional workflow that connects |isaac-sim_short| with your motion generation software:

.. figure:: images/isim_6.0_full_tut_external_motion_generation_api_overview.svg
   :alt: Motion Generation API overview showing bidirectional flow between Isaac Sim and motion generation software
   :align: center
   :width: 100%

   The API reads collision data from simulation (1), supports any motion generation algorithm (2), and provides a uniform interface to write motion commands back (3).

Next Steps
----------

For detailed information on each component, see the following sections:

Interfacing simulation data to motion generators
###################################################
.. toctree::
   :maxdepth: 2

   scene_interaction

Interfacing motion to the simulation
######################################
.. toctree::
   :maxdepth: 2

   mobile_robot_control_example
   trajectory_planning
