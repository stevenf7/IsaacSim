async def _run_pallet_scenario(self):
    await omni.kit.app.get_app().next_update_async()
    print(f"[PalletizingSDGDemo] Running pallet scenario for bin {self._bin_counter}..")
    mesh_to_orig_mats = {}
    pallet_mesh = self._stage.GetPrimAtPath(self.PALLET_PRIM_MESH_PATH)
    pallet_orig_mat, _ = UsdShade.MaterialBindingAPI(pallet_mesh).ComputeBoundMaterial()
    mesh_to_orig_mats[pallet_mesh] = pallet_orig_mat
    for i in range(self._bin_counter + 1):
        bin_mesh = self._stage.GetPrimAtPath(f"{self.BINS_FOLDER_PATH}/bin_{i}/Visuals/FOF_Mesh_Magenta_Box")
        bin_orig_mat, _ = UsdShade.MaterialBindingAPI(bin_mesh).ComputeBoundMaterial()
        mesh_to_orig_mats[bin_mesh] = bin_orig_mat

    self._create_bin_and_pallet_graph()

    out_dir = os.path.join(self._output_dir, f"writer_bin_{self._bin_counter}", "")
    backend = rep.backends.get("DiskBackend")
    backend.initialize(output_dir=out_dir)
    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(
        backend=backend,
        rgb=True,
        instance_segmentation=True,
        colorize_instance_segmentation=True,
    )
    rp = rep.create.render_product(self._rep_camera, (512, 512))
    writer.attach(rp)

    for i in range(self._pallet_frames):
        await rep.orchestrator.step_async(rt_subframes=16, delta_time=0.0)

    # Make sure the backend finishes writing the data before clearing the generated SDG graph
    await rep.orchestrator.wait_until_complete_async()

    # Free up resources after the capture
    writer.detach()
    rp.destroy()

    # Restore the original materials of the randomized meshes
    for mesh, mat in mesh_to_orig_mats.items():
        UsdShade.MaterialBindingAPI(mesh).Bind(mat, UsdShade.Tokens.strongerThanDescendants)

    # Cleanup the generated SDG graph
    if self._stage.GetPrimAtPath("/Replicator"):
        omni.kit.commands.execute("DeletePrimsCommand", paths=["/Replicator"])

    # Return in paused state if there are no more bins to capture
    if not self._next_bin():
        return

    # Resume the simulation and continue with the next bin
    self._timeline_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
        event_name=omni.timeline.GLOBAL_EVENT_CURRENT_TIME_TICKED,
        on_event=self._on_timeline_event,
        observer_name="PalletizingSDGDemo._on_timeline_event",
    )
    self._timeline.play()
