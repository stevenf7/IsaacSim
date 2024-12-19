API
===

Overview
--------

.. automodule:: lula
    :no-index:

|

Logging
-------
..
  autodoc does not provide a mechanism for controlling the ordering of class members derived
  from bound C++ (as opposed to python source).  Default ordering is alphabetical, so we have
  to document the log levels manually to ensure that they appear in the correct order.

.. autoclass:: lula.LogLevel
    :no-index:

    .. py:data:: FATAL
        :no-index:

        Logging level for nonrecoverable errors (minimum level, so always enabled).

    .. py:data:: ERROR
        :no-index:

        Logging level for recoverable errors.

    .. py:data:: WARNING
        :no-index:

        Logging level for warnings, indicating possible cause for concern.

    .. py:data:: INFO
        :no-index:

        Logging level for informational messages.

    .. py:data:: VERBOSE
        :no-index:

        Logging level for highly verbose informational messages.

.. autofunction:: lula.set_log_level
    :no-index:

|

Rotations and Poses
-------------------

.. autoclass:: lula.Rotation3
    :no-index:
    :members:
    :undoc-members:

.. autoclass:: lula.Pose3
    :no-index:
    :members:
    :undoc-members:

|

Robot Specification
-------------------

.. autoclass:: lula.RobotDescription
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.load_robot
    :no-index:

.. autofunction:: lula.load_robot_from_memory
    :no-index:

|

World Specification
-------------------

.. autoclass:: lula.Obstacle
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_obstacle
    :no-index:

.. autoclass:: lula.World
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_world
    :no-index:

.. autoclass:: lula.WorldView
    :no-index:
    :members:
    :undoc-members:

|

Kinematics
----------

.. autoclass:: lula.Kinematics
    :no-index:
    :members:
    :undoc-members:

|

Inverse Kinematics
------------------

.. autoclass:: lula.CyclicCoordDescentIkConfig
    :no-index:
    :members:
    :undoc-members:

.. autoclass:: lula.CyclicCoordDescentIkResults
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.compute_ik_ccd
    :no-index:

|

Path Specification
------------------

.. autoclass:: lula.CSpacePathSpec
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_c_space_path_spec
    :no-index:

.. autoclass:: lula.TaskSpacePathSpec
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_task_space_path_spec
    :no-index:

.. autoclass:: lula.CompositePathSpec
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_composite_path_spec
    :no-index:

.. autofunction:: lula.load_c_space_path_spec_from_file
    :no-index:

.. autofunction:: lula.load_c_space_path_spec_from_memory
    :no-index:

.. autofunction:: lula.export_c_space_path_spec_to_memory
    :no-index:

.. autofunction:: lula.load_task_space_path_spec_from_file
    :no-index:

.. autofunction:: lula.load_task_space_path_spec_from_memory
    :no-index:

.. autofunction:: lula.export_task_space_path_spec_to_memory
    :no-index:

.. autofunction:: lula.load_composite_path_spec_from_file
    :no-index:

.. autofunction:: lula.load_composite_path_spec_from_memory
    :no-index:

.. autofunction:: lula.export_composite_path_spec_to_memory
    :no-index:

|

Path Generation
---------------

.. autoclass:: lula.CSpacePath
    :no-index:
    :members:
    :undoc-members:

.. autoclass:: lula.LinearCSpacePath
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_linear_c_space_path
    :no-index:

.. autoclass:: lula.TaskSpacePath
    :no-index:
    :members:
    :undoc-members:

.. autoclass:: lula.TaskSpacePathConversionConfig
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.convert_composite_path_spec_to_c_space
    :no-index:

.. autofunction:: lula.convert_task_space_path_spec_to_c_space
    :no-index:

|

Trajectory Generation
---------------------

.. autoclass:: lula.Trajectory
    :no-index:
    :members:
    :undoc-members:

.. autoclass:: lula.CSpaceTrajectoryGenerator
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_c_space_trajectory_generator
    :no-index:

|

Collision Sphere Generation
---------------------------

.. autoclass:: lula.CollisionSphereGenerator
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_collision_sphere_generator
    :no-index:

|

Motion Planning
---------------

.. autoclass:: lula.MotionPlanner
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_motion_planner
    :no-index:

|

RmpFlow
-------

.. autoclass:: lula.RmpFlowConfig
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_rmpflow_config
    :no-index:

.. autofunction:: lula.create_rmpflow_config_from_memory
    :no-index:

.. autoclass:: lula.RmpFlow
    :no-index:
    :members:
    :undoc-members:

.. autofunction:: lula.create_rmpflow
    :no-index:
