..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_replicator_amr_navigation:

==============================================
Randomization in Simulation -- AMR Navigation
==============================================

Example of using |isaac-sim_short| and Replicator to capture synthetic data from simulated environments (AMR Navigation).

Learning Objectives
-------------------

The goal of this tutorial is to demonstrate how to setup an |isaac-sim_short| simulation scenario together with the :doc:`omni.replicator <extensions:ext_replicator>` extension to capture synthetic data using diverse randomization techniques. 

In this tutorial you:

* Implement scene randomizations using USD / |isaac-sim_short| APIs:

    * Randomize poses of assets in the scene
    * Switch between different background environments

* Collect synthetic data at specific simulation events with Replicator
* Create and destroy render products on the fly to improve runtime performance
* Create and destroy Replicator capture graphs within the same simulation instance

Prerequisites
##############

* Familiarity with USD / |isaac-sim_short| APIs for scene creation and manipulation.
* Familiarity with :doc:`omni.replicator <extensions:ext_replicator>` and its :doc:`writers <extensions:ext_replicator/writer_examples>`.
* Basic understanding of :doc:`OmniGraph <extensions:ext_omnigraph>` for the navigation implementation.
* Running simulations as :ref:`Standalone Applications <standalone-application>` or via the :ref:`Script Editor <script-editor>`.

Scenario
---------

This tutorial uses the Nova Carter robot equipped with an :doc:`OmniGraph <extensions:ext_omnigraph>` navigation stack, notably without collision avoidance features. The navigation stack constantly drives the robot towards a designated Xform target (``<..>/targetXform``), positioned at the location of the randomized objects of interest. As the robot comes in the proximity of the object of interest, a synthetic data generation (SDG) pipeline is triggered to capture data from its two main camera sensors. After the data is captured the objects of interest are re-randomized and the simulation continues. After a certain number of frames (``env_interval``) the background environment is changed as well. After ``num_frames`` the application terminates. 

The ``use_temp_rp`` flag is used to provide an option to use temporary render products to improve the runtime performance. This speeds up the simulation by only using the render products when capturing the data, thus avoiding the overhead of rendering the sensor views when not capturing data.

.. image:: /images/isaac_tutorial_replicator_amr_0.gif
    :width: 32.5%

.. image:: /images/isaac_tutorial_replicator_amr_2.gif
    :width: 32.5%

.. image:: /images/isaac_tutorial_replicator_amr_1.gif
    :width: 32.5%

The scenario uses the left and right camera sensors of Nova Carter (``<..>/stereo_cam_<left/right>_sensor_frame/camera_sensor_<left/right>``) to collect **LdrColor** (rgb) :doc:`annotator <extensions:ext_replicator/annotators_details>` data using Replicator. By default, the data is written to ``<working_dir>/_out_nav_sdg_demo`` and runs for ``num_frames=9`` iterations. 

Furthermore, it changes the background environment every ``env_interval=3`` captured frames. By default the tutorial cycles through ``DEFAULT_ENV_URLS``; an entry of ``None`` creates a generic environment under ``/Environment`` using a Replicator dome light and a collider-enabled plane instead of loading a USD environment. The ``use_temp_rp`` flag can be used to optimize performance by disabling the sensor render products during simulation and temporarily enabling them during data capture. 

The following image provides an illustration of the resulting data from the various environments.

.. image:: /images/isaac_tutorial_replicator_amr_data.png

Implementation
---------------

The following section provides an overview and explanation of the implementation and examples on how to run the demo. 

