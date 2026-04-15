..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_cortex_2_decider_networks:

==============================
Decider networks
==============================

.. warning::
    [DEPRECATED]: The Cortex framework has been deprecated as of Isaac Sim 6.0.0 and will be removed in a future release.
    For behavior programming, migrate to open-source libraries such as
    `py_trees <https://py-trees.readthedocs.io/en/devel/>`_ for behavior trees or
    `transitions <https://github.com/pytransitions/transitions>`_ for finite state machines.
    Isaac Sim 7.0 will include examples using these libraries.


This tutorial steps through the basics of decider networks and demonstrates the concepts with some
simple examples. Decider networks, as a class of decision tools, include  state machines, and we
include some examples of how to construct state machines using our built in tooling.

In all command line examples, we use the abbreviation ``isaac_python`` for the Isaac Sim python
script (``<isaac_sim_root>/python.sh`` on Linux and ``<isaac_sim_root>\python.bat`` on Windows).
The command lines are written relative to the working directory
``standalone_examples/api/isaacsim.cortex.framework``.

Each example will launch Isaac Sim without playing the simulation. Press play to run the simulation
and behavior.

Related tutorials: :ref:`isaac_sim_app_tutorial_cortex_3_example_peck_games` steps through scripting
a series of simple games for the Franka robot, building off the concepts presented here. The
tutorial emphasizes some of the limitations of state machines and illustrates how decider networks
simplify the development of reactive behaviors. Likewise,
:ref:`isaac_sim_app_tutorial_cortex_4_franka_block_stacking` walks through a complete demo of how
decider networks and state machines are used to develop an interactive block stacking behavior for
the Franka.


Basics of decider networks
==============================

All behaviors in Cortex are decider networks. This section describes decider networks and covers the
basics of the framework tooling for implementing them. We also show how to implement state machines
using the framework.

.. image:: /images/isaac_cortex_decider_networks.png
    :align: center
    :width: 960
    :alt: Decider networks.


Decision framework tooling
------------------------------

A decider network is similar to a decision tree (although not strictly a tree, as described below),
but with a notion of statefulness. The full *decision framework* is implemented in
``isaacsim.cortex.framework/isaacsim/cortex/framework/df.py``. The decider network is represented by the
``DfNetwork`` class.

Decider networks are formally directed acyclic graphs of ``DfDecider`` nodes. One node is designated
the *root*, and *leaf* nodes are nodes with no children. Each decider node's job is to choose among
its children. This choice is made by the decider node's ``decide()`` method. Every step of the
behavior (generally at 60hz, one step per physics step) the decider network algorithm traces from
the root down to a leaf following the sequence of decisions made by the decider nodes encountered
along the way.

The decider network is represented by the ``DfNetwork`` class. The root is passed into the
``DfNetwork`` object on construction along with a custom *context* object which handles monitoring
logical state and gives each decider node access to the command API. Each decider node can access
the context object as ``self.context`` during execution.

Context objects derive from ``DfLogicalState`` which provides an API for adding logical state
monitors. Logical state monitors are simply functions that take the context object as input (e.g.
member functions of the context object are common); they're called once every cycle in the order
they're added. The context object also generally provides access to the robot's command API. See for
instance ``DfContext`` the behavior tools in the module
``isaacsim.cortex.framework/isaacsim/cortex/framework/dfb.py``. The ``DfContext`` is a common base class which
additionally provides access to the robot along with its command API.

Here's a simple example:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/decision_framework_tooling.py
    :language: python

The section at the bottom illustrates how to create a world, add a robot and behavior, and run it.
See ``isaacsim.cortex.framework/isaacsim/cortex/framework/cortex_world.py`` for more information on the cortex world
and its API. Its stepped automatically from ``world.run(simulation_app)`` in a standard loop runner.
Stepping the world processes the logical state, decision (behavior), and command API (policy) layers
of the Cortex pipeline:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/the_decide_method_has_access_to_the_context_object.py
    :language: python

The ``world.add_decider_network(decider_network)`` automatically adds a logical state monitor which
calls the context object's monitors and adds a behavior which steps the decider network. More
generally, logical state monitors can be added using ``world.add_logical_state_monitor(...)`` and
behaviors can be added using ``world.add_behavior(...)``.


Statefulness of decider nodes and state machines
------------------------------------------------

Every cycle, the decider network algorithm traces from the root to a leaf creating an execution path
(the sequence of decider nodes visited). (See the above figure.) From cycle to cycle it keeps track
of the execution path and uses the previous path to determine whether the decider nodes are making
the same decisions as before, or making different decisions. Each decide node has an ``enter()`` and
``exit()`` method, and every time a new branch to a leaf is chosen, ``exit()`` is called on the
branch no longer taken in reverse order from the leaf to the branching point, and ``enter()`` is
called along the new branch in the order the new decider nodes are visited. The full decider node
API is

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/statefulness_of_decider_nodes_and_state_machines.py
    :language: python

``enter()`` is called (along with ``decide()``) only when the decider node is entered in the sense
defined above. As long as the execution path to this node remains consistent from step to step, only
``decide()`` is called.  Once it's no longer reached, ``exit()`` is called. (``DfBindable``
indicates that objects of this type will be able to access the custom context object as
``self.context`` during execution.)

These concepts are analogous to the entry and exit concepts of state machines. The decision
framework provides a ``DfState`` base class for defining state machines with an analogous API:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/class_dfdeciderdfbindable.py
    :language: python

