"""Minimal static-scene SDG pipeline using Isaac Sim Replicator.

Captures annotated RGB, depth, segmentation, and bounding-box frames to disk
via BasicWriter.  Run with $ISAAC_SIM_DIR/python.sh.
"""


def run_minimal_sdg_pipeline(
    output_dir: str = "/tmp/sdg_output",
    num_frames: int = 10,
    rt_subframes: int = 32,
) -> None:
    """Run a minimal static-scene SDG capture loop.

    Args:
        output_dir: Directory to write captured frames.
        num_frames: Number of frames to capture.
        rt_subframes: Number of RT subframes per capture step.
    """
    import carb.settings
    import isaacsim.core.experimental.utils.stage as stage_utils
    import omni.replicator.core as rep
    from isaacsim.core.experimental.utils.semantics import add_labels
    from isaacsim.storage.native import get_assets_root_path

    # 1. Scene
    rep.orchestrator.set_capture_on_play(False)
    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)  # DLSS Quality
    assets_root = get_assets_root_path()
    stage_utils.open_stage(assets_root + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd")

    # 2. Semantic labels — add a referenced prop and tag it for annotators.
    stage_utils.add_reference_to_stage(
        usd_path=assets_root + "/Isaac/Props/YCB/Axis_Aligned/003_cracker_box.usd",
        path="/World/MyObj",
    )
    prim = stage_utils.get_current_stage().GetPrimAtPath("/World/MyObj")
    # Either API writes the UsdSemantics LabelsAPI schema on the prim:
    add_labels(prim, labels=["cracker_box"], taxonomy="class")
    # or, equivalently:
    # rep.functional.modify.semantics(prim, {"class": "cracker_box"}, mode="add")

    # 3. Camera + render product
    cam = rep.functional.create.camera(position=(3, 3, 2), look_at=(0, 0, 0), name="DataCam")
    rp = rep.create.render_product(cam, (1280, 720), name="main_view")

    # 4. Writer (explicit backend form)
    backend = rep.backends.get("DiskBackend")
    backend.initialize(output_dir=output_dir)
    writer = rep.writers.get("BasicWriter")
    writer.initialize(
        backend=backend,
        rgb=True,
        bounding_box_2d_tight=True,
        semantic_segmentation=True,
        distance_to_image_plane=True,
    )
    writer.attach(rp)

    # 5. Capture loop with randomization (static scene: delta_time=0.0 freezes timeline)
    for i in range(num_frames):
        # Randomize object pose, camera, lights here
        rep.orchestrator.step(delta_time=0.0, rt_subframes=rt_subframes)

    # 6. Cleanup
    rep.orchestrator.wait_until_complete()
    writer.detach()
    rp.destroy()
