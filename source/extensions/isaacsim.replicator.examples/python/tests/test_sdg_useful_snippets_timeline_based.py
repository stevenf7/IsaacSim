# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
from collections import Counter

import omni.kit
import omni.usd


# Check the contents of a folder against expected extension counts e.g expected_counts={png: 3, json: 3, npy: 3}
def validate_folder_contents(path: str, expected_counts: dict[str, int]) -> bool:
    if not os.path.exists(path) or not os.path.isdir(path):
        return False

    # Count the number of files with each extension
    file_counts = Counter(f.split(".")[-1] for f in os.listdir(path) if "." in f)
    print(f"File counts: {file_counts}")

    # Check that the counts match the expected counts
    return all(file_counts.get(ext, 0) == count for ext, count in expected_counts.items())


class TestSDGUsefulSnippets(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def test_sdg_snippet_custom_fps_writer_annotator(self):
        import asyncio
        import os

        import carb.settings
        import omni.kit.app
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd

        # NOTE: To avoid FPS delta misses make sure the sensor framerate is divisible by the timeline framerate
        STAGE_FPS = 100.0
        SENSOR_FPS = 10.0
        SENSOR_DT = 1.0 / SENSOR_FPS

        async def run_custom_fps_example_async(num_frames=10):
            # Create a new stage
            await omni.usd.get_context().new_stage_async()

            # Disable capture on play (data will only be accessed at custom times)
            carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)

            # Make sure fixed time stepping is set (the timeline will be advanced with the same delta time)
            carb.settings.get_settings().set("/app/player/useFixedTimeStepping", True)

            # Set the timeline parameters
            timeline = omni.timeline.get_timeline_interface()
            timeline.set_looping(False)
            timeline.set_current_time(0.0)
            timeline.set_end_time(10)
            timeline.set_time_codes_per_second(STAGE_FPS)
            timeline.play()
            timeline.commit()

            # Create a light and a semantically annotated cube
            rep.create.light()
            rep.create.cube(semantics=[("class", "cube")])

            # Create a render product and disable it (it will re-enabled when data is needed)
            rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512), name="rp")
            rp.hydra_texture.set_updates_enabled(False)

            # Create a writer and an annotator as different ways to access the data
            out_dir_rgb = os.getcwd() + "/_out_writer_fps_rgb"
            print(f"Writer data will be written to: {out_dir_rgb}")
            writer_rgb = rep.WriterRegistry.get("BasicWriter")
            writer_rgb.initialize(output_dir=out_dir_rgb, rgb=True)
            # NOTE: 'trigger=None' is needed to make sure the writer is only triggered at the custom schedule times
            writer_rgb.attach(rp, trigger=None)
            annot_depth = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
            annot_depth.attach(rp)

            # Run the simulation for the given number of frames and access the data at the desired framerates
            written_frames = 0
            previous_time = timeline.get_current_time()
            elapsed_time = 0.0
            for i in range(num_frames):
                current_time = timeline.get_current_time()
                delta_time = current_time - previous_time
                elapsed_time += delta_time
                print(
                    f"[{i}] current_time={current_time:.4f}; delta_time={delta_time:.4f}; elapsed_time={elapsed_time:.4f}/{SENSOR_DT:.4f};"
                )

                # Check if enough time has passed to trigger the sensor
                if elapsed_time >= SENSOR_DT:
                    # Reset the elapsed time with the difference to the optimal trigger time (when the timeline fps is not divisible by the sensor framerate)
                    elapsed_time = elapsed_time - SENSOR_DT

                    # Enable render products for data access
                    rp.hydra_texture.set_updates_enabled(True)

                    # Write will be scheduled at the next step call
                    writer_rgb.schedule_write()

                    # Step needs to be called after scheduling the write
                    await rep.orchestrator.step_async(delta_time=0.0)

                    # After step, the annotator data is available and in sync with the stage
                    annot_data = annot_depth.get_data()

                    # Count the number of frames written
                    print(f"\t Writing frame {written_frames}; annotator data shape={annot_data.shape};")
                    written_frames += 1

                    # Disable render products to avoid unnecessary rendering
                    rp.hydra_texture.set_updates_enabled(False)

                    # Restart the timeline if it has been paused by the replicator step function
                    if not timeline.is_playing():
                        timeline.play()

                previous_time = current_time
                # Advance the app (timeline) by one frame
                await omni.kit.app.get_app().next_update_async()

            # Make sure the writer finishes writing the data to disk
            await rep.orchestrator.wait_until_complete_async()

        # Run the example for a given number of frames
        # NOTE: the expected number of frames written will be (num_frames - 1) * SENSOR_FPS / STAGE_FPS
        await run_custom_fps_example_async(num_frames=61)

        # Validate the output directory contents
        num_frames = 61
        expected_write_counts = (num_frames - 1) * SENSOR_FPS / STAGE_FPS
        self.assertTrue(
            validate_folder_contents(
                path=os.getcwd() + "/_out_writer_fps_rgb", expected_counts={"png": expected_write_counts}
            )
        )

    async def test_sdg_snippet_subscribers_and_events(self):
        import asyncio
        import time

        import carb.events
        import carb.settings
        import omni.kit.app
        import omni.physx
        import omni.timeline
        import omni.usd
        from pxr import PhysxSchema, UsdPhysics

        # TIMELINE / STAGE
        USE_CUSTOM_TIMELINE_SETTINGS = False
        USE_FIXED_TIME_STEPPING = False
        PLAY_EVERY_FRAME = True
        PLAY_DELAY_COMPENSATION = 0.0
        SUBSAMPLE_RATE = 1
        STAGE_FPS = 30.0

        # PHYSX
        USE_CUSTOM_PHYSX_FPS = False
        PHYSX_FPS = 60.0
        MIN_SIM_FPS = 30

        # Simulations can also be enabled/disabled at runtime
        DISABLE_SIMULATIONS = False

        # APP / RENDER
        LIMIT_APP_FPS = False
        APP_FPS = 120

        # Duration after which to clear subscribers and print the cached events
        MAX_DURATION = 3.0
        PRINT_EVENTS = False

        def on_timeline_event(event: omni.timeline.TimelineEventType):
            global timeline_sub
            global timeline_events
            global wall_start_time
            elapsed_wall_time = time.time() - wall_start_time

            # Cache only time advance events
            if event.type == omni.timeline.TimelineEventType.CURRENT_TIME_TICKED.value:
                event_name = omni.timeline.TimelineEventType(event.type).name
                event_payload = event.payload
                timeline_events.append((elapsed_wall_time, event_name, event_payload))

            # Clear subscriber and print cached events
            if elapsed_wall_time > MAX_DURATION:
                if timeline_sub is not None:
                    timeline_sub.unsubscribe()
                    timeline_sub = None
                num_events = len(timeline_events)
                fps = num_events / MAX_DURATION
                print(f"[timeline] captured {num_events} events with aprox {fps} FPS")
                if PRINT_EVENTS:
                    for i, (wall_time, event_name, payload) in enumerate(timeline_events):
                        print(f"\t[timeline][{i}]\ttime={wall_time:.4f};\tevent={event_name};\tpayload={payload}")

        def on_physics_step(dt: float):
            global physx_events
            global wall_start_time
            elapsed_wall_time = time.time() - wall_start_time

            # Cache physics events
            physx_events.append((elapsed_wall_time, dt))

            # Clear subscriber and print cached events
            if elapsed_wall_time > MAX_DURATION:
                # Physics unsubscription needs to be deferred from the callback function
                # see: '[Error] [omni.physx.plugin] Subscription cannot be changed during the event call'
                async def clear_physx_sub_async():
                    global physx_sub
                    if physx_sub is not None:
                        physx_sub.unsubscribe()
                        physx_sub = None

                asyncio.ensure_future(clear_physx_sub_async())
                num_events = len(physx_events)
                fps = num_events / MAX_DURATION
                print(f"[physics] captured {num_events} events with aprox {fps} FPS")
                if PRINT_EVENTS:
                    for i, (wall_time, dt) in enumerate(physx_events):
                        print(f"\t[physics][{i}]\ttime={wall_time:.4f};\tdt={dt};")

        def on_stage_render_event(event: omni.usd.StageRenderingEventType):
            global stage_render_sub
            global stage_render_events
            global wall_start_time
            elapsed_wall_time = time.time() - wall_start_time

            event_name = omni.usd.StageRenderingEventType(event.type).name
            event_payload = event.payload
            stage_render_events.append((elapsed_wall_time, event_name, event_payload))

            if elapsed_wall_time > MAX_DURATION:
                if stage_render_sub is not None:
                    stage_render_sub.unsubscribe()
                    stage_render_sub = None
                num_events = len(stage_render_events)
                fps = num_events / MAX_DURATION
                print(f"[stage render] captured {num_events} events with aprox {fps} FPS")
                if PRINT_EVENTS:
                    for i, (wall_time, event_name, payload) in enumerate(stage_render_events):
                        print(f"\t[stage render][{i}]\ttime={wall_time:.4f};\tevent={event_name};\tpayload={payload}")

        def on_app_update(event: carb.events.IEvent):
            global app_sub
            global app_update_events
            global wall_start_time
            elapsed_wall_time = time.time() - wall_start_time

            event_type = event.type
            event_payload = event.payload
            app_update_events.append((elapsed_wall_time, event_type, event_payload))

            if elapsed_wall_time > MAX_DURATION:
                if app_sub is not None:
                    app_sub.unsubscribe()
                    app_sub = None
                num_events = len(app_update_events)
                fps = num_events / MAX_DURATION
                print(f"[app] captured {num_events} events with aprox {fps} FPS")
                if PRINT_EVENTS:
                    for i, (wall_time, event_type, payload) in enumerate(app_update_events):
                        print(f"\t[app][{i}]\ttime={wall_time:.4f};\tevent={event_type};\tpayload={payload}")

        stage = omni.usd.get_context().get_stage()
        timeline = omni.timeline.get_timeline_interface()

        if USE_CUSTOM_TIMELINE_SETTINGS:
            # Ideal to make simulation and animation synchronized.
            # Default: True in editor, False in standalone.
            # NOTE:
            # - It may limit the frame rate (see 'timeline.set_play_every_frame') such that the elapsed wall clock time matches the frame's delta time.
            # - If the app runs slower than this, animation playback may slow down (see 'CompensatePlayDelayInSecs').
            # - For performance benchmarks, turn this off or set a very high target in `timeline.set_target_framerate`
            carb.settings.get_settings().set("/app/player/useFixedTimeStepping", USE_FIXED_TIME_STEPPING)

            # This compensates for frames that require more computation time than the frame's fixed delta time, by temporarily speeding up playback.
            # The parameter represents the length of these "faster" playback periods, which means that it must be larger than the fixed frame time to take effect.
            # Default: 0.0
            # NOTE:
            # - only effective if `useFixedTimeStepping` is set to True
            # - setting a large value results in long fast playback after a huge lag spike
            carb.settings.get_settings().set("/app/player/CompensatePlayDelayInSecs", PLAY_DELAY_COMPENSATION)

            # If set to True, no frames are skipped and in every frame time advances by `1 / TimeCodesPerSecond`.
            # Default: False
            # NOTE:
            # - only effective if `useFixedTimeStepping` is set to True
            # - simulation is usually faster than real-time and processing is only limited by the frame rate of the runloop
            # - useful for recording
            # - same as `carb.settings.get_settings().set("/app/player/useFastMode", PLAY_EVERY_FRAME)`
            timeline.set_play_every_frame(PLAY_EVERY_FRAME)

            # Timeline sub-stepping, i.e. how many times updates are called (update events are dispatched) each frame.
            # Default: 1
            # NOTE: same as `carb.settings.get_settings().set("/app/player/timelineSubsampleRate", SUBSAMPLE_RATE)`
            timeline.set_ticks_per_frame(SUBSAMPLE_RATE)

            # Time codes per second for the stage
            # NOTE: same as `stage.SetTimeCodesPerSecond(STAGE_FPS)` and `carb.settings.get_settings().set("/app/stage/timeCodesPerSecond", STAGE_FPS)`
            timeline.set_time_codes_per_second(STAGE_FPS)

        # Create a PhysX scene to set the physics time step
        if USE_CUSTOM_PHYSX_FPS:
            physx_scene = None
            for prim in stage.Traverse():
                if prim.IsA(UsdPhysics.Scene):
                    physx_scene = PhysxSchema.PhysxSceneAPI.Apply(prim)
                    break
            if physx_scene is None:
                physics_scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
                physx_scene = PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/PhysicsScene"))

            # Time step for the physics simulation
            # Default: 60.0
            physx_scene.GetTimeStepsPerSecondAttr().Set(PHYSX_FPS)

            # Minimum simulation frequency to prevent clamping; if the frame rate drops below this,
            # physics steps are discarded to avoid app slowdown if the overall frame rate is too low.
            # Default: 30.0
            # NOTE: Matching `minFrameRate` with `TimeStepsPerSecond` ensures a single physics step per update.
            carb.settings.get_settings().set("/persistent/simulation/minFrameRate", MIN_SIM_FPS)

        # Throttle Render/UI/Main thread update rate
        if LIMIT_APP_FPS:
            # Enable rate limiting of the main run loop (UI, rendering, etc.)
            # Default: False
            carb.settings.get_settings().set("/app/runLoops/main/rateLimitEnabled", LIMIT_APP_FPS)

            # FPS limit of the main run loop (UI, rendering, etc.)
            # Default: 120
            # NOTE: disabled if `/app/player/useFixedTimeStepping` is False
            carb.settings.get_settings().set("/app/runLoops/main/rateLimitFrequency", int(APP_FPS))

        # Simulations can be selectively disabled (or toggled at specific times)
        if DISABLE_SIMULATIONS:
            carb.settings.get_settings().set("/app/player/playSimulations", False)

        # Start the timeline
        timeline.set_current_time(0)
        timeline.set_end_time(MAX_DURATION + 1)
        timeline.set_looping(False)
        timeline.play()
        timeline.commit()
        wall_start_time = time.time()

        # Subscribe and cache various events for a limited duration
        timeline_events = []
        timeline_sub = timeline.get_timeline_event_stream().create_subscription_to_pop(on_timeline_event)
        physx_events = []
        physx_sub = omni.physx.get_physx_interface().subscribe_physics_step_events(on_physics_step)
        stage_render_events = []
        stage_render_sub = (
            omni.usd.get_context().get_rendering_event_stream().create_subscription_to_pop(on_stage_render_event)
        )
        app_update_events = []
        app_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(on_app_update)