``enter()`` is called on entry to the state, ``step()`` is called while in the state, and ``exit()``
is called when the state is exited. The ``step()`` method indicates the state machine transition
through its return value. E.g. returning ``self`` will transition back to itself, and returning
``None`` will transition to the terminal "do nothing" state. More generally, state transitions to
new states are implemented by returning a reference to that state object.

Since the concepts of entry, step/decide, and exit align between state machines and decider nodes
they are compatible within the decision framework. A ``DfStateMachineDecider`` is a decider node
which takes a start state of a state machine on construction and runs the state machine. The decider
node's ``enter()`` method resets the state machine to the start state and the ``decide()`` method
steps the state machine.

One common use case is the sequential state machine. If ``State1``, ``State2``, and ``State3`` are
each ``DfState`` objects which transition to themselves while doing work and terminate (transition
to ``None``) when finished, we can string them together into a sequential state machine using
``DfStateSequence([State1(), State2(), State3()])``. A ``DfStateSequence`` is itself a ``DfState``
object which transitions back to itself, making it a hierarchical state machine. Internally, it runs
the states in sequence, transitioning to the next state whenever a state terminates. We can loop the
sequence using ``DfStateSequence([State1(), State2(), State3()], loop=True)``

We can create a decider network that runs this state machine using:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/class_dfstatedfbindable.py
    :language: python

To see a complete example of using a looping sequential state machine run:

.. code-block:: bash

    isaac_python example_command_api_main.py

The robot will move the end-effector to a fixed target and maintain that target while changing the
nullspace arm configuration and opening and closing the gripper.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_1" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_1",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_yvdusn92'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>



Simple follow example
==============================

Run the follow example:

.. code-block:: bash

    isaac_python follow_example_main.py

It'll launch the robot with a sphere at the end-effector. Select the sphere and drag it around with
the Move gizmo.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_2" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_2",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_0g2wk0by'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>


We'll modify this simple example below. The final modified code is shown in
``follow_example_modified_main.py`` for reference.


Add an end-effector monitor
---------------------------

Currently, the decider network is created with just the default context object ``DfContext``. We'll
modify it to include a logical state monitor that monitors whether the end-effector has converged.

Add the following code

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/add_an_end_effector_monitor.py
    :language: python

Then modify the creation of the decider network to use this context object.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/add_an_end_effector_monitor_1.py
    :language: python

Run the example again, and you'll see ``is_target_reached: <val>`` printed out where ``<val>`` is
``False`` when the end-effector is away from the target and ``True`` when it reaches the target.


Setup automatic action on the monitored logical state
-----------------------------------------------------

Adding the end-effector monitor toggles the ``is_target_reached`` logical state, but doesn't do
anything with it. Now we'll add a second monitor to the ``FollowContext`` class to automatically
open and close the gripper based on whether the end-effector is at the target.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/setup_automatic_action_on_the_monitored_logical_st.py
    :language: python

This will close the gripper once the target's been reached and open it when it's not.

Run the example again and play with the sphere target. If you move the target away from the
end-effector, you'll see the gripper open and the end-effector each toward the target. Once the
target is reached, the gripper will close.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_3" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_3",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_x6d93n1s'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>



Simple state machine
========================

Run the following to launch an example of a simple state machine.

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=simple_state_machine

You'll see the robot move its end-effector up and down moving between two pre-specified points.

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_4" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_4",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_urqo1gyf'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>



Simple decider network
==============================

Run the following to launch an example of a simple state machine.

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=simple_decider_network

You'll see "<middle>" printed in the console. Select the ``/World/motion_commander_target`` prim in
the stage listing and select the Move gizmo. Move the end-effector to the left and right. When it
enters the left region (from the user's perspective) it'll print out "<left>"; when it moves back
into the middle region it'll print out "<middle>"; and when it moves into the right region it'll
print out "<right>".

.. raw:: html

   <div style="width: 100%;display: inline-block;position: relative;">
      <div id="dummy" style="margin-top: 56%;"></div>
      <div align="center">
      <div id="kaltura_player_5" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
      <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
      <script type="text/javascript">
         try {
         var kalturaPlayer = KalturaPlayer.setup({
         targetId: "kaltura_player_5",
         provider:
         { partnerId: 2935771, uiConfId: 46302491 }
         });
         kalturaPlayer.loadMedia(
         {entryId: '1_xg4cxvv7'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>


Note that this example additionally demonstrates passing parameters to a decider node.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_2_decider_networks/simple_decider_network.py
    :language: python

Running other behaviors
=======================

Any of the behaviors listed in ``isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/franka`` can be
loaded with this ``franka_examples_main.py`` example.

The full command line is

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=<behavior_name>


with ``<behavior_name>`` set to any of the following

.. code-block:: bash

        block_stacking_behavior
        peck_state_machine
        peck_decider_network
        peck_game
        simple_state_machine
        simple_decider_network


Alternatively, you can load behaviors directly from their Python module:

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=<path_to_behavior>

This tutorial stepped through the last two "simple" behaviors.  The ``peck_state_machine``,
``peck_decider_network`` and ``peck_game`` behaviors will be covered in
:ref:`isaac_sim_app_tutorial_cortex_3_example_peck_games`, and the ``block_stacking_behavior`` is
walked through in detail in :ref:`isaac_sim_app_tutorial_cortex_4_franka_block_stacking`.
