..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_cortex_4_franka_block_stacking:

==================================
Walkthrough: Franka Block Stacking
==================================



This tutorial walks through a complete reactive block stacking application. This example builds
the scene entirely using the Isaac Sim core Python API and runs the behavior. See
:ref:`isaac_sim_app_tutorial_cortex_5_ur10_bin_stacking` for an example of designing a behavior for
an existing USD environment.

In all command line examples, we use the abbreviation ``isaac_python`` for the Isaac Sim python
script (``<isaac_sim_root>/python.sh`` on Linux and ``<isaac_sim_root>\python.bat`` on Windows).
The command lines are written relative to the working directory
``standalone_examplesomni/api/isaacsim.cortex.framework``.

Run the following demo

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=block_stacking_behavior

Press play once Isaac Sim has started up. You'll see the Franka block stacking demo running.

This tutorial will step through the demo.

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
         {entryId: '1_x9i19fxg'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>


The environment has a Franka robot with a set of 4 blocks of different colors. Its goal is to stack
the blocks into a tower in a pre-defined order. This behavior is reactive and robust to user
interaction. Users can move the blocks as shown in the video and the robot will adapt as needed to
continue progressing toward its goal.


Block stacking decider network
==============================

The decider network is shown in the figure below.

.. image:: /images/isaac_cortex_block_stacking_decider_network.png
    :align: center
    :width: 960
    :alt: Block stacking decider network.

In words, the dispatch revolves around the state of the tower and the gripper. If the tower's done,
then go home. If there's more work to do, if there's a block in the gripper, place it somewhere.
Otherwise, if there's no block in the gripper, acquire a block. At the next level down, it decides
where to place the block and which block to acquire. The pick block and place at target decider
nodes (action nodes) are the same in all cases and key off parameters passed in from the decider
nodes one level up.


Top-level dispatch
==================

The behavior is constructed as a decider network:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/top_level_dispatch.py
    :language: python

with top-level dispatch decider node ``BlockPickAndPlaceDispatch``. The dispatch decider node's
implementation is simple, directly modeling the logic shown in the above diagram:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/top_level_dispatch_1.py
    :language: python

If the tower's complete, then go home. Otherwise, there's more to do with the tower. If there's
nothing in the gripper (gripper clear) then pick up a block. Otherwise, there's a block in the
gripper, and place it somewhere. The rest is about both choosing what to pick or where to place the
current block, and how to perform this specific action.

Each of these decisions map to the children setup on construction. Both the pick and place behaviors
are modeled as ``DfRldsDecider`` nodes as described next.


Robust Logical Dynamical Systems (RLDS)
=======================================

Both the pick and place behaviors are modeled as Robust Logical Dynamical Systems (RLDS). See the
`RLDS paper on ArXiv <https://arxiv.org/abs/1908.01896>`_. An RLDS is a sequence of behaviors, each
of which has a entry condition on the logical state defining whether it's runnable. The RLDS
algorithm steps backward from the last behavior in the sequence checking each node's runnability
condition. It executes the first (most distal) behavior that says it's runnable. In that sense, the
more distal the behavior, the higher the priority. The sequence is known as its *priority sequence*.

See ``class DfRldsDecider`` for the RLDS implementation as a decider node. The ``decide()`` method
implements the reverse sweep through the RLDS sequence.  See also Nathan Ratliff's `Isaac Cortex
GTC22 talk <https://www.nvidia.com/en-us/on-demand/session/gtcspring22-s42693/>`_ for additional
details on RLDSs.

The pick RLDS decider
-----------------------

The pick RLDS decider has three behaviors in its priority sequence.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/the_pick_rlds_decider.py
    :language: python

It's most intuitive to read these nodes in reverse since that's the order they're processed by the
RLDS algorithm. In order of highest priority to lowest priority (reverse order) we have:

#. **Open gripper:** If the gripper isn't open, the highest priority action is to open the gripper.
#. **Pick block:** To get here, the gripper must be open. If the block is between the fingers, pick it.
#. **Reach to block:** To get here, the gripper is open but not at the block yet. Reach toward the
   block.

Each node in the sequence executes an action designed to drive the system toward satisfying the
runnable condition of the next behavior in the sequence.

The decision of which block to pick is handled by the ``reach_to_block_rd`` node. It's constructed
in the section of code hidden by the ``...`` above:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/reach_to_block_to_get_here_the_gripper_is_open_but.py
    :language: python

It first chooses the block in a ``choose_block`` node, then passes the chosen block as parameters down to
``approach_grasp``. ``ChooseNextBlock`` itself has two possible children
``ChooseNextBlockForTowerBuildUp`` and ``ChooseNextBlockForTowerTeardown``, and the decision is made
based on whether the stack is currently in the right order.

The place RLDS decider
------------------------

The place RLDS decider is similar in nature to the pick decider:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/the_place_rlds_decider.py
    :language: python

Again, ``ReachToPlacementRd`` itself decides where to place base on the current logical state of the
tower.

Pick and place atomic actions
-----------------------------

The ``pick_block`` node is itself an state machine implemented by the ``PickBlockRd`` node. Its
state sequence is built on construction:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/pick_and_place_atomic_actions.py
    :language: python

The state machine shouldn't be interrupted to ensure successful grasps, so we make it atomic,
by locking the decider network in the beginning and unlocking it in the end.
Locking the decider network ensures that the decision path from the root to this node remain the
same until it's unlocked. If we didn't do that, the higher-level dispatch could preempt this node
half way through and prevent a successful pick. This model is the reverse of most other frameworks
to promote reactivity. Everything is preemptable unless it's specifically locked.

The full sequence for a pick is

#. Lock the decider network so the pick behavior is atomic.
#. Close the gripper for .5 seconds.
#. Lift for .25 seconds.
#. Mark the block as being in the gripper.
#. Unlock the decider network.

Much of this behavior is simply a timed sequence. If for any reason it's unsuccessful, the decider
network will be reactive to that at a higher level and recover. So we can model this behavior as
simply a blind behavior that executes at the right time. It records its belief (that the block is in
the gripper), but the context will continue to monitor whether that's true.

The ``PlaceBlockRd`` is another atomic sequential state machine similar to the pick state machine:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/unlock_the_decider_network.py
    :language: python

This state sequence includes opening, lifting, writing logical state, and closing the gripper. Note
that ``set_top_block_aligned`` marks an ``is_aligned`` flag in the block. In this demo we don't do
anything with that flag, but in a real-world system implementation, we would likely have two
behaviors, a place behavior, then an align behavior. Placement might be inaccurate, so on initial
placement the ``is_aligned`` flag is ``False``. Then the decider would see that and run a pinch
alignment behavior which results in ``is_aligned`` being set to ``True``. This a good example of
logical state that's unobservable. Perception modules might not be accurate enough to fully detect
whether the block is misaligned, but pinching the block we know will align it to higher precision.
So we can run that behavior, and simply mark that it's been run.

In this example, keep the ``is_aligned`` logical state in there, but for brevity we don't implement
the pinch alignment behavior.

Logical state context
=====================

All of these behaviors are supported by the logical state information extracted by the
``BuildTowerContext``.  The easiest way to understand what information the context extracts as
logical state is to look at the collection of logical state monitors it uses:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_4_franka_block_stacking/logical_state_context.py
    :language: python

In order, the set of monitors are:

#. **Monitor perception:** Periodically sync measured block transforms to the belief blocks. Syncing
   is suppressed when the block is in the end-effector and the measured transform is within a radius
   of the belief. Since the block is moving, we expect the belief to be more accurate during this
   period than perception, but it's still reactive to the block falling from the gripper.

#. **Monitor block tower:** Based on the positions of the blocks, it infers what the current state of
   the block tower is and populates the ``block_tower`` data structure appropriately. Decider nodes
   can query the state of the block tower using that data structure and it will always reflect the
   current state.

#. **Monitor gripper has block:** Monitors whether there's a block in the gripper. There's an
   interaction between this monitor and the pick behavior. The pick behavior will seed the belief
   that there's a block in the gripper since that was the intent, and this monitor simply verifies
   that it's true.

#. **Monitor suppression requirements:** Generally, collision avoidance is active between the robot
   and the blocks (especially important to avoid knocking the tower down). But the robot needs to
   interact with the blocks when picking and placing. This monitor automatically suppresses
   collisions when interaction with blocks is expected.

#. **Monitor diagnostics:** Prints some information about the logical state at a readable
   (throttled) rate.

The information collected by the logical state monitors is everything needed for the decider network
to make robust reactive decisions.
