Lula [omni.isaac.lula]
################################

Overview
========

.. automodule:: lula

Logging
=======

..
  autodoc does not provide a mechanism for controlling the ordering of class members derived
  from bound C++ (as opposed to python source).  Default ordering is alphabetical, so we have
  to document the log levels manually to ensure that they appear in the correct order.
.. autoclass:: lula.LogLevel

  .. py:data:: FATAL

    Logging level for nonrecoverable errors (minimum level, so always enabled).

  .. py:data:: ERROR

    Logging level for recoverable errors.

  .. py:data:: WARNING

    Logging level for warnings, indicating possible cause for concern.

  .. py:data:: INFO

    Logging level for informational messages.

  .. py:data:: VERBOSE

    Logging level for highly verbose informational messages.

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
