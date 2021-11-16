Lula [omni.isaac.lula]
################################

Overview
========

.. automodule:: lula

Logging
=======

.. autoclass:: lula.LogLevel
  :members:
  :undoc-members:

.. autofunction:: lula.set_log_level

Rotations and Poses
===================

.. autoclass:: lula.Rotation3
  :members:
  :undoc-members:

.. autoclass:: lula.Pose3
  :members:
  :undoc-members:

Robot Specification
===================

.. autoclass:: lula.RobotDescription
  :members:
  :undoc-members:

.. autofunction:: lula.load_robot
.. autofunction:: lula.load_robot_from_memory

World Specification
===================

.. autoclass:: lula.Obstacle
  :members:
  :undoc-members:

.. autofunction:: lula.create_obstacle

.. autoclass:: lula.World
  :members:
  :undoc-members:

.. autofunction:: lula.create_world

.. autoclass:: lula.WorldView
  :members:
  :undoc-members:

Kinematics
==========

.. autoclass:: lula.Kinematics
  :members:
  :undoc-members:

Inverse Kinematics
==================

.. autoclass:: lula.CyclicCoordDescentIkConfig
  :members:
  :undoc-members:

.. autoclass:: lula.CyclicCoordDescentIkResults
  :members:
  :undoc-members:

.. autofunction:: lula.compute_ik_ccd

Motion Planning
===============

.. autoclass:: lula.MotionPlanner
  :members:
  :undoc-members:

.. autofunction:: lula.create_motion_planner

RMPflow
=======

.. autoclass:: lula.RmpFlowConfig
  :members:
  :undoc-members:

.. autofunction:: lula.create_rmpflow_config
.. autofunction:: lula.create_rmpflow_config_from_memory

.. autoclass:: lula.RmpFlow
  :members:
  :undoc-members:

.. autofunction:: lula.create_rmpflow

Geometric Fabrics
=================

.. note::
  Lula's support for motion policies based on `geometric fabrics <https://arxiv.org/abs/2109.10443>`_
  is under active development and will be exposed in a future release.

..
  Suppress generation of geometric fabrics docs for now:
  .. autoclass:: lula.FabricConfig
  .. autofunction:: lula.create_fabric_config
  .. autofunction:: lula.create_fabric_config_from_memory

  .. autoclass:: lula.FabricState
  .. autofunction:: lula.create_fabric_state

  .. autofunction:: lula.create_fabric