.. tab-set::

    .. tab-item:: Standalone Application

        To run the example as a standalone application, use the following command to execute the provided script. The script also accepts several optional arguments to customize its behavior (on Windows use ``python.bat`` instead of ``python.sh``):

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/amr_navigation.py

        Arguments include:

        - ``--use_temp_rp`` flag to use temporary render products (default: False) 
        - ``--num_frames`` the number of frames to be captured (default: 9)
        - ``--env_interval`` the capture interval at which the background environment is changed (default: 3)
        - ``--env_urls`` replaces ``DEFAULT_ENV_URLS`` entirely. Use ``None`` for the generic environment

        For example, to run the application with all the arguments:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/amr_navigation.py --use_temp_rp --num_frames 9 --env_interval 3

        .. raw:: html

            <details closed>
            <summary>Standalone Script</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/amr_navigation.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        To run the example from the script editor, the following code must be executed:

        .. raw:: html

            <details closed>
            <summary>Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_amr_navigation/amr_navigation_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Code Explanation

        This tab describes each section of the larger sample script that is used for this tutorial. By reviewing the descriptions and code snippets you can understand how the script is working and how you might customize it for your use.
        
        The following snippets can be used to load and start the demo scene. Each of the snippets has an explanation that can be expanded. The snippets and explanations are collapsed so that you can control opening them as you read and work through the tutorial for yourself.

        **Running the AMR Navigation SDG Demo**

        The following snippet is from the end of the code sample, it runs for the given ``num_frames`` and changes the background environment every ``env_interval``. The output is written to the given ``out_dir path``. The ``use_temp_rp`` parameter can be used to optimize performance by creating render products only for the frames when the data is captured. When ``--env_urls`` is provided it replaces ``DEFAULT_ENV_URLS`` entirely; otherwise the demo uses the default environment cycle.

        The start method loads and runs the demo with the specified parameters, while clear halts the demo and clears any active subscribers and render products. You can use ``is_running`` to verify whether the demo is still running.  
      

        .. raw:: html

            <details closed>
            <summary>Running the NavSDGDemo Python Script Example</summary>

        .. code-block:: python

            out_dir = os.path.join(os.getcwd(), "_out_nav_sdg_demo", "")
            selected_env_urls = args.env_urls if args.env_urls is not None else DEFAULT_ENV_URLS
            nav_demo = NavSDGDemo()
            nav_demo.start(
                num_frames=args.num_frames,
                out_dir=out_dir,
                env_urls=selected_env_urls,
                env_interval=args.env_interval,
                use_temp_rp=args.use_temp_rp,
                seed=22,
            )

            while simulation_app.is_running() and nav_demo.is_running():
                simulation_app.update()

            simulation_app.close()

        .. raw:: html

            </details>


        **NavSDGDemo Class and Attributes**

        The demo script is wrapped in its own class called ``NavSDGDemo``.
            
        .. raw:: html

            <details closed>
            <summary>NavSDGDemo Class Snippet</summary>

        .. code-block:: python

            class NavSDGDemo:
                """Demonstration of synthetic data generation using an AMR navigating towards a target."""

                CARTER_URL = "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd"
                DOLLY_URL = "/Isaac/Props/Dolly/dolly.usd"
                PROPS_URL = "/Isaac/Props/YCB/Axis_Aligned_Physics"
                LEFT_CAMERA_REL_PATH = "sensors/front_hawk/left/camera_left"
                RIGHT_CAMERA_REL_PATH = "sensors/front_hawk/right/camera_right"
                ENVIRONMENT_SCOPE_PATH = "/Environment"

                def __init__(self) -> None:
                    """Initialize the navigation SDG demo with default values."""
                    self._carter_chassis = None
                    self._carter_nav_target = None
                    self._dolly = None
                    self._dolly_light = None
                    self._props = []
                    self._cycled_env_urls = None
                    self._env_interval = 1
                    self._timeline = None
                    self._timeline_sub = None
                    self._stage_event_sub = None
                    self._stage = None
                    self._trigger_distance = 2.0
                    self._num_frames = 0
                    self._frame_counter = 0
                    self._writer = None
                    self._out_dir = None
                    self._render_products = []
                    self._use_temp_rp = False
                    self._in_running_state = False

        .. raw:: html

            </details>
            
        The attributes of this class include:
            
        * ``self._carter_chassis`` and ``self._carter_nav_target`` prims are used to track Nova Carter and its target Xform in the navigation graph
        * ``self._dolly`` is used as the target for the navigation target of Nova Carter and to track the distance to Nova Carter
        * ``self._dolly_light`` randomized light placed above the dolly each captured frame
        * ``self._props`` list of prop prims to place and simulate above the dolly each captured frame
        * ``self._cycled_env_urls`` the paths for the background environments to cycle through, including ``None`` for the generic Replicator-built environment
        * ``self._env_interval`` is used to determine after how many frames to change the background environment
        * ``self._timeline`` is used to control (play/pause) the simulation timeline between frame captures
        * ``self._timeline_sub`` is the subscriber to the timeline ticks. It is used as the feedback loop to trigger the synthetic data generation
        * ``self._stage_event_sub`` is a subscriber to stage closing events used to clear the demo in case a new stage is opened
        * ``self._stage`` is used to access the active stage in order to create, access, and delete prims of interest
        * ``self._trigger_distance`` is used to determine the distance between Nova Carter and the dolly at which the synthetic data generation should trigger, the value is randomized after each capture
        * ``self._num_frames`` and ``self._frame_counter`` are used to track and stop the demo after the given number of frames
        * ``self._writer`` is the writer used to write the synthetic data to disk
        * ``self._render_products`` are the two render products attached to the left and right camera sensors of Nova Carter, the writer is attached to these to access data from the annotators
        * ``self._use_temp_rp`` is a flag, which when set to ``True``, causes the demo to disable render products when not capturing. Otherwise the render products are always enabled
        * ``self._in_running_state`` indicates the running state of the demo used to track whether the demo has finished or not
        * The class constant ``ENVIRONMENT_SCOPE_PATH`` keeps both referenced USD environments and the generic fallback environment under the same ``/Environment`` scope, which makes switching between them consistent.
 
    
        **Workflow and Start Function**

        The workflow's main functions are ``start`` and the ``_on_timeline_event`` callback functions. ``start`` resolves the selected environment list, creates a new environment with:
            
        * navigation specific physics scene
        * Nova Carter
        * navigation graph with the target Xform
        * dolly
        * randomization light
        * props to drop around the dolly

        If ``env_urls`` is ``None``, ``start`` uses ``DEFAULT_ENV_URLS``. Environment changes are routed through ``_load_environment``, which always rebuilds the shared ``/Environment`` scope. When the selected environment entry is ``None``, the demo creates a generic environment with ``rep.functional.create.dome_light``, ``rep.functional.create.plane``, and ``rep.functional.physics.apply_collider``.

        It also creates the timeline subscriber with ``_on_timeline_event`` as the callback function triggered with each timeline tick. The ``_on_timeline_event`` function checks if Nova Carter is close enough to the dolly, if so it pauses the simulation, unsubscribes the timeline callback, and triggers the synthetic data generation (SDG). Depending on whether the demo is running in the script editor or as a standalone application it runs the SDG synchronously or asynchronously.

        .. raw:: html

             <details closed>
             <summary>Workflow Snippet</summary>

        .. code-block:: python

            def start(
                self,
                num_frames: int = 10,
                out_dir: str | None = None,
                env_urls: list[str | None] | None = None,
                env_interval: int = 3,
                use_temp_rp: bool = False,
                seed: int | None = None,
            ) -> None:
                """Start the SDG demo with the given configuration."""
                print(f"[SDG] Starting")
                if seed is not None:
                    rep.set_global_seed(seed)
                    random.seed(seed)
                selected_env_urls = env_urls if env_urls is not None else DEFAULT_ENV_URLS
                self._num_frames = num_frames
                self._out_dir = out_dir if out_dir is not None else os.path.join(os.getcwd(), "_out_nav_sdg_demo")
                self._cycled_env_urls = cycle(selected_env_urls)
                self._env_interval = env_interval
                self._use_temp_rp = use_temp_rp
                self._frame_counter = 0
                self._trigger_distance = 2.0
                self._load_env()
                self._randomize_dolly_pose()
                self._randomize_dolly_light()
                self._randomize_prop_poses()
                self._setup_sdg()
                self._timeline = omni.timeline.get_timeline_interface()
                self._timeline.play()
                self._timeline_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
                    event_name=omni.timeline.GLOBAL_EVENT_CURRENT_TIME_TICKED,
                    on_event=self._on_timeline_event,
                    observer_name="amr_navigation.NavSDGDemo._on_timeline_event",
                )
                self._stage_event_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
                    event_name=omni.usd.get_context().stage_event_name(omni.usd.StageEventType.CLOSING),
                    on_event=self._on_stage_closing_event,
                    observer_name="amr_navigation.NavSDGDemo._on_stage_closing_event",
                )
                self._in_running_state = True

        .. code-block:: python

            def _on_timeline_event(self, e: carb.eventdispatcher.Event):
                """Check distance to dolly and trigger SDG capture when close enough."""
                carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
                dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
                dist = (Gf.Vec2f(dolly_loc[0], dolly_loc[1]) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
                if dist < self._trigger_distance:
                    print(f"[SDG] Starting SDG for frame no. {self._frame_counter}")
                    self._timeline.pause()
                    if self._is_running_in_script_editor():
                        import asyncio

                        task = asyncio.ensure_future(self._run_sdg_async())
                        task.add_done_callback(self._on_sdg_done)
                    else:
                        self._run_sdg()
                        self._setup_next_frame()

        .. raw:: html

                </details>


        **Randomizations Explanation** 

        To randomize the environment before the synthetic data capture, the following functions are used:

        * ``_randomize_dolly_pose``: places the dolly at a random pose with a given minimum distance from Nova Carter. After such a pose is found, the navigation target is placed at the dolly's position.
        * ``_randomize_dolly_light``: places the dolly light above the dolly with a new random color.
        * ``_randomize_prop_poses``: places the props above the dolly at random locations, which eventually starts to fall after the simulation starts.


        .. raw:: html

            <details closed>
            <summary>Randomizations Snippet</summary>

        .. code-block:: python

            def _randomize_dolly_pose(self) -> None:
                """Set random dolly position ensuring minimum distance from Carter."""
                min_dist_from_carter = 4
                carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
                for _ in range(100):
                    x, y = random.uniform(-6, 6), random.uniform(-6, 6)
                    dist = (Gf.Vec2f(x, y) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
                    if dist > min_dist_from_carter:
                        self._dolly.GetAttribute("xformOp:translate").Set((x, y, 0))
                        self._carter_nav_target.GetAttribute("xformOp:translate").Set((x, y, 0))
                        break
                self._dolly.GetAttribute("xformOp:rotateXYZ").Set((0, 0, random.uniform(-180, 180)))

            def _randomize_dolly_light(self) -> None:
                """Position light above dolly with random color."""
                dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
                self._dolly_light.GetAttribute("xformOp:translate").Set(dolly_loc + (0, 0, 3))
                self._dolly_light.GetAttribute("inputs:color").Set(
                    (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
                )

            def _randomize_prop_poses(self) -> None:
                """Stack props above the dolly with random horizontal offsets."""
                spawn_loc = self._dolly.GetAttribute("xformOp:translate").Get()
                spawn_loc[2] = spawn_loc[2] + 0.5
                for prop in self._props:
                    prop.GetAttribute("xformOp:translate").Set(spawn_loc + (random.uniform(-1, 1), random.uniform(-1, 1), 0))
                    spawn_loc[2] = spawn_loc[2] + 0.2

        .. raw:: html

            </details>


        **Synthetic Data Generation (SDG) Explanation**        

        When executing the synthetic data generation (SDG) pipeline the ``rep.orchestrator.step`` function is called to initiate the data capture and the execution of the writer's write function.
            
        Depending on the value of the ``use_temp_rp`` flag, the sensor's render products are handled differently: 
            
        * If set to ``True``, the render products are only enabled during data capture. 
        * ``False`` is the default. It renders the render products and processes every frame.

        .. note::

            ``_setup_sdg`` sets ``omni:sensor:tickRate = 0`` (autotrigger) on the Nova Carter
            ``front_hawk`` left and right cameras. Under multi-tick rendering, the per-sensor
            tick scheduler can fall out of sync with ``rep.orchestrator.step_async`` and the
            writer may receive no frames; forcing autotrigger keeps these sensor cameras in
            step with the orchestrator. This workaround is expected to be removed in a future
            release. See :ref:`isaac_sim_sensors_multitick_rendering` for details on the
            ``omni:sensor:tickRate`` attribute.

        .. raw:: html

            <details closed>
            <summary>Synthetic Data Generation (SDG) Snippet</summary>

        .. code-block:: python

            def _run_sdg(self) -> None:
                """Execute one SDG capture step synchronously."""
                if self._use_temp_rp:
                    self._enable_render_products()
                rep.orchestrator.step(rt_subframes=16)
                if self._use_temp_rp:
                    self._disable_render_products()

        .. raw:: html

            </details>

        **Next Frame Explanation**

        After the synthetic data generation (SDG) completes, the ``_setup_next_frame`` function prepares the simulation for the next frame. This involves incrementing the frame counter (``self._frame_counter``), randomizing the dolly, dolly light, and props. Then changing the background environment, if the ``env_interval`` is reached. Because environment loading now goes through the shared ``/Environment`` scope, switching between referenced USD environments and the generic ``None`` environment uses the same update path. Additionally the timeline and its subscriber are re-started. 
            
        If the ``_num_frames`` is reached the demo makes sure the the writer backend is finished with writing the data to disk (``rep.orchestrator.wait_until_complete``) and clears the demo.

        .. raw:: html

              <details closed>
              <summary>Next Frame Snippet</summary>

        .. code-block:: python

            def _setup_next_frame(self) -> None:
                """Prepare scene for next frame or finish if all frames captured."""
                self._frame_counter += 1
                if self._frame_counter >= self._num_frames:
                    print(f"[SDG] Finished")
                    # Make sure the data has been written to disk before clearing the state
                    if self._is_running_in_script_editor():
                        import asyncio

                        task = asyncio.ensure_future(rep.orchestrator.wait_until_complete_async())
                        task.add_done_callback(lambda t: self.clear())
                    else:
                        rep.orchestrator.wait_until_complete()
                        self.clear()
                    return

                self._randomize_dolly_pose()
                self._randomize_dolly_light()
                self._randomize_prop_poses()
                if self._frame_counter % self._env_interval == 0:
                    self._load_next_env()
                # Set a new random distance from which to take capture the next frame
                self._trigger_distance = random.uniform(1.75, 2.5)
                self._timeline.play()
                self._timeline_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
                    event_name=omni.timeline.GLOBAL_EVENT_CURRENT_TIME_TICKED,
                    on_event=self._on_timeline_event,
                    observer_name="amr_navigation.NavSDGDemo._on_timeline_event",
                )

        .. raw:: html

            </details>
