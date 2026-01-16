async def _run_bin_flip_scenario(self):
    await omni.kit.app.get_app().next_update_async()
    print(f"[PalletizingSDGDemo] Running bin flip scenario for bin {self._bin_counter}..")

    self._switch_to_pathtracing(spp=16, total_spp=32)
    await omni.kit.app.get_app().next_update_async()
    self._create_bin_flip_graph()

    rgb_annot = rep.annotators.get("rgb")
    instance_segmentation_annot = rep.annotators.get("instance_segmentation", init_params={"colorize": True})
    rp = rep.create.render_product(self._rep_camera, (512, 512))
    rgb_annot.attach(rp)
    instance_segmentation_annot.attach(rp)
    out_dir = os.path.join(self._output_dir, f"annot_bin_{self._bin_counter}")
    os.makedirs(out_dir, exist_ok=True)

    for i in range(self._bin_flip_frames):
        await rep.orchestrator.step_async(rt_subframes=16, delta_time=0.0)

        rgb_data = rgb_annot.get_data()
        rgb_file_path = os.path.join(out_dir, f"rgb_{i}.png")
        write_image(path=rgb_file_path, data=rgb_data)

        instance_segmentation_data = instance_segmentation_annot.get_data()
        instance_segmentation_file_path = os.path.join(out_dir, f"instance_segmentation_{i}.png")
        write_image(path=instance_segmentation_file_path, data=instance_segmentation_data["data"])
        with open(os.path.join(out_dir, f"instance_segmentation_info_{i}.json"), "w") as f:
            json.dump(instance_segmentation_data["info"], f, indent=4)

    # Wait for the data to be written to disk and free up resources after the capture
    await rep.orchestrator.wait_until_complete_async()
    rgb_annot.detach()
    instance_segmentation_annot.detach()
    rp.destroy()

    # Cleanup the generated SDG graph
    if self._stage.GetPrimAtPath("/Replicator"):
        omni.kit.commands.execute("DeletePrimsCommand", paths=["/Replicator"])

    self._switch_to_realtime_pathtracing()

    # Set the flag to indicate that the bin flip scenario is done
    self._bin_flip_scenario_done = True
    self._timeline_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
        event_name=omni.timeline.GLOBAL_EVENT_CURRENT_TIME_TICKED,
        on_event=self._on_timeline_event,
        observer_name="PalletizingSDGDemo._on_timeline_event",
    )
    self._timeline.play()
