..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_cortex_3_example_peck_games:

==============================
Behavior Examples: Peck Games
==============================



This tutorial shows how to design simple behaviors and explores the tradeoffs between state machines
and decider networks. It steps through two implementations of a simple ground-pecking behavior with
the Franka robot where the robot must peck around the blocks. The first implementation uses a state
machine and is unable to react to blocks moved in front of its path. We fix that issue in the second
implementation with a simple decider network that internally leverages parts of the original state
machine. The state machine is effectively the same, but the higher-level decider can preempt the
state machine as needed for reactivity. Finally, we implement a reactive pick game using a pure
decider network. In that final example, we demonstrate the utility of the custom context object and
its monitors.

In all command line examples, we use the abbreviation ``isaac_python`` for the Isaac Sim python
script (``<isaac_sim_root>/python.sh`` on Linux and ``<isaac_sim_root>\python.bat`` on Windows).
The command lines are written relative to the working directory
``standalone_examples/api/isaacsim.cortex.framework``.

Each example will launch Isaac Sim without playing the simulation. Press play to run the simulation
and behavior.


Designing reactivity using decider networks
===========================================

We start with a simple behavior that has the robot peck at the ground avoiding regions occupied by
blocks.

State machine implementation
-----------------------------

The ``peck_state_machine`` module implements this simple peck behavior as a
state machine. Run the behavior using:

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=peck_state_machine

The Franka robot will peck at the ground avoiding the blocks. You can move the blocks around to see
how that affects where the robot chooses to peck.

The implementation is straightforward:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_3_example_peck_games/state_machine_implementation.py
    :language: python

With the simple state machine implementation, however, there's an error case in reactivity. Try
moving a block directly into the path of a current peck. The behavior will hang trying
unsuccessfully to get the end-effector to the target.

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
         {entryId: '1_2w7nfxac'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>


The state machine chooses the target on entry and keeps it fixed throughout the behavior. It,
therefore, doesn't react to the changing environment. State machines, by themselves, aren't great at
modeling reactive behavior. We'll use decider networks to fix this problem.

Decider network implementation
------------------------------

The ``peck_decider_network`` module augments this simple peck behavior by adding
a reactive ``Dispatch`` decider node. Run the behavior using:

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=peck_decider_network

The decider network uses a logical state monitor to monitor whether there's a block that would
prevent the end-effector from reaching the current peck target. If there is, it triggers the system
to re-choose the target.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_3_example_peck_games/decider_network_implementation.py
    :language: python

Note that the top-level ``Dispatch()`` decider can immediately preempt the sequential "peck" state
machine if the monitor ``monitor_active_target_p()`` detects a block to close to the target.

Try moving the block under the end-effector. This time, every time the block gets too close to the
end-effector's target, it immediately chooses a different target.

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
         {entryId: '1_o7v2lrub'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>



Designing logical state contexts
================================

Now let's implement a simple game where the robot pecks the block that's most recently been moved.
We use decider networks to make it simple to program reactivity to the block movements. This example
demonstrates how simple behaviors can be when the logical state is sufficiently modeled by the
context object.

The behavior is implemented in ``peck_game``. Run the behavior using:

.. code-block:: bash

    isaac_python franka_examples_main.py --behavior=peck_game

The ``PeckContext`` class handles monitoring block movement and setting the latest active target
accordingly. It also monitors whether the end-effector is close to the block which is useful in
deciding whether the robot needs to lift away from the block before moving to it's next target.

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_3_example_peck_games/designing_logical_state_contexts.py
    :language: python

Given the logical state monitored by the context object, the main logic can be concisely written as
the following ``Dispatch`` decider node:

.. literalinclude:: ../snippets/cortex_tutorials/tutorial_cortex_3_example_peck_games/designing_logical_state_contexts.py
    :language: python

In words, it reasons according to the following rules: If the end-effector is close to an inactive
block, we need to just lift away from it (it's too close). Otherwise, if there's an active block,
move to peck it. If no block is active, go home. This ``decide()`` method is ticked every cycle so
immediately once the active block monitor notices a block has moved, it acts on it.

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
         {entryId: '1_slk6iea5'}
         );
         } catch (e)
         { console.error(e.message) }
      </script>
      </div>
   </div>

