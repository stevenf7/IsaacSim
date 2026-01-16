def register_lights_graph_randomizer(forklift_prim: Usd.Prim, pallet_prim: Usd.Prim, event_name: str) -> None:
    """Register graph randomizer to create sphere lights with varying color, intensity, and position."""
    bb_cache = create_bbox_cache()
    combined_bounds = compute_combined_aabb(bb_cache, [forklift_prim.GetPrimPath(), pallet_prim.GetPrimPath()])
    light_pos_min = (combined_bounds[0], combined_bounds[1], 6)
    light_pos_max = (combined_bounds[3], combined_bounds[4], 7)

    with rep.trigger.on_custom_event(event_name):
        rep.create.light(
            light_type="Sphere",
            color=rep.distribution.uniform((0.2, 0.1, 0.1), (0.9, 0.8, 0.8)),
            intensity=rep.distribution.uniform(2000, 4000),
            position=rep.distribution.uniform(light_pos_min, light_pos_max),
            scale=rep.distribution.uniform(1, 4),
            count=3,
        )


# Register lights randomizer
register_lights_graph_randomizer(forklift_prim, pallet_prim, event_name="randomize_lights")
