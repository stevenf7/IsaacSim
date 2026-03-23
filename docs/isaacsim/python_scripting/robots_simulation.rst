..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_robot_simulation_how_to:

===============================
Robot Simulation Snippets
===============================

.. |link_Articulation| raw:: html

    <a href="../py/source/extensions/isaacsim.core.experimental.prims/docs/index.html#isaacsim.core.experimental.prims.Articulation" target="_blank">Articulation</a>

.. hint::

    Refer to the |link_Articulation| class documentation for more details on the API.

Wrapping Articulations
=======================

.. note::

    The following snippets should only be run once on a new stage.
    Create a new stage (`File > New` menu) and run the snippets in the Script Editor (`Window > Script Editor` menu).

Adds two Franka robots to the stage and wraps them via an |link_Articulation| object to control them simultaneously.

.. literalinclude:: ../snippets/python_scripting/robots_simulation/wrapping_articulations.py
    :language: python
    :linenos:

Play the simulation.
Then, open a new tab in the Script Editor window (`Tab > Add Tab` menu) and execute the following code to set the DOF positions for each articulation.

.. literalinclude:: ../snippets/python_scripting/robots_simulation/wrapping_articulations_2.py
    :language: python
    :linenos:

DOF Control
=====================

.. note::

    The following snippets should only be run once on a new stage that has the Franka robot at the ``/Franka`` prim path,
    and while the simulation is playing.

    Prepare the scene:

    #. Add a Franka robot to the stage via the `Create > Robots > Franka Emika Panda Arm` menu.
    #. Play the simulation.

.. warning::

    The snippets are disparate examples, running them out of order may have unintended consequences.
    The resulting movements may not respect the robot's kinematic limitations.

Make sure there is a Franka robot at the ``/Franka`` prim path and that the simulation is playing.
Then, open the Script Editor window (`Window > Script Editor` menu) and run the following snippets.

Query Articulation
^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/query_articulation.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

Read DOF States
^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/read_dof_states.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

DOF Position Control
^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/dof_position_control.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

Single DOF Position Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/single_dof_position_control.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

DOF Velocity Control
^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/velocity_control.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

Single DOF Velocity Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/single_dof_velocity_control.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --

DOF Effort Control
^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/robots_simulation/dof_effort_control.py
    :language: python
    :linenos:
    :start-after: # -- End test setup --
    :end-before: # -- Test cleanup --
