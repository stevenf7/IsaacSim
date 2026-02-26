.. _isaac_sim_cumotion_api:

==================
cuMotion API Reference
==================

This page provides an overview of the cuMotion integration API. For detailed information on each class, see the Python API documentation.

Core Classes
============

Configuration Loading
---------------------

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.load_cumotion_robot
.. #     isaacsim.robot_motion.experimental.cumotion.load_cumotion_supported_robot
.. #     isaacsim.robot_motion.experimental.cumotion.CumotionRobot

World Interface
---------------

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.CumotionWorldInterface

Controllers
-----------

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.RmpFlowController

Motion Planning
---------------

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.GraphBasedMotionPlanner

Trajectory Generation
---------------------

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.TrajectoryGenerator
.. #     isaacsim.robot_motion.experimental.cumotion.TrajectoryOptimizer
.. #     isaacsim.robot_motion.experimental.cumotion.CumotionTrajectory

Utility Functions
=================

Transform Utilities
-------------------

The transform utilities in ``isaacsim.robot_motion.experimental.cumotion.impl.utils`` provide coordinate conversion between Isaac Sim world frame and cuMotion robot base frame:

.. note::
    API documentation is temporarily disabled. See the source code for API details.

.. # .. autosummary::
.. #     :toctree: api
.. #     :template: autosummary/module.rst
.. #
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.isaac_sim_to_cumotion_pose
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.isaac_sim_to_cumotion_translation
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.isaac_sim_to_cumotion_rotation
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.cumotion_to_isaac_sim_pose
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.cumotion_to_isaac_sim_translation
.. #     isaacsim.robot_motion.experimental.cumotion.impl.utils.cumotion_to_isaac_sim_rotation

Direct cuMotion API Access
==========================

The integration provides direct access to cuMotion's native Python API. Key objects you can access:

* ``cumotion.Kinematics``: Direct access via ``robot_config.kinematics``
* ``cumotion.RobotDescription``: Direct access via ``robot_config.robot_description``
* ``cumotion.RmpFlowConfig``: Access via ``controller.get_rmp_flow_config()``
* ``cumotion.CSpaceTrajectoryGenerator``: Access via ``generator.get_cspace_trajectory_generator()``

For complete cuMotion API documentation, refer to the cuMotion library documentation.
