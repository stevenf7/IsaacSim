.. _isaac_sim_cumotion:

====================
cuMotion Integration
====================

This page provides a high-level overview of the |cumotion| integration to the |isaac-sim_short| :doc:`Motion Generation API <../motion_generation/index>`. 
Detailed tutorials for each component are linked at the end of this page.

What is cuMotion?
-----------------

|cumotion| is a high-performance, GPU-accelerated Motion Generation library for robotic manipulation. 
This integration provides access to |cumotion|'s planning and control algorithms within |isaac-sim_short|:

* **RMPflow**: Real-time, reactive motion policies for smooth, collision-free motions
* **Graph-Based Motion Planning**: Sampling-based algorithms (RRT variants) for global path planning
* **Trajectory Generation**: Time-optimal collision-unaware trajectory generation from waypoints or path specifications
* **Trajectory Optimization**: Collision-free and kinematically constrained global optimization-based trajectory planning (new to cuMotion, did not exist in Lula)

These algorithms make use of two main classes that manage the |cumotion| robot and world: 

* :class:`CumotionRobot` - encapsulates the robot description, kinematics, and configuration
* :class:`CumotionWorldInterface` - manages obstacles and world state for collision-aware planning

The |cumotion| integration follows a minimal wrapping philosophy, directly exposing |cumotion|'s powerful 
Python API while maintaining compatibility with |isaac-sim_short|'s Motion Generation interfaces. |cumotion|
is descended from the Lula library, though its integration into |isaac-sim_short| is substantially different.
It is recommended to complete the full cuMotion tutorials even if you are familiar with the previous Lula integration.

Key Architectural Principles
----------------------------

Centralized World State
#######################

All world state (obstacles, robot base transforms) is managed by a single :class:`CumotionWorldInterface` instance that is shared 
across all algorithms. This ensures consistency and simplifies obstacle management. The :class:`CumotionWorldInterface` meets 
the :class:`WorldInterface` defined by the Motion Generation API (see :doc:`Scene Interaction <../motion_generation/scene_interaction>`), allowing automatic scene initialization and synchronization
using the Motion Generation :class:`WorldBinding`.

Minimal Wrapping
#######################

The integration only wraps what's necessary for |isaac-sim_short| compatibility. |cumotion|'s native Python API is used directly for:

* Kinematics - Direct access to :class:`cumotion.Kinematics` objects
* Path specifications - Use |cumotion|'s native path specification API
* Parameter configuration - Full parameter structs are exposed for direct modification according to |cumotion|'s documentation

Coordinate Frame Conversion
############################

The |cumotion| integration provides utility functions to convert between |isaac-sim_short| world frame 
coordinates and |cumotion| base frame coordinates. These helpers simplify working with the |cumotion| Python API
while using Isaac Sim coordinates. The general workflow is:

* Create the world coordinate you need in Isaac Sim (full pose, translation, or rotation)
* Convert to |cumotion| base frame coordinates using the utility function
* Use the |cumotion| python API with the base frame coordinates (call kinematics functions, create path specifications, etc.)
* If needed, convert back to Isaac Sim coordinates using the utility function

Integration with Motion Generation API
---------------------------------------

The cuMotion integration is built on top of the |isaac-sim_short| Motion Generation API, providing:

* **WorldInterface Implementation**: :class:`CumotionWorldInterface` implements the :class:`WorldInterface` interface, enabling use with :class:`WorldBinding` and :class:`SceneQuery`
* **BaseController Implementation**: :class:`RmpFlowController` implements the :class:`BaseController` interface, enabling composition with other controllers
* **Trajectory Interface**: |cumotion| trajectories implement the :class:`Trajectory` interface, enabling use with :class:`TrajectoryFollower`


Next Steps
----------

For detailed information on each component, see the following sections:

Tutorials
#########
.. toctree::
   :maxdepth: 2

   tutorial_robot_configuration
   tutorial_world_interface
   tutorial_rmpflow
   tutorial_graph_planner
   tutorial_trajectory_generator
   tutorial_trajectory_optimizer
